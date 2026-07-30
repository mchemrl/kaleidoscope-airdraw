import logging
import os
import time
import math
from datetime import datetime

import cv2

from vision.handtracker import HandTracker
from vision.gesture_detector import GestureDetector
from vision.kalman_smoother import KalmanSmoother2D
from vision.calibration import calibrate_pinch_threshold
from capture.capture_thread import ThreadedVideoCapture
from drawing.canvas import FadingCanvas
from drawing.symmetry import KaleidoscopeSymmetry
from drawing.styler import Styler
from ui.overlay import UIOverlay
from ui.palette import ColorPalette

logger = logging.getLogger(__name__)


class KaleidoscopeApp:
    window_name = 'kaleidoscope air draw'
    auto_rotate_speed = math.radians(20)

    def __init__(self, config):
        self.config = config
        self.capture = ThreadedVideoCapture(camera_index=config.camera_index).start()
        self.tracker = HandTracker(model_path='assets/hand_landmarker.task', max_num_hands=1)
        self.gesture = GestureDetector(
            pinch_threshold=config.pinch_threshold,
            open_palm_min_fingers=config.open_palm_min_fingers,
            fist_max_fingers=config.fist_max_fingers,
        )
        self.style = Styler()
        self.ui = UIOverlay()

        self.smoother = None
        self.draw_canvas = None
        self.symmetry = None
        self.color_palette = None
        self.auto_rotate = False

        os.makedirs('output', exist_ok=True)

    def calibrate(self):
        if not self.config.calibrate:
            return
        threshold = calibrate_pinch_threshold(
            self.capture, self.tracker, self.gesture,
            num_frames=self.config.calibration_frames,
            fallback_threshold=self.config.pinch_threshold,
            window_name=self.window_name,
        )
        self.gesture.pinch_threshold = threshold

    def setup_frame_dependent_state(self, frame_width, frame_height):
        self.smoother = KalmanSmoother2D(
            process_noise=self.config.kalman_process_noise,
            measurement_noise=self.config.kalman_measurement_noise,
        )
        self.draw_canvas = FadingCanvas(frame_width, frame_height)
        self.symmetry = KaleidoscopeSymmetry(
            (frame_width // 2, frame_height // 2),
            num_axes=self.config.default_num_axes,
        )
        self.color_palette = ColorPalette(
            self.style.palette, frame_width,
            dwell_time=self.config.palette_dwell_time,
        )

    def run(self):
        self.calibrate()
        logger.info('webcam started, press q to quit')

        was_pinching = False
        was_open_palm = False
        was_fist = False
        prev_smoothed_pos = None
        last_frame_time = time.time()

        while True:
            success, frame = self.capture.read()
            if not success:
                logger.warning('no frame available, skipping')
                continue

            frame = cv2.flip(frame, 1)
            frame_height, frame_width = frame.shape[:2]

            if self.draw_canvas is None:
                self.setup_frame_dependent_state(frame_width, frame_height)

            now = time.time()
            dt = now - last_frame_time
            last_frame_time = now

            if self.auto_rotate:
                self.symmetry.update_rotation(dt, self.auto_rotate_speed)
            self.draw_canvas.fade()

            self.tracker.process_frame(frame)
            frame = self.tracker.draw_landmarks(frame)

            fingertip_pos = self.tracker.get_index_fingertip_pos(frame_width, frame_height)
            mode = 'idle'

            if fingertip_pos is not None and self.tracker.results.hand_landmarks:
                hand_landmarks = self.tracker.results.hand_landmarks[0]

                is_pinching = self.gesture.is_pinching(hand_landmarks)
                is_open_palm = self.gesture.is_open_palm(hand_landmarks)
                is_fist = self.gesture.is_fist(hand_landmarks)

                smoothed_pos = self.smoother.update(fingertip_pos)

                selected_idx = None
                if not is_pinching:
                    selected_idx = self.color_palette.update_hover(fingertip_pos)
                else:
                    self.color_palette.update_hover(None)

                if selected_idx is not None:
                    self.style.select_color(selected_idx)

                if is_open_palm and not was_open_palm:
                    self.draw_canvas.clear()
                    mode = 'cleared'
                elif is_fist and not was_fist:
                    self.style.next_color()
                    mode = 'color switched'
                elif is_pinching:
                    if not was_pinching:
                        self.draw_canvas.start_stroke()
                        prev_smoothed_pos = smoothed_pos

                    speed = self.gesture.distance(prev_smoothed_pos, smoothed_pos)
                    thickness = self.style.thickness_from_speed(speed)
                    color_name, color_value = self.style.current_color()

                    self.draw_canvas.draw_to(smoothed_pos, self.symmetry, color=color_value, thickness=thickness)
                    cv2.circle(frame, smoothed_pos, 8, color_value, cv2.FILLED)
                    mode = 'drawing'
                elif selected_idx is not None:
                    mode = 'color picked'
                else:
                    self.draw_canvas.start_stroke()
                    cv2.circle(frame, smoothed_pos, 8, (0, 255, 255), 2)
                    mode = 'idle'

                prev_smoothed_pos = smoothed_pos
                was_pinching = is_pinching
                was_open_palm = is_open_palm
                was_fist = is_fist
            else:
                self.smoother.reset()
                self.draw_canvas.start_stroke()
                self.color_palette.update_hover(None)
                was_pinching = False
                was_open_palm = False
                was_fist = False

            frame = self.draw_canvas.overlay_on(frame)
            frame = self.color_palette.draw(frame)

            color_name, _ = self.style.current_color()
            frame = self.ui.draw(frame, mode, color_name, self.symmetry.num_axes)

            cv2.imshow(self.window_name, frame)

            key = cv2.waitKey(1) & 0xff
            if key == ord('q'):
                break
            elif key == ord('+') or key == ord('='):
                self.symmetry.set_num_axes(self.symmetry.num_axes + 1)
            elif key == ord('-') or key == ord('_'):
                self.symmetry.set_num_axes(self.symmetry.num_axes - 1)
            elif key == ord('r'):
                self.auto_rotate = not self.auto_rotate
                logger.info('auto rotate: %s', self.auto_rotate)
            elif key == ord('s'):
                filename = 'output/kaleidoscope_' + datetime.now().strftime('%y%m%d_%H%M%S') + '.png'
                cv2.imwrite(filename, self.draw_canvas.layer)
                logger.info('saved to %s', filename)

        self.shutdown()

    def shutdown(self):
        self.capture.stop()
        self.tracker.close()
        cv2.destroyAllWindows()