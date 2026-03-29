"""gm_volume.py — 3-finger pinch + vertical move → volume up/down."""

import pyautogui
import config


class VolumeGesture:
    def __init__(self):
        self._active       = False
        self._last_y       = 0
        self._repeat_timer = 0

    def update(self, state, active):
        overlay = []
        if not active:
            self._active = False
            return overlay

        if not self._active:
            self._active       = True
            self._last_y       = state.s8y
            self._repeat_timer = 0
        else:
            delta = self._last_y - state.s8y
            if abs(delta) > config.SCROLL_DEAD_ZONE:
                self._repeat_timer += 1
                if self._repeat_timer >= config.VOL_REPEAT_DELAY:
                    self._repeat_timer = 0
                    if delta > 0:
                        pyautogui.press('volumeup')
                        overlay.append(("VOL +", (0, 230, 100)))
                    else:
                        pyautogui.press('volumedown')
                        overlay.append(("VOL -", (0, 100, 230)))
            else:
                self._repeat_timer = 0

        overlay.append((f"3-finger pinch  d={state.pinch_3f:.3f}", (160, 255, 160)))
        return overlay

    def reset(self):
        self._active = False