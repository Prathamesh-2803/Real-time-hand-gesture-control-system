import math
import numpy as np
from collections import deque
import pyautogui
import config




def dist2d(x1, y1, x2, y2):
    return float(math.hypot(x2 - x1, y2 - y1))


def dist_lm(lm_a, lm_b):
    """Distance between two normalised MediaPipe landmarks (0-1 space)."""
    return float(math.hypot(lm_a.x - lm_b.x, lm_a.y - lm_b.y))


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




class OneEuroFilter:
    """
    One-Euro Filter for 2-D cursor positions.

    Parameters pulled from config so they can be tuned without code changes:
        CURSOR_OEF_MIN_CUTOFF  — smaller = smoother when still
        CURSOR_OEF_BETA        — larger = lower lag when moving fast
        CURSOR_OEF_D_CUTOFF    — derivative cutoff (usually 1 Hz is fine)
    """
    def __init__(self,
                 freq=None,
                 min_cutoff=None,
                 beta=None,
                 d_cutoff=None):
        self.freq       = freq       or float(config.CAMERA_FPS)
        self.min_cutoff = min_cutoff or getattr(config, 'CURSOR_OEF_MIN_CUTOFF', 0.5)
        self.beta       = beta       or getattr(config, 'CURSOR_OEF_BETA', 0.006)
        self.d_cutoff   = d_cutoff   or getattr(config, 'CURSOR_OEF_D_CUTOFF', 1.0)

        self._x_prev  = self._y_prev = None
        self._dx      = self._dy = 0.0

    def _alpha(self, cutoff):
        te  = 1.0 / self.freq
        tau = 1.0 / (2.0 * math.pi * cutoff)
        return 1.0 / (1.0 + tau / te)

    def update(self, x, y):
        if self._x_prev is None:
            self._x_prev, self._y_prev = float(x), float(y)
            return int(x), int(y)

    
        dx   = (x - self._x_prev) * self.freq
        dy   = (y - self._y_prev) * self.freq
        da   = self._alpha(self.d_cutoff)
        self._dx = da * dx + (1.0 - da) * self._dx
        self._dy = da * dy + (1.0 - da) * self._dy

        
        speed  = math.hypot(self._dx, self._dy)
        cutoff = self.min_cutoff + self.beta * speed
        a      = self._alpha(cutoff)

        fx = a * x + (1.0 - a) * self._x_prev
        fy = a * y + (1.0 - a) * self._y_prev
        self._x_prev, self._y_prev = fx, fy
        return int(fx), int(fy)

    def reset(self, x=None, y=None):
        if x is not None:
            self._x_prev, self._y_prev = float(x), float(y)
        else:
            self._x_prev = self._y_prev = None
        self._dx = self._dy = 0.0

    def seed_from_cursor(self):
        p = pyautogui.position()
        self.reset(float(p.x), float(p.y))

    def value(self):
        if self._x_prev is None:
            return 0, 0
        return int(self._x_prev), int(self._y_prev)




class AdaptiveEMABuffer:
    def __init__(self, alpha_slow=None, alpha_fast=None, fast_threshold_px=None):
        self.alpha_slow  = alpha_slow        or config.CURSOR_EMA_ALPHA
        self.alpha_fast  = alpha_fast        or config.CURSOR_EMA_ALPHA_FAST
        self.fast_thresh = fast_threshold_px or config.CURSOR_FAST_MOVE_PX
        self._x = self._y = None

    def update(self, x, y):
        if self._x is None:
            self._x, self._y = float(x), float(y)
            return int(self._x), int(self._y)
        raw_dist = math.hypot(x - self._x, y - self._y)
        alpha    = self.alpha_fast if raw_dist > self.fast_thresh else self.alpha_slow
        self._x  = alpha * x + (1.0 - alpha) * self._x
        self._y  = alpha * y + (1.0 - alpha) * self._y
        return int(self._x), int(self._y)

    def value(self):
        return (int(self._x), int(self._y)) if self._x is not None else (0, 0)

    def reset(self, x=None, y=None):
        if x is not None:
            self._x, self._y = float(x), float(y)
        else:
            self._x = self._y = None

    def seed_from_cursor(self):
        p = pyautogui.position()
        self.reset(p.x, p.y)


class EMABuffer(AdaptiveEMABuffer):
    """Backward-compat alias."""
    def __init__(self, alpha=None):
        super().__init__(alpha_slow=alpha or config.CURSOR_EMA_ALPHA)




class DistanceSmoother:
    def __init__(self, alpha=None):
        self.alpha  = alpha or config.DIST_SMOOTH_ALPHA
        self._value = None

    def update(self, raw):
        if self._value is None:
            self._value = float(raw)
        else:
            self._value = self.alpha * raw + (1.0 - self.alpha) * self._value
        return self._value

    def reset(self):
        self._value = None

    @property
    def value(self):
        return self._value if self._value is not None else 1.0




class HysteresisCounter:
    """
    Returns True only after `enter_frames` consecutive True inputs.
    Returns False only after `exit_frames` consecutive False inputs.
    """
    def __init__(self, enter_frames=3, exit_frames=3):
        self.enter_frames = enter_frames
        self.exit_frames  = exit_frames
        self._state       = False
        self._counter     = 0

    def update(self, signal: bool) -> bool:
        if signal:
            if not self._state:
                self._counter += 1
                if self._counter >= self.enter_frames:
                    self._state   = True
                    self._counter = 0
            else:
                self._counter = 0
        else:
            if self._state:
                self._counter += 1
                if self._counter >= self.exit_frames:
                    self._state   = False
                    self._counter = 0
            else:
                self._counter = 0
        return self._state

    def reset(self):
        self._state   = False
        self._counter = 0



class SmoothBuffer:
    def __init__(self, size, ix=0, iy=0):
        self.size = size
        self.xb   = deque([ix] * size, maxlen=size)
        self.yb   = deque([iy] * size, maxlen=size)

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