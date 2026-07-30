"""
reads webcam frames on a background thread with a small drop-oldest queue, decoupling capture fps from processing fps
"""
import queue
import threading
import logging

import cv2

logger = logging.getLogger(__name__)


class ThreadedVideoCapture:
    def __init__(self, camera_index=0, queue_size=2):
        self.camera_index = camera_index
        self.cap = cv2.VideoCapture(camera_index)
        if not self.cap.isOpened():
            raise RuntimeError(f"could not open webcam index {camera_index}")

        self.frame_queue = queue.Queue(maxsize=queue_size)
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)

    def start(self):
        self._thread.start()
        logger.info("capture thread started (camera index=%s)", self.camera_index)
        return self

    def _capture_loop(self):
        while not self._stop_event.is_set():
            success, frame = self.cap.read()
            if not success:
                logger.warning("frame grab failed, retrying")
                continue

            if self.frame_queue.full():
                try:
                    self.frame_queue.get_nowait()
                except queue.Empty:
                    pass
            try:
                self.frame_queue.put_nowait(frame)
            except queue.Full:
                pass

    def read(self, timeout=1.0):
        try:
            frame = self.frame_queue.get(timeout=timeout)
            return True, frame
        except queue.Empty:
            return False, None

    def stop(self):
        self._stop_event.set()
        self._thread.join(timeout=2.0)
        self.cap.release()
        logger.info("capture thread stopped")