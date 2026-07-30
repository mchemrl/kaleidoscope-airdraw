"""
turns hand landmarks into pinch/open palm/fist booleans using configurable finger-count and distance thresholds
"""
INDEX_FINGER_TIP = 8
THUMB_TIP = 4
WRIST = 0
MIDDLE_MCP = 9


class GestureDetector:
    def __init__(self, pinch_threshold=0.1, open_palm_min_fingers=4, fist_max_fingers=0):
        self.pinch_threshold = pinch_threshold
        self.open_palm_min_fingers = open_palm_min_fingers
        self.fist_max_fingers = fist_max_fingers

    def distance(self, p1, p2):
        return ((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2) ** 0.5

    def is_pinching(self, hand_landmarks):
        thumb = hand_landmarks[THUMB_TIP]
        index = hand_landmarks[INDEX_FINGER_TIP]
        wrist = hand_landmarks[WRIST]
        middle_mcp = hand_landmarks[MIDDLE_MCP]

        thumb_point = (thumb.x, thumb.y)
        index_point = (index.x, index.y)
        wrist_point = (wrist.x, wrist.y)
        middle_mcp_point = (middle_mcp.x, middle_mcp.y)

        pinch_dist = self.distance(thumb_point, index_point)
        hand_size = self.distance(wrist_point, middle_mcp_point)

        if hand_size == 0:
            return False

        normalized_dist = pinch_dist / hand_size
        return normalized_dist < self.pinch_threshold

    def count_extended_fingers(self, hand_landmarks):
        tips = [8, 12, 16, 20]
        pips = [6, 10, 14, 18]
        count = 0

        for tip_idx, pip_idx in zip(tips, pips):
            if hand_landmarks[tip_idx].y < hand_landmarks[pip_idx].y:
                count += 1

        thumb_tip = hand_landmarks[4]
        thumb_ip = hand_landmarks[3]
        wrist = hand_landmarks[0]
        if abs(thumb_tip.x - wrist.x) > abs(thumb_ip.x - wrist.x):
            count += 1

        return count

    def is_open_palm(self, hand_landmarks):
        return self.count_extended_fingers(hand_landmarks) >= self.open_palm_min_fingers

    def is_fist(self, hand_landmarks):
        return self.count_extended_fingers(hand_landmarks) == self.fist_max_fingers