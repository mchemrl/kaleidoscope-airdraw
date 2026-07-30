"""
on-screen color swatches with hover-to-select dwell logic and progress ring feedback
"""
import time

import cv2


class ColorPalette:
    def __init__(self, colors, frame_width, swatch_size=48, margin=10,top_offset=85, dwell_time=0.6):
        self.colors = colors
        self.swatch_size = swatch_size
        self.margin = margin
        self.top_offset = top_offset
        self.dwell_time = dwell_time

        self.selected_index = 0
        self.hover_index = None
        self.hover_start = None
        self.rects = list()

        self._layout(frame_width)

    def _layout(self, frame_width):
        self.rects = []
        n = len(self.colors)
        total_width = n * self.swatch_size + (n - 1) * self.margin
        start_x = frame_width - total_width - self.margin
        y1 = self.top_offset
        y2 = y1 + self.swatch_size
        for i in range(n):
            x1 = start_x + i * (self.swatch_size + self.margin)
            x2 = x1 + self.swatch_size
            self.rects.append((x1, y1, x2, y2))

    def hit_test(self, point):
        if point is None:
            return None
        px, py = point
        for i, (x1, y1, x2, y2) in enumerate(self.rects):
            if x1 <= px <= x2 and y1 <= py <= y2:
                return i
        return None

    def update_hover(self, point):

        idx = self.hit_test(point)

        if idx is None:
            self.hover_index = None
            self.hover_start = None
            return None

        if idx != self.hover_index:
            self.hover_index = idx
            self.hover_start = time.time()
            return None

        elapsed = time.time() - self.hover_start
        if elapsed >= self.dwell_time:
            self.selected_index = idx
            self.hover_index = None
            self.hover_start = None
            return idx

        return None

    def hover_progress(self):
        if self.hover_index is None or self.hover_start is None:
            return 0.0
        elapsed = time.time() - self.hover_start
        return min(1.0, elapsed / self.dwell_time)

    def draw(self, frame):
        for i, (x1, y1, x2, y2) in enumerate(self.rects):
            _name, color = self.colors[i]
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, cv2.FILLED)

            is_selected = (i == self.selected_index)
            border_color = (255, 255, 255) if is_selected else (90, 90, 90)
            thickness = 3 if is_selected else 1
            cv2.rectangle(frame, (x1, y1), (x2, y2), border_color, thickness)

            if i == self.hover_index:
                progress = self.hover_progress()
                center = ((x1 + x2) // 2, (y1 + y2) // 2)
                radius = self.swatch_size // 2 + 6
                angle = int(360 * progress)
                cv2.ellipse(frame, center, (radius, radius), -90, 0, angle,
                             (255, 255, 255), 3)
        return frame