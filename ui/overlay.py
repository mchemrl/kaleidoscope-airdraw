"""
draws the top hud bar showing mode, current color, axis count, and gesture hints
"""
import cv2

class UIOverlay:
    def __init__(self):
        self.font = cv2.FONT_HERSHEY_SIMPLEX

    def draw(self, frame, mode, color_name, num_axes):
        cv2.rectangle(frame, (0, 0), (frame.shape[1], 75), (0, 0, 0), cv2.FILLED)
        cv2.putText(frame, 'mode: ' + mode, (10, 22), self.font, 0.6, (255, 255, 255), 2)
        cv2.putText(frame, 'color: ' + color_name, (10, 47), self.font, 0.6, (255, 255, 255), 2)
        cv2.putText(frame, 'axes: ' + str(num_axes), (200, 22), self.font, 0.6, (255, 255, 255), 2)
        cv2.putText(frame, 'pinch=draw  fist=cycle color  palm=clear  hover=pick color  r=auto rotate  s=save  q=quit',
                    (200, 47), self.font, 0.42, (200, 200, 200), 1)
        return frame