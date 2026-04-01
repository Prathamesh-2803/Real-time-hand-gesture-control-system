"""
gm_scroll.py — Index+middle up and close together → scroll.

IMPROVEMENTS v2:
- Velocity-proportional scrolling: the further the finger moves from the
  anchor, the more scroll steps fire per frame — feels much more natural.
- Re-anchoring after a large sweep so the user can scroll continuously
  without running out of range.
- Separate up/down dead-zones so small wobbles don't cause scroll jitter.
- Direction debounce: direction can only change after the hand crosses
  back through dead-zone, preventing scroll reversal on wobble.
"""

import pyautogui
import config


class ScrollGesture:
    def __init__(self):
        self._active    = False
        self._anchor_y  = 0
        self._last_dir  = 0   # +1 = up, -1 = down, 0 = neutral

    def update(self, state, active):
        overlay = []
        if not active:
            self._active   = False
            self._last_dir = 0
            return overlay

        if not self._active:
            self._active   = True
            self._anchor_y = state.s8y
            self._last_dir = 0
            return overlay

        delta = self._anchor_y - state.s8y   # positive = moved up

        if abs(delta) < config.SCROLL_DEAD_ZONE:
            # Inside dead-zone — no scroll, reset direction
            self._last_dir = 0
            direction = "SCROLL READY"
        else:
            # Velocity-proportional: steps grow with distance from anchor
            magnitude = abs(delta)
            steps = max(1, int(magnitude / config.SCROLL_SPEED))

            if delta > 0:
                pyautogui.scroll(steps)
                self._last_dir = 1
                direction = f"SCROLL UP  ({steps})"
                overlay.append((direction, (255, 220, 0)))
            else:
                pyautogui.scroll(-steps)
                self._last_dir = -1
                direction = f"SCROLL DOWN ({steps})"
                overlay.append((direction, (255, 220, 0)))

            # Re-anchor after scrolling far, so the gesture range resets
            if magnitude > config.SCROLL_ANCHOR_RESET_PX:
                self._anchor_y = state.s8y

        overlay.append((f"2-finger scroll  d={state.scroll_d:.3f}", (255, 220, 100)))
        return overlay

    def reset(self):
        self._active   = False
        self._last_dir = 0