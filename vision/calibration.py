"""
asks the user to hold their hand open and relaxed in front of the
camera, and measures their resting thumb-index distance.
the pinch threshold is set to a fraction of that resting
distance, so it adapts to hand shape/size/camera distance per user
"""

import logging
import cv2

logger = logging.getLogger(__name__)

def calibrate_pinch_threshold(capture, tracker, gesture, num_frames=45,
                               fallback_threshold=0.4, window_name='calibration'):
    samples = list()
    font = cv2.FONT_HERSHEY_SIMPLEX

    logger.info("starting calibration: hold your hand open in front of the camera")

    while len(samples) < num_frames:
        success, frame = capture.read()
        if not success:
            continue

        frame = cv2.flip(frame, 1)
        tracker.process_frame(frame)

        if tracker.results and tracker.results.hand_landmarks:
            hand_landmarks = tracker.results.hand_landmarks[0]

            if gesture.count_extended_fingers(hand_landmarks) >= 4:
                thumb = hand_landmarks[4]
                index = hand_landmarks[8]
                wrist = hand_landmarks[0]
                middle_mcp = hand_landmarks[9]

                hand_size = gesture.distance((wrist.x, wrist.y), (middle_mcp.x, middle_mcp.y))
                if hand_size > 0:
                    pinch_dist = gesture.distance((thumb.x, thumb.y), (index.x, index.y))
                    samples.append(pinch_dist / hand_size)

        frame = tracker.draw_landmarks(frame)
        progress = f'{len(samples)}/{num_frames}'
        cv2.rectangle(frame, (0, 0), (frame.shape[1], 60), (0, 0, 0), cv2.FILLED)
        cv2.putText(frame, 'calibrating: hold hand open, relaxed  ' + progress,
                    (10, 25), font, 0.6, (255, 255, 255), 2)
        cv2.putText(frame, 'fingers spread, not pinching...',
                    (10, 50), font, 0.5, (200, 200, 200), 1)
        cv2.imshow(window_name, frame)

        if cv2.waitKey(1) & 0xff == ord('q'):
            logger.warning("calibration skipped by user, using fallback threshold")
            return fallback_threshold

    resting_distance = sum(samples) / len(samples)
    threshold = resting_distance * 0.45

    logger.info("calibration complete: resting_distance=%.3f pinch_threshold=%.3f",
                resting_distance, threshold)
    return threshold