"""gm_screenshot.py — Hold open palm spread wide → screenshot."""

import time
import pyautogui
import config


class ScreenshotGesture:
    def __init__(self):
        self._hold  = 0
        self._fired = False

    def update(self, state, active):
        overlay = []
        if not active:
            self._hold  = 0
            self._fired = False
            return overlay

        if state.spread_all > config.SPREAD_THRESH:
            self._hold += 1
            remaining = config.SPREAD_HOLD_FRAMES - self._hold
            if remaining > 0:
                overlay.append((f"Hold {remaining} frames for screenshot", (200, 100, 255)))
            if self._hold >= config.SPREAD_HOLD_FRAMES and not self._fired:
                fname = f"screenshot_{int(time.time())}.png"
                pyautogui.screenshot(fname)
                self._fired = True
                overlay.append((f"Saved {fname}", (180, 255, 120)))
        else:
            self._hold  = 0
            self._fired = False
        return overlay

    def reset(self):
        self._hold  = 0
        self._fired = False