"""
gm_screenshot.py — Hold open palm spread wide → screenshot.

IMPROVEMENTS v2:
- Countdown shows remaining seconds (using CAMERA_FPS) rather than
  arbitrary frame count, so the UI makes sense to users.
- Screenshot saved in a dedicated screenshots/ sub-folder (auto-created).
- Cooldown after firing so one long palm-hold doesn't spam screenshots.
- Visual flash effect: overlay turns bright green for 10 frames on fire.
"""

import time
import math
import pyautogui
import config
from pathlib import Path


_SS_DIR     = Path("screenshots")
_FLASH_FRAMES = 10   # frames to show "Saved!" message


class ScreenshotGesture:
    def __init__(self):
        self._hold     = 0
        self._fired    = False
        self._flash    = 0
        self._last_file = ""
        _SS_DIR.mkdir(exist_ok=True)

    def update(self, state, active):
        overlay = []

        # Flash countdown after screenshot
        if self._flash > 0:
            self._flash -= 1
            overlay.append((f"✓ Saved: {self._last_file}", (120, 255, 80)))

        if not active:
            self._hold  = 0
            self._fired = False
            return overlay

        if state.spread_all > config.SPREAD_THRESH:
            self._hold += 1

            # Show remaining time in seconds
            frames_left  = config.SPREAD_HOLD_FRAMES - self._hold
            secs_left    = math.ceil(frames_left / max(config.CAMERA_FPS, 1))
            overlay.append((
                f"Hold {secs_left}s for screenshot …",
                (200, 100, 255)
            ))

            if self._hold >= config.SPREAD_HOLD_FRAMES and not self._fired:
                ts    = int(time.time())
                fname = str(_SS_DIR / f"screenshot_{ts}.png")
                pyautogui.screenshot(fname)
                self._fired     = True
                self._last_file = fname
                self._flash     = _FLASH_FRAMES
                overlay.append((f"✓ Saved: {fname}", (120, 255, 80)))
        else:
            # Reset if spread drops (but keep _fired True until re-entry,
            # so releasing and re-spreading doesn't retrigger immediately)
            if not self._fired:
                self._hold = 0
            else:
                # Allow re-trigger after fully releasing
                if self._hold > 0 and state.spread_all < config.SPREAD_THRESH * 0.7:
                    self._hold  = 0
                    self._fired = False

        return overlay

    def reset(self):
        self._hold  = 0
        self._fired = False