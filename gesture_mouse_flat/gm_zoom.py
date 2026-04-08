"""
Zoom gesture — Thumb + Index finger only (all other fingers curled).

  Spread thumb & index apart  →  Zoom IN  (Ctrl +)
  Bring thumb & index closer  →  Zoom OUT (Ctrl -)

The distance between landmark 4 (thumb tip) and landmark 8 (index tip)
is used directly.  A rolling history buffer smooths jitter so the
direction is stable before a key-press fires.
"""

import pyautogui
from collections import deque
import config


class ZoomGesture:
    def __init__(self):
        self._active    = False
        self._cooldown  = 0
        self._dist_hist = deque(maxlen=getattr(config, 'ZOOM_HIST_LEN', 4))

    # ------------------------------------------------------------------
    def update(self, state, active):
        overlay = []

        if not active:
            self._reset_state()
            return overlay

        if self._cooldown > 0:
            self._cooldown -= 1

        dist = state.zoom_dist   # thumb-tip ↔ index-tip, normalised 0-1

        # Sanity-check: ignore clearly out-of-range values
        max_dist = getattr(config, 'ZOOM_SHAPE_MAX_DIST', 0.45)
        if dist > max_dist:
            self._reset_state()
            return overlay

        if not self._active:
            # First frame entering zoom mode — seed history, don't fire yet
            self._active = True
            self._dist_hist.clear()
            self._dist_hist.append(dist)
            overlay.append((f"Zoom ready  d={dist:.3f}", (100, 220, 255)))
            return overlay

        self._dist_hist.append(dist)

        # Need at least 2 samples to compute a direction
        if len(self._dist_hist) < 2:
            overlay.append((f"Zoom  d={dist:.3f}", (100, 220, 255)))
            return overlay

        # Compare smoothed oldest vs newest in the window
        oldest = self._dist_hist[0]
        newest = self._dist_hist[-1]
        delta  = newest - oldest   # positive → spreading → zoom in

        thresh = getattr(config, 'ZOOM_DELTA_THRESH', 0.018)

        if self._cooldown == 0:
            if delta > thresh:
                pyautogui.hotkey('ctrl', '+')
                overlay.append(("ZOOM IN  ▲", (0, 220, 255)))
                self._cooldown = config.ZOOM_COOLDOWN

            elif delta < -thresh:
                pyautogui.hotkey('ctrl', '-')
                overlay.append(("ZOOM OUT ▼", (255, 160, 0)))
                self._cooldown = config.ZOOM_COOLDOWN

        # Direction hint for the HUD
        if delta > 0.006:
            direction = "→ spreading (IN)"
        elif delta < -0.006:
            direction = "→ closing (OUT)"
        else:
            direction = "→ stable"

        overlay.append((f"Zoom d={dist:.3f}  {direction}", (100, 220, 255)))
        return overlay

    # ------------------------------------------------------------------
    def reset(self):
        self._reset_state()

    def _reset_state(self):
        self._active = False
        self._dist_hist.clear()