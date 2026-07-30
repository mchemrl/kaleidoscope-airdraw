""" constant-velocity kalman filter smoothing the fingertip's (x, y) position frame to frame. """
import numpy as np

class KalmanSmoother2D:
    def __init__(self, process_noise=1e-3, measurement_noise=1e-1):
        self.state = np.zeros(4, dtype=np.float64)
        self.initialized = False

        self.F = np.array([
            [1, 0, 1, 0],
            [0, 1, 0, 1],
            [0, 0, 1, 0],
            [0, 0, 0, 1],
        ], dtype=np.float64)

        self.H = np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0],
        ], dtype=np.float64)

        self.Q = np.eye(4, dtype=np.float64) * process_noise
        self.R = np.eye(2, dtype=np.float64) * measurement_noise
        self.P = np.eye(4, dtype=np.float64)

    def reset(self):
        self.initialized = False
        self.P = np.eye(4, dtype=np.float64)

    def update(self, measurement):
        z = np.array(measurement, dtype=np.float64)

        if not self.initialized:
            self.state[:2] = z
            self.state[2:] = 0
            self.initialized = True
            return int(self.state[0]), int(self.state[1])

        # predict
        self.state = self.F @ self.state
        self.P = self.F @ self.P @ self.F.T + self.Q

        # correct
        y = z - self.H @ self.state
        S = self.H @ self.P @ self.H.T + self.R
        K = self.P @ self.H.T @ np.linalg.inv(S)

        self.state = self.state + K @ y
        self.P = (np.eye(4) - K @ self.H) @ self.P

        return int(self.state[0]), int(self.state[1])