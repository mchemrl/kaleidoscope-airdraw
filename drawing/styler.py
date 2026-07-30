"""
holds the color palette list, current color selection/cycling, and stroke thickness based on draw speed.
"""
class Styler:
    def __init__(self):
        self.palette = [
            ('teal', (0, 224, 186)),
            ('dark purple', (145, 0, 141)),
            ('pink', (255, 52, 131)),
            ('yellow', (255, 207, 0)),
            ('purple', (129, 64, 220)),
        ]
        self.palette_index = 0

    def current_color(self):
        return self.palette[self.palette_index]

    def next_color(self):
        self.palette_index = (self.palette_index + 1) % len(self.palette)
        return self.current_color()

    def select_color(self, index):
        if 0 <= index < len(self.palette):
            self.palette_index = index
        return self.current_color()

    def thickness_from_speed(self, speed, min_thickness=2, max_thickness=16, max_speed=40):
        speed = min(speed, max_speed)
        ratio = speed / max_speed
        thickness = max_thickness - ratio * (max_thickness - min_thickness)
        return int(max(min_thickness, thickness))