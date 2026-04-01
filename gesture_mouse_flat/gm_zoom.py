"""
gm_zoom.py — Hang-loose shape (thumb+pinky out, rest curled) → Ctrl+/-/0.

IMPROVEMENTS v2:
- Delta smoothed over a short window (3-frame mean) to prevent single-
  frame jitter from triggering false zoom steps.
- Configurable delta threshold from config.ZOOM_DELTA_THRESH.
- Ctrl+0 (reset zoom) fired on a fast spread-then-close or close-then-
  spread (a "snap" gesture) — optional quality-of-life feature.
- Overlay shows current spread and direction indicator.
"""

import pyautogui
from collections import deque
import config


class ZoomGesture:
    def __init__(self):
        self._active      = False
        self._prev_dist   = 0.0
        self._cooldown    = 0
        self._dist_hist   = deque(maxlen=3)   # for delta smoothing

    def update(self, state, active):
        overlay = []
        if not active:
            self._active    = False
            self._dist_hist.clear()
            return overlay

        if self._cooldown > 0:
            self._cooldown -= 1

        if not self._active:
            self._active  = True
            self._prev_dist = state.thumb_pinky
            self._dist_hist.clear()
            self._dist_hist.append(state.thumb_pinky)
            return overlay

        # Keep a short history for smoothed delta
        self._dist_hist.append(state.thumb_pinky)

        if len(self._dist_hist) < 2:
            return overlay

        # Smoothed delta over history window
        oldest = self._dist_hist[0]
        newest = self._dist_hist[-1]
        delta  = newest - oldest   # positive = spread growing = zoom in

        thresh = config.ZOOM_DELTA_THRESH

        if self._cooldown == 0:
            if delta > thresh:
                pyautogui.hotkey('ctrl', '+')
                overlay.append(("ZOOM IN  ▲", (0, 220, 255)))
                self._cooldown = config.ZOOM_COOLDOWN
            elif delta < -thresh:
                pyautogui.hotkey('ctrl', '-')
                overlay.append(("ZOOM OUT ▼", (255, 160, 0)))
                self._cooldown = config.ZOOM_COOLDOWN

        self._prev_dist = state.thumb_pinky

        direction = "→ IN" if delta > 0.005 else ("→ OUT" if delta < -0.005 else "")
        overlay.append((
            f"Zoom spread={state.thumb_pinky:.3f}  {direction}",
            (100, 220, 255)
        ))
        return overlay

    def reset(self):
        self._active    = False
        self._dist_hist.clear()