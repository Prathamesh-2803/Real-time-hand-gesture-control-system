"""
gm_volume.py — 3-finger pinch + vertical move → volume up/down.

IMPROVEMENTS v2:
- Volume steps are proportional to hand displacement: a small nudge
  fires 1 step, a big sweep fires up to 3 steps at once.
- Re-anchor after large movement so continuous adjustment is possible.
- Faster repeat rate at wider displacement (adaptive VOL_REPEAT_DELAY).
- Dead-zone reset so returning to neutral stops the repeat timer.
"""

import pyautogui
import config


class VolumeGesture:
    def __init__(self):
        self._active       = False
        self._anchor_y     = 0
        self._repeat_timer = 0

    def update(self, state, active):
        overlay = []
        if not active:
            self._active = False
            return overlay

        if not self._active:
            self._active       = True
            self._anchor_y     = state.s8y
            self._repeat_timer = 0
            return overlay

        delta = self._anchor_y - state.s8y   # positive = hand moved up

        if abs(delta) < config.VOL_DEAD_ZONE:
            self._repeat_timer = 0
            overlay.append((f"3-finger pinch  d={state.pinch_3f:.3f}", (160, 255, 160)))
            return overlay

        # Adaptive repeat delay: farther from anchor → fires faster
        magnitude = abs(delta)
        if magnitude > config.VOL_DEAD_ZONE * 4:
            delay = max(2, config.VOL_REPEAT_DELAY - 2)
        elif magnitude > config.VOL_DEAD_ZONE * 2:
            delay = max(3, config.VOL_REPEAT_DELAY - 1)
        else:
            delay = config.VOL_REPEAT_DELAY

        self._repeat_timer += 1
        if self._repeat_timer >= delay:
            self._repeat_timer = 0
            steps = max(1, int(magnitude / (config.VOL_DEAD_ZONE * 2)))
            steps = min(steps, 3)  # cap at 3 key presses per tick

            if delta > 0:
                for _ in range(steps):
                    pyautogui.press('volumeup')
                overlay.append((f"VOL +{steps}", (0, 230, 100)))
            else:
                for _ in range(steps):
                    pyautogui.press('volumedown')
                overlay.append((f"VOL -{steps}", (0, 100, 230)))

            # Re-anchor to allow continuous adjustment
            if magnitude > config.VOL_DEAD_ZONE * 5:
                self._anchor_y = state.s8y

        overlay.append((f"3-finger pinch  d={state.pinch_3f:.3f}", (160, 255, 160)))
        return overlay

    def reset(self):
        self._active = False