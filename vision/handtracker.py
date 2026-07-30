"""
wraps mediapipe hand landmarker, processes frames, returns fingertip position and landmark drawing
"""

import cv2
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision

INDEX_FINGER_TIP = 8
THUMB_TIP = 4

# standard 21-point hand skeleton connections

HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),          # thumb
    (0, 5), (5, 6), (6, 7), (7, 8),          # index finger
    (5, 9), (9, 10), (10, 11), (11, 12),     # middle finger
    (9, 13), (13, 14), (14, 15), (15, 16),   # ring finger
    (13, 17), (17, 18), (18, 19), (19, 20),  # pinky
    (0, 17),                                  # palm base
]


class HandTracker:
    def __init__(self, model_path="hand_landmarker.task", max_num_hands=1,
                 detection_confidence=0.5, tracking_confidence=0.5):
        base_options = mp_python.BaseOptions(model_asset_path=model_path)
        options = mp_vision.HandLandmarkerOptions(
            base_options=base_options,
            num_hands=max_num_hands,
            min_hand_detection_confidence=detection_confidence,
            min_tracking_confidence=tracking_confidence,
            running_mode=mp_vision.RunningMode.VIDEO,
        )
        self.landmarker = mp_vision.HandLandmarker.create_from_options(options)

        self.results = None
        self._frame_timestamp_ms = 0

    def process_frame(self, frame_bgr):
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)

        self._frame_timestamp_ms += 33  # 30fps step
        self.results = self.landmarker.detect_for_video(mp_image, self._frame_timestamp_ms)
        return self.results

    def draw_landmarks(self, frame_bgr):
        if not self.results or not self.results.hand_landmarks:
            return frame_bgr

        frame_height, frame_width = frame_bgr.shape[:2]
        for hand_landmarks in self.results.hand_landmarks:
            points = list()
            for landmark in hand_landmarks:
                x_px = int(landmark.x * frame_width)
                y_px = int(landmark.y * frame_height)
                points.append((x_px, y_px))

            for start_idx, end_idx in HAND_CONNECTIONS:
                cv2.line(frame_bgr, points[start_idx], points[end_idx], (0, 0, 200), 1)
            for x_px, y_px in points:
                cv2.circle(frame_bgr, (x_px, y_px), 4, (0, 140, 255), cv2.FILLED)
        return frame_bgr

    def get_landmark_pixel_pos(self, landmark_index, frame_width, frame_height, hand_index=0):
        if not self.results or not self.results.hand_landmarks:
            return None
        if hand_index >= len(self.results.hand_landmarks):
            return None

        landmark = self.results.hand_landmarks[hand_index][landmark_index]
        x_px = int(landmark.x * frame_width)
        y_px = int(landmark.y * frame_height)
        return x_px, y_px

    def get_index_fingertip_pos(self, frame_width, frame_height, hand_index=0):
        return self.get_landmark_pixel_pos(INDEX_FINGER_TIP, frame_width, frame_height, hand_index)

    def close(self):
        self.landmarker.close()