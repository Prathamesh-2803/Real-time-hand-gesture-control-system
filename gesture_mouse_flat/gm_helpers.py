"""gm_helpers.py — Math helpers, coordinate mapping, adaptive smoothing."""

import numpy as np
from collections import deque
import pyautogui


def dist2d(x1, y1, x2, y2):
    return float(np.hypot(x2 - x1, y2 - y1))


def dist_lm(lm_a, lm_b):
    """Distance between two normalised MediaPipe landmarks (0-1 space)."""
    return float(np.hypot(lm_a.x - lm_b.x, lm_a.y - lm_b.y))


def map_to_screen(val, low, high, screen_dim):
    if high == low:
        return screen_dim // 2
    return int(np.clip((val - low) / (high - low) * screen_dim, 0, screen_dim - 1))


def landmark_to_screen(lm, frame_w, frame_h, zx0, zx1, zy0, zy1, sw, sh):
    rx = int(lm.x * frame_w)
    ry = int(lm.y * frame_h)
    sx = map_to_screen(rx, zx0, zx1, sw)
    sy = map_to_screen(ry, zy0, zy1, sh)
    return rx, ry, sx, sy


class EMABuffer:
    """
    Exponential Moving Average smoother.
    alpha=0.30 is a good default — smooth but responsive.
    """
    def __init__(self, alpha=0.30):
        self.alpha = alpha
        self._x = None
        self._y = None

    def update(self, x, y):
        if self._x is None:
            self._x, self._y = float(x), float(y)
        else:
            self._x = self.alpha * x + (1 - self.alpha) * self._x
            self._y = self.alpha * y + (1 - self.alpha) * self._y
        return int(self._x), int(self._y)

    def value(self):
        if self._x is None:
            return 0, 0
        return int(self._x), int(self._y)

    def reset(self, x=None, y=None):
        if x is not None:
            self._x, self._y = float(x), float(y)
        else:
            self._x = self._y = None

    def seed_from_cursor(self):
        p = pyautogui.position()
        self.reset(p.x, p.y)


# Keep SmoothBuffer for backward compat
class SmoothBuffer:
    def __init__(self, size, ix=0, iy=0):
        self.size = size
        self.xb = deque([ix] * size, maxlen=size)
        self.yb = deque([iy] * size, maxlen=size)

    def update(self, x, y):
        self.xb.append(x)
        self.yb.append(y)

    def value(self):
        return int(np.mean(self.xb)), int(np.mean(self.yb))

    def reset(self, x=0, y=0):
        self.xb = deque([x] * self.size, maxlen=self.size)
        self.yb = deque([y] * self.size, maxlen=self.size)

    def seed_from_cursor(self):
        p = pyautogui.position()
        self.reset(p.x, p.y)