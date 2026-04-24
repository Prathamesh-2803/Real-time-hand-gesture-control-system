import pyautogui
import config
from gm_helpers import OneEuroFilter, dist2d


# Consecutive frames above CLICK_RELEASE_NORM to confirm "open"
RELEASE_CONFIRM_FRAMES = 4

# Pinch must be held at least this many frames to be intentional
MIN_PINCH_FRAMES = 3

# Right-click needs a deeper pinch than left-click
_RIGHT_CLICK_THRESH = getattr(config, 'RIGHT_CLICK_THRESH', 0.050)

# Max cursor drift (px) during a click before it is suppressed
_MAX_CLICK_DRIFT = 28


class CursorGesture:

    _ST_IDLE    = 0
    _ST_PINCHED = 1
    _ST_DRAG    = 2

    def __init__(self):
        self._oef    = OneEuroFilter()
        self._prev_x = self._prev_y = 0.0
        self._seeded = False

        self._state          = self._ST_IDLE
        self._pinch_frames   = 0
        self._release_frames = 0
        self._click_cd       = 0
        self._last_lclick_f  = -9999
        self._frame          = 0

        self._drag_start_x   = 0.0
        self._drag_start_y   = 0.0
        self._pinch_min_dist = 1.0   # deepest pinch seen in current gesture

    
    def update(self, state, active):
        self._frame += 1
        overlay = []

        if not active:
            self._hard_reset()
            return overlay

        # Seed OEF from actual cursor position so there is no jump on entry
        if not self._seeded:
            self._oef.seed_from_cursor()
            p = pyautogui.position()
            self._prev_x, self._prev_y = float(p.x), float(p.y)
            self._seeded = True

        #  Cursor movement 
        cx, cy = self._oef.update(state.s8x, state.s8y)
        moved  = dist2d(cx, cy, self._prev_x, self._prev_y)

        if self._state == self._ST_DRAG:
            pyautogui.dragTo(int(cx), int(cy), button='left', _pause=False)
            self._prev_x, self._prev_y = cx, cy
        elif moved > config.DEAD_ZONE:
            pyautogui.moveTo(int(cx), int(cy), _pause=False)
            self._prev_x, self._prev_y = cx, cy

        if self._click_cd > 0:
            self._click_cd -= 1

        dist = state.pinch_2f

        #  Release detection (debounced) 
        if dist > config.CLICK_RELEASE_NORM:
            self._release_frames += 1
        else:
            self._release_frames = 0

        pinch_released = (self._release_frames >= RELEASE_CONFIRM_FRAMES)

        #  State machine 

        if self._state == self._ST_IDLE:
            if dist < config.CLICK_THRESH_NORM:
                self._state          = self._ST_PINCHED
                self._pinch_frames   = 1
                self._release_frames = 0
                self._pinch_min_dist = dist
                self._drag_start_x, self._drag_start_y = cx, cy

        elif self._state == self._ST_PINCHED:
            if not pinch_released:
                self._pinch_frames   += 1
                self._pinch_min_dist  = min(self._pinch_min_dist, dist)

                if self._pinch_frames >= config.DRAG_HOLD_FRAMES:
                    moved_since = dist2d(cx, cy,
                                         self._drag_start_x, self._drag_start_y)
                    if moved_since >= config.DRAG_MIN_MOVE_PX:
                        self._state = self._ST_DRAG
                        pyautogui.mouseDown(button='left', _pause=False)
                        overlay.append(("DRAG START", (0, 180, 255)))
                    else:
                        pct = min(100, int(self._pinch_frames /
                                           config.DRAG_HOLD_FRAMES * 100))
                        overlay.append((f"Hold for drag {pct}%", (200, 200, 100)))
                else:
                    pct = min(100, int(self._pinch_frames /
                                       config.PINCH_FRAMES * 100))
                    overlay.append((f"Pinching {pct}%", (255, 220, 100)))

            else:
                # Finger opened — decide which action to fire
                held     = self._pinch_frames
                min_dist = self._pinch_min_dist

                self._state          = self._ST_IDLE
                self._pinch_frames   = 0
                self._release_frames = 0
                self._pinch_min_dist = 1.0

                # Too brief — likely filter noise, ignore completely
                if held < MIN_PINCH_FRAMES:
                    pass

                elif held < config.PINCH_FRAMES:
                    # Short pinch → RIGHT click
                    # Must have gone below the tighter right-click threshold
                    moved_since = dist2d(cx, cy,
                                         self._drag_start_x, self._drag_start_y)
                    if (min_dist < _RIGHT_CLICK_THRESH
                            and moved_since < _MAX_CLICK_DRIFT
                            and self._click_cd == 0):
                        pyautogui.rightClick(_pause=False)
                        overlay.append(("RIGHT CLICK", (0, 165, 255)))
                        self._click_cd = config.CLICK_COOLDOWN

                else:
                    # Long pinch → LEFT click (or double click)
                    moved_since = dist2d(cx, cy,
                                         self._drag_start_x, self._drag_start_y)
                    if moved_since < _MAX_CLICK_DRIFT and self._click_cd == 0:
                        gap = self._frame - self._last_lclick_f
                        if 0 < gap <= config.DOUBLE_CLICK_WINDOW:
                            pyautogui.doubleClick(_pause=False)
                            overlay.append(("DOUBLE CLICK", (0, 255, 200)))
                            self._last_lclick_f = -9999
                        else:
                            pyautogui.click(_pause=False)
                            overlay.append(("LEFT CLICK", (0, 255, 130)))
                            self._last_lclick_f = self._frame
                        self._click_cd = config.CLICK_COOLDOWN

        elif self._state == self._ST_DRAG:
            if pinch_released:
                pyautogui.mouseUp(button='left', _pause=False)
                self._state          = self._ST_IDLE
                self._pinch_frames   = 0
                self._release_frames = 0
                overlay.append(("DRAG END", (0, 180, 255)))
            else:
                self._pinch_frames += 1
                overlay.append(("DRAGGING", (0, 180, 255)))

        #  Pinch distance bar 
        fill = int(max(0.0, 1.0 - dist / config.CLICK_RELEASE_NORM) * 12)
        bar  = "X" * fill + "." * (12 - fill)
        overlay.append((f"d={dist:.3f} [{bar}]", (140, 140, 140)))
        return overlay

    
    def reset(self):
        self._hard_reset()
        self._seeded = False
        self._oef.reset()

    def _hard_reset(self):
        if self._state == self._ST_DRAG:
            try:
                pyautogui.mouseUp(button='left', _pause=False)
            except Exception:
                pass
        self._state          = self._ST_IDLE
        self._pinch_frames   = 0
        self._release_frames = 0
        self._pinch_min_dist = 1.0