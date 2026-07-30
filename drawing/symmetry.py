"""
kaleidoscope mirror-tile symmetry math, including the rotation offset used for auto-rotate.
"""
import math

class KaleidoscopeSymmetry:
    def __init__(self, center, num_axes=6):
        self.center = center
        self.num_axes = max(1, num_axes)
        self.rotation_offset = 0.0

    def set_center(self, center):
        self.center = center

    def set_num_axes(self, num_axes):
        self.num_axes = max(1, num_axes)

    def update_rotation(self, dt, angular_speed):
        self.rotation_offset += angular_speed * dt

    def mirror_point(self, point):
        cx, cy = self.center
        px, py = point
        dx = px - cx
        dy = py - cy
        radius = (dx ** 2 + dy ** 2) ** 0.5
        angle = math.atan2(dy, dx)

        wedge_angle = 2 * math.pi / self.num_axes
        points = list()
        for i in range(self.num_axes):
            step = wedge_angle * i + self.rotation_offset
            for a in (angle + step, -angle + step):
                x = cx + radius * math.cos(a)
                y = cy + radius * math.sin(a)
                points.append((int(x), int(y)))
        return points