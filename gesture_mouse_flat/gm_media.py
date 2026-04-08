import pyautogui
import config


HOLD_REQUIRED = 3
MEDIA_LOCKOUT = 30   


def _is_peace(lm):
    """Index + middle up, ring + pinky curled."""
    return (lm[8].y  < lm[5].y  and lm[12].y < lm[9].y  and
            lm[16].y > lm[13].y and lm[20].y > lm[17].y)


def _is_thumbs_up(lm):
    """Thumb pointing up, all fingers curled."""
    thumb_up = lm[4].y < lm[2].y - 0.05
    curled   = all(lm[t].y > lm[p].y
                   for t, p in [(8, 5), (12, 9), (16, 13), (20, 17)])
    return thumb_up and curled


class MediaGesture:
    def __init__(self):
        self._fist_frames  = 0
        self._fist_fired   = False

        self._peace_frames = 0
        self._peace_fired  = False

        self._thumb_frames = 0
        self._thumb_fired  = False

        self._lockout      = 0  

    def update(self, state, raw_lm, active):
        overlay = []

        if self._lockout > 0:
            self._lockout -= 1

        if not active or raw_lm is None:
            self._reset()
            return overlay


        if state.fingers_curled:
            self._fist_frames += 1
            if (self._fist_frames >= config.FIST_HOLD_FRAMES
                    and not self._fist_fired and self._lockout == 0):
                pyautogui.press('playpause')
                self._fist_fired  = True
                self._lockout     = MEDIA_LOCKOUT
                overlay.append(("FIST — PLAY/PAUSE", (255, 180, 0)))
        else:
            self._fist_frames = 0
            self._fist_fired  = False

       
        if _is_peace(raw_lm):
            self._peace_frames += 1
            if (self._peace_frames >= HOLD_REQUIRED
                    and not self._peace_fired and self._lockout == 0):
                pyautogui.press('nexttrack')
                self._peace_fired = True
                self._lockout     = MEDIA_LOCKOUT
                overlay.append(("PEACE — NEXT TRACK", (80, 255, 200)))
        else:
            self._peace_frames = 0
            self._peace_fired  = False

       
        if _is_thumbs_up(raw_lm):
            self._thumb_frames += 1
            if (self._thumb_frames >= HOLD_REQUIRED
                    and not self._thumb_fired and self._lockout == 0):
                pyautogui.press('prevtrack')
                self._thumb_fired = True
                self._lockout     = MEDIA_LOCKOUT
                overlay.append(("THUMBS — PREV TRACK", (80, 200, 255)))
        else:
            self._thumb_frames = 0
            self._thumb_fired  = False

        return overlay

    def reset(self):
        self._reset()

    def _reset(self):
        self._fist_frames  = 0
        self._fist_fired   = False
        self._peace_frames = 0
        self._peace_fired  = False
        self._thumb_frames = 0
        self._thumb_fired  = False