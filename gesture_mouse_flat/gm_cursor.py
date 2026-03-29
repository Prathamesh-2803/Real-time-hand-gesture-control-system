"""
gm_cursor.py — Cursor movement, left/right click, double-click, drag.

Uses EMA smoothing for buttery movement.
Cursor maps only when index finger is isolated (cursor_mode=True).
Pinch is detected in normalised space for reliability.
"""

import pyautogui
import config
from gm_helpers import EMABuffer, dist2d


class CursorGesture:
    def __init__(self):
        self._ema  = EMABuffer(alpha=config.CURSOR_EMA_ALPHA)
        self._prev_x = self._prev_y = 0
        self._first  = True

        self._pinch_frames    = 0
        self._click_cooldown  = 0
        self._right_done      = False
        self._drag_active     = False
        self._last_click_frame = -999
        self._frame = 0

    def update(self, state, active):
        self._frame += 1
        overlay = []

        if not active:
            self._pinch_frames = 0
            self._right_done   = False
            return overlay

        # Seed EMA from current cursor position on first appearance
        if self._first:
            self._ema.seed_from_cursor()
            p = pyautogui.position()
            self._prev_x, self._prev_y = p.x, p.y
            self._first = False

        # ── Smooth cursor movement ────────────────────────────────────────────
        cx, cy = self._ema.update(state.s8x, state.s8y)
        moved  = dist2d(cx, cy, self._prev_x, self._prev_y)

        if self._drag_active:
            pyautogui.dragTo(cx, cy, button='left', _pause=False)
            self._prev_x, self._prev_y = cx, cy
        elif moved > config.DEAD_ZONE:
            pyautogui.moveTo(cx, cy, _pause=False)
            self._prev_x, self._prev_y = cx, cy

        # ── Click / drag in normalised pinch distance ─────────────────────────
        if self._click_cooldown > 0:
            self._click_cooldown -= 1

        if state.pinch_2f < config.CLICK_THRESH_NORM:
            self._pinch_frames += 1
            if self._pinch_frames == config.DRAG_HOLD_FRAMES and not self._drag_active:
                self._drag_active = True
                pyautogui.mouseDown(button='left')
                overlay.append(("DRAG START", (0, 180, 255)))
        else:
            if self._pinch_frames > 0:
                if self._drag_active:
                    pyautogui.mouseUp(button='left')
                    self._drag_active = False
                    overlay.append(("DRAG END", (0, 180, 255)))
                elif self._pinch_frames < config.PINCH_FRAMES:
                    if not self._right_done:
                        pyautogui.rightClick()
                        self._right_done = True
                        overlay.append(("RIGHT CLICK", (0, 165, 255)))
                else:
                    if self._click_cooldown == 0:
                        gap = self._frame - self._last_click_frame
                        if gap <= config.DOUBLE_CLICK_WINDOW:
                            pyautogui.doubleClick()
                            overlay.append(("DOUBLE CLICK", (0, 255, 200)))
                            self._last_click_frame = -999
                        else:
                            pyautogui.click()
                            overlay.append(("LEFT CLICK", (0, 255, 130)))
                            self._last_click_frame = self._frame
                        self._click_cooldown = config.CLICK_COOLDOWN
            self._pinch_frames = 0
            self._right_done   = False

        overlay.append((
            f"Pinch {state.pinch_2f:.3f}  move {int(moved)}px"
            + ("  DRAGGING" if self._drag_active else ""),
            (200, 200, 200)
        ))
        return overlay

    def reset(self):
        if self._drag_active:
            pyautogui.mouseUp(button='left')
            self._drag_active = False
        self._pinch_frames = 0
        self._right_done   = False
        self._first        = True
        self._ema.reset()