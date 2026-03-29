"""gm_scroll.py — Index+middle up and close together → scroll."""

import pyautogui
import config


class ScrollGesture:
    def __init__(self):
        self._active   = False
        self._anchor_y = 0

    def update(self, state, active):
        overlay = []
        if not active:
            self._active = False
            return overlay

        if not self._active:
            self._active   = True
            self._anchor_y = state.s8y
        else:
            delta = self._anchor_y - state.s8y
            if abs(delta) > config.SCROLL_DEAD_ZONE:
                steps = int(delta / config.SCROLL_SPEED)
                if steps:
                    pyautogui.scroll(steps)
                    self._anchor_y = state.s8y
            direction = "SCROLL UP" if (self._anchor_y - state.s8y) >= 0 else "SCROLL DOWN"
            overlay.append((direction, (255, 220, 0)))

        overlay.append((f"2-finger scroll  d={state.scroll_d:.3f}", (255, 220, 100)))
        return overlay

    def reset(self):
        self._active = False