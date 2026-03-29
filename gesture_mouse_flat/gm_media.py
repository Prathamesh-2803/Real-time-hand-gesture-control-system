"""gm_media.py — Media controls: fist=play/pause, peace=next, thumbs=prev."""

import pyautogui
import config


def _is_peace(lm):
    return (lm[8].y  < lm[5].y and lm[12].y < lm[9].y and
            lm[16].y > lm[13].y and lm[20].y > lm[17].y)


def _is_thumbs_up(lm):
    thumb_up = lm[4].y < lm[2].y - 0.05
    curled   = all(lm[t].y > lm[p].y for t,p in [(8,6),(12,10),(16,14),(20,18)])
    return thumb_up and curled


class MediaGesture:
    def __init__(self):
        self._fist_frames = 0
        self._fist_fired  = False
        self._peace_fired = False
        self._thumb_fired = False

    def update(self, state, raw_lm, active):
        overlay = []
        if not active or raw_lm is None:
            self._reset()
            return overlay

        if state.fingers_curled:
            self._fist_frames += 1
            if self._fist_frames >= config.FIST_HOLD_FRAMES and not self._fist_fired:
                pyautogui.press('playpause')
                self._fist_fired = True
                overlay.append(("FIST - PLAY/PAUSE", (255,180,0)))
        else:
            self._fist_frames = 0
            self._fist_fired  = False

        if _is_peace(raw_lm):
            if not self._peace_fired:
                pyautogui.press('nexttrack')
                self._peace_fired = True
                overlay.append(("PEACE - NEXT TRACK", (80,255,200)))
        else:
            self._peace_fired = False

        if _is_thumbs_up(raw_lm):
            if not self._thumb_fired:
                pyautogui.press('prevtrack')
                self._thumb_fired = True
                overlay.append(("THUMBS - PREV TRACK", (80,200,255)))
        else:
            self._thumb_fired = False

        return overlay

    def reset(self):
        self._reset()

    def _reset(self):
        self._fist_frames = 0
        self._fist_fired  = False
        self._peace_fired = False
        self._thumb_fired = False