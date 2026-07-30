"""
the fading kaleidoscope canvas: draws mirrored/tiled strokes with color gradient and per-frame decay for trailing effects
"""
import numpy as np
import cv2

class FadingCanvas:
    def __init__(self, width, height, decay=0.965, hue_speed=40.0):
        self.width = width
        self.height = height
        self.decay = decay
        self.hue_speed = hue_speed
        self.layer = np.zeros((height, width, 3), dtype=np.float32)
        self.last_point = None
        self.total_distance = 0.0

    def start_stroke(self):
        self.last_point = None
        self.total_distance = 0.0

    def _shift_hue(self, bgr_color, degrees):
        color_arr = np.uint8([[bgr_color]])
        hsv = cv2.cvtColor(color_arr, cv2.COLOR_BGR2HSV).astype(np.int16)
        hsv[0, 0, 0] = int(hsv[0, 0, 0] + degrees) % 180
        shifted = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
        return tuple(int(c) for c in shifted[0, 0])

    def draw_to(self, point, symmetry, color=(0, 200, 255), thickness=4):
        if self.last_point is not None:
            dx = point[0] - self.last_point[0]
            dy = point[1] - self.last_point[1]
            segment_length = (dx ** 2 + dy ** 2) ** 0.5
            self.total_distance += segment_length

            hue_degrees = (self.total_distance * self.hue_speed / 100.0) % 180
            gradient_color = self._shift_hue(color, hue_degrees)

            mirrored_last = symmetry.mirror_point(self.last_point)
            mirrored_current = symmetry.mirror_point(point)
            for p1, p2 in zip(mirrored_last, mirrored_current):
                cv2.line(self.layer, p1, p2, gradient_color, thickness, cv2.LINE_AA)
        self.last_point = point

    def fade(self):
        self.layer *= self.decay

    def clear(self):
        self.layer[:] = 0

    def overlay_on(self, frame):
        layer_uint8 = np.clip(self.layer, 0, 255).astype(np.uint8)
        mask = np.any(layer_uint8 != 0, axis=2)
        frame[mask] = layer_uint8[mask]
        return frame