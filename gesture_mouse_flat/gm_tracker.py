"""
gm_tracker.py — MediaPipe hand tracker.

CHANGES v3:
- Full-screen support: when MARGIN_RATIO = 0, zone covers whole frame
- landmark_to_screen works correctly with full-frame coords
- Distance smoothers unchanged — already solid
- Finger extension logic unchanged — already robust
- Added scroll_exit_hyst to prevent flicker on scroll exit
"""

import cv2
import mediapipe as mp
import numpy as np
from dataclasses import dataclass, field

from gm_helpers import (landmark_to_screen, dist_lm, dist2d,
                        DistanceSmoother, HysteresisCounter)
import config


@dataclass
class HandState:
    present:     bool  = False
    hand_active: bool  = False
    hand_size:   float = 0.15

    # Raw frame pixel coords (for drawing)
    r4x:  int = 0;  r4y:  int = 0
    r8x:  int = 0;  r8y:  int = 0
    r12x: int = 0;  r12y: int = 0
    r16x: int = 0;  r16y: int = 0
    r20x: int = 0;  r20y: int = 0

    # Screen coords (mapped to monitor)
    s4x:  int = 0;  s4y:  int = 0
    s8x:  int = 0;  s8y:  int = 0
    s12x: int = 0;  s12y: int = 0
    s16x: int = 0;  s16y: int = 0
    s20x: int = 0;  s20y: int = 0

    # Smoothed normalised distances
    pinch_2f:     float = 1.0
    scroll_d:     float = 1.0
    pinch_3f:     float = 1.0
    thumb_pinky:  float = 1.0
    spread_all:   float = 0.0

    # Per-finger extended flags
    thumb_up:   bool = False
    index_up:   bool = False
    middle_up:  bool = False
    ring_up:    bool = False
    pinky_up:   bool = False

    # Composite gestures
    cursor_mode:    bool = False
    scroll_mode:    bool = False
    volume_mode:    bool = False
    zoom_shape:     bool = False
    fingers_curled: bool = False
    palm_open:      bool = False


class HandTracker:
    def __init__(self, screen_w, screen_h):
        self.sw = screen_w
        self.sh = screen_h
        self._mp    = mp.solutions.hands
        self._draw  = mp.solutions.drawing_utils
        self._hands = self._mp.Hands(
            max_num_hands=config.MAX_HANDS,
            model_complexity=config.MODEL_COMPLEXITY,
            min_detection_confidence=config.MIN_DETECTION_CONFIDENCE,
            min_tracking_confidence=config.MIN_TRACKING_CONFIDENCE,
        )
        self.last_landmarks = None

        # Distance EMA smoothers
        self._sm_pinch2 = DistanceSmoother()
        self._sm_scroll = DistanceSmoother()
        self._sm_pinch3 = DistanceSmoother()
        self._sm_tpinky = DistanceSmoother()
        self._sm_spread = DistanceSmoother()

        # Hysteresis counters
        self._active_hyst = HysteresisCounter(
            enter_frames=config.HAND_ACTIVE_HYSTERESIS,
            exit_frames=config.HAND_INACTIVE_HYSTERESIS,
        )
        self._scroll_hyst = HysteresisCounter(enter_frames=3, exit_frames=5)

    @staticmethod
    def _finger_up(tip, pip, mcp):
        """Extended = tip above BOTH PIP and MCP joints."""
        return tip.y < pip.y and tip.y < mcp.y

    @staticmethod
    def _fake_lm(x, y):
        class _FL:
            pass
        fl = _FL(); fl.x = x; fl.y = y
        return fl

    def process(self, frame_bgr, zx0, zx1, zy0, zy1):
        s = HandState()
        h, w = frame_bgr.shape[:2]
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        out = self._hands.process(rgb)
        self.last_landmarks = None

        if not out.multi_hand_landmarks:
            self._active_hyst.update(False)
            self._scroll_hyst.update(False)
            for sm in (self._sm_pinch2, self._sm_scroll, self._sm_pinch3,
                       self._sm_tpinky, self._sm_spread):
                sm.reset()
            return s

        s.present = True
        hand = out.multi_hand_landmarks[0]
        self._draw.draw_landmarks(frame_bgr, hand)
        lm = hand.landmark
        self.last_landmarks = lm

        # ── Screen + raw coords ───────────────────────────────────────────────
        def _c(idx):
            return landmark_to_screen(lm[idx], w, h, zx0, zx1, zy0, zy1,
                                      self.sw, self.sh)

        s.r4x,  s.r4y,  s.s4x,  s.s4y  = _c(4)
        s.r8x,  s.r8y,  s.s8x,  s.s8y  = _c(8)
        s.r12x, s.r12y, s.s12x, s.s12y = _c(12)
        s.r16x, s.r16y, s.s16x, s.s16y = _c(16)
        s.r20x, s.r20y, s.s20x, s.s20y = _c(20)

        # ── Hand size (wrist → middle MCP, scale reference) ───────────────────
        s.hand_size = max(dist_lm(lm[0], lm[9]), 0.05)

        # ── Hand activation gate ──────────────────────────────────────────────
        raw_active    = (lm[0].y - lm[8].y) > config.HAND_ACTIVE_MARGIN
        s.hand_active = self._active_hyst.update(raw_active)

        # ── Raw normalised distances ──────────────────────────────────────────
        raw_pinch2 = dist_lm(lm[4], lm[8])
        raw_scroll = dist_lm(lm[8], lm[12])
        raw_tpinky = dist_lm(lm[4], lm[20])

        mid        = self._fake_lm((lm[8].x + lm[12].x) / 2,
                                    (lm[8].y + lm[12].y) / 2)
        raw_pinch3 = dist_lm(lm[4], mid)

        tips  = [lm[4], lm[8], lm[12], lm[16], lm[20]]
        dists = [dist_lm(tips[i], tips[j])
                 for i in range(5) for j in range(i + 1, 5)]
        raw_spread = float(np.mean(dists))

        # ── EMA smoothing ─────────────────────────────────────────────────────
        s.pinch_2f    = self._sm_pinch2.update(raw_pinch2)
        s.scroll_d    = self._sm_scroll.update(raw_scroll)
        s.pinch_3f    = self._sm_pinch3.update(raw_pinch3)
        s.thumb_pinky = self._sm_tpinky.update(raw_tpinky)
        s.spread_all  = self._sm_spread.update(raw_spread)

        # ── Finger extension ──────────────────────────────────────────────────
        s.thumb_up  = lm[4].y < lm[3].y
        s.index_up  = self._finger_up(lm[8],  lm[7],  lm[5])
        s.middle_up = self._finger_up(lm[12], lm[11], lm[9])
        s.ring_up   = self._finger_up(lm[16], lm[15], lm[13])
        s.pinky_up  = self._finger_up(lm[20], lm[19], lm[17])

        up_count = sum([s.index_up, s.middle_up, s.ring_up, s.pinky_up])
        s.palm_open      = (up_count == 4 and s.thumb_up)
        s.fingers_curled = (up_count == 0)

        # ── Gesture shapes ────────────────────────────────────────────────────

        # CURSOR: only index finger up
        s.cursor_mode = (
            s.index_up and
            not s.middle_up and
            not s.ring_up and
            not s.pinky_up
        )

        # SCROLL: index + middle up, tips close, ring + pinky down
        scroll_raw = (
            s.index_up and s.middle_up and
            not s.ring_up and not s.pinky_up and
            s.scroll_d < config.SCROLL_THRESH_NORM
        )
        s.scroll_mode = self._scroll_hyst.update(scroll_raw)

        # VOLUME: 3-finger pinch
        s.volume_mode = s.pinch_3f < config.VOL_PINCH_THRESH_NORM

        # ZOOM: hang-loose (thumb + pinky extended, rest curled, wide spread)
        s.zoom_shape = (
            s.thumb_up and s.pinky_up and
            not s.index_up and not s.middle_up and not s.ring_up and
            s.thumb_pinky > config.ZOOM_THRESH_NORM
        )

        return s

    def release(self):
        self._hands.close()