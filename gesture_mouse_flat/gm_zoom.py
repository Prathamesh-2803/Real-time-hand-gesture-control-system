"""gm_zoom.py — Hang-loose shape (thumb+pinky out, rest curled) → Ctrl+/-."""

import pyautogui
import config


class ZoomGesture:
    def __init__(self):
        self._active    = False
        self._prev_dist = 0.0
        self._cooldown  = 0

    def update(self, state, active):
        overlay = []
        if not active:
            self._active = False
            return overlay

        if self._cooldown > 0:
            self._cooldown -= 1

        if not self._active:
            self._active    = True
            self._prev_dist = state.thumb_pinky
        else:
            delta = state.thumb_pinky - self._prev_dist
            if self._cooldown == 0:
                if delta > 0.02:
                    pyautogui.hotkey('ctrl', '+')
                    overlay.append(("ZOOM IN", (0, 220, 255)))
                    self._cooldown = 10
                elif delta < -0.02:
                    pyautogui.hotkey('ctrl', '-')
                    overlay.append(("ZOOM OUT", (255, 160, 0)))
                    self._cooldown = 10
            self._prev_dist = state.thumb_pinky

        overlay.append((f"Zoom  spread={state.thumb_pinky:.3f}", (100, 220, 255)))
        return overlay

    def reset(self):
        self._active = False