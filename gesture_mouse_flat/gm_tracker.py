"""
gm_tracker.py — MediaPipe hand tracker.

Key design decisions:
- All pinch/distance thresholds use NORMALISED landmark space (0.0–1.0)
  not screen pixels, so they work regardless of screen resolution or
  how far the hand is from the camera.
- Curl detection uses tip-vs-MCP (knuckle), not tip-vs-PIP, which is
  more robust to hand rotation.
- hand_active gate: index tip must be clearly above wrist.
- Cursor mode requires ONLY index finger extended (others curled).
"""

import cv2
import mediapipe as mp
import numpy as np
from dataclasses import dataclass

from gm_helpers import landmark_to_screen, dist_lm, dist2d
import config


@dataclass
class HandState:
    present:     bool  = False
    hand_active: bool  = False   # index raised above wrist

    # Raw frame pixel coords (for drawing circles)
    r4x:  int = 0; r4y:  int = 0   # thumb tip
    r8x:  int = 0; r8y:  int = 0   # index tip
    r12x: int = 0; r12y: int = 0   # middle tip
    r16x: int = 0; r16y: int = 0   # ring tip
    r20x: int = 0; r20y: int = 0   # pinky tip

    # Screen coords (mapped to monitor resolution)
    s4x:  int = 0; s4y:  int = 0
    s8x:  int = 0; s8y:  int = 0
    s12x: int = 0; s12y: int = 0
    s16x: int = 0; s16y: int = 0
    s20x: int = 0; s20y: int = 0

    # Normalised distances (0.0–1.0 hand space) — resolution independent
    pinch_2f:    float = 1.0   # thumb ↔ index tip
    scroll_d:    float = 1.0   # index ↔ middle tip
    pinch_3f:    float = 1.0   # thumb ↔ avg(index, middle)
    thumb_pinky: float = 1.0   # thumb ↔ pinky tip
    spread_all:  float = 0.0   # mean of all tip-to-tip distances (normalised)

    # Per-finger extended flags  (True = finger is UP / extended)
    thumb_up:  bool = False
    index_up:  bool = False
    middle_up: bool = False
    ring_up:   bool = False
    pinky_up:  bool = False

    # Composite gesture shapes
    cursor_mode:    bool = False  # only index up
    scroll_mode:    bool = False  # index + middle up, rest down, tips close
    volume_mode:    bool = False  # 3-finger pinch (thumb close to index+middle)
    zoom_shape:     bool = False  # thumb+pinky out, index+middle+ring curled
    fingers_curled: bool = False  # fist (≥3 fingers curled)
    palm_open:      bool = False  # all fingers extended


class HandTracker:
    def __init__(self, screen_w, screen_h):
        self.sw = screen_w
        self.sh = screen_h
        self._mp   = mp.solutions.hands
        self._draw = mp.solutions.drawing_utils
        self._hands = self._mp.Hands(
            max_num_hands=config.MAX_HANDS,
            model_complexity=config.MODEL_COMPLEXITY,
            min_detection_confidence=config.MIN_DETECTION_CONFIDENCE,
            min_tracking_confidence=config.MIN_TRACKING_CONFIDENCE,
        )
        self.last_landmarks = None

    def process(self, frame_bgr, zx0, zx1, zy0, zy1):
        s = HandState()
        h, w = frame_bgr.shape[:2]
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        out = self._hands.process(rgb)

        self.last_landmarks = None
        if not out.multi_hand_landmarks:
            return s

        s.present = True
        hand = out.multi_hand_landmarks[0]
        self._draw.draw_landmarks(frame_bgr, hand)
        lm = hand.landmark
        self.last_landmarks = lm

        # ── Screen + raw coords ───────────────────────────────────────────────
        def _c(idx):
            return landmark_to_screen(lm[idx], w, h, zx0, zx1, zy0, zy1, self.sw, self.sh)

        s.r4x,  s.r4y,  s.s4x,  s.s4y  = _c(4)
        s.r8x,  s.r8y,  s.s8x,  s.s8y  = _c(8)
        s.r12x, s.r12y, s.s12x, s.s12y = _c(12)
        s.r16x, s.r16y, s.s16x, s.s16y = _c(16)
        s.r20x, s.r20y, s.s20x, s.s20y = _c(20)

        # ── Hand activation gate ──────────────────────────────────────────────
        # Index tip must be above wrist by HAND_ACTIVE_MARGIN (normalised units)
        s.hand_active = (lm[0].y - lm[8].y) > config.HAND_ACTIVE_MARGIN

        # ── Normalised distances ──────────────────────────────────────────────
        # Using normalised coords so thresholds are camera-distance independent
        s.pinch_2f    = dist_lm(lm[4], lm[8])
        s.scroll_d    = dist_lm(lm[8], lm[12])
        s.thumb_pinky = dist_lm(lm[4], lm[20])

        mid_x = (lm[8].x + lm[12].x) / 2
        mid_y = (lm[8].y + lm[12].y) / 2
        class _FakeLM:
            pass
        fl = _FakeLM(); fl.x = mid_x; fl.y = mid_y
        s.pinch_3f = dist_lm(lm[4], fl)

        tips = [lm[4], lm[8], lm[12], lm[16], lm[20]]
        dists = [dist_lm(tips[i], tips[j]) for i in range(5) for j in range(i+1, 5)]
        s.spread_all = float(np.mean(dists))

        # ── Finger extension (tip above MCP knuckle = extended) ───────────────
        # MCP indices: thumb=2, index=5, middle=9, ring=13, pinky=17
        # For thumb: compare tip x vs IP joint x (horizontal check works better)
        s.thumb_up  = lm[4].y  < lm[3].y                  # tip above IP
        s.index_up  = lm[8].y  < lm[5].y                  # tip above MCP
        s.middle_up = lm[12].y < lm[9].y
        s.ring_up   = lm[16].y < lm[13].y
        s.pinky_up  = lm[20].y < lm[17].y

        up_count    = sum([s.index_up, s.middle_up, s.ring_up, s.pinky_up])
        s.palm_open      = up_count == 4
        s.fingers_curled = up_count == 0

        # ── Gesture shapes ────────────────────────────────────────────────────

        # CURSOR: only index finger up, others down
        s.cursor_mode = (
            s.index_up and
            not s.middle_up and
            not s.ring_up and
            not s.pinky_up
        )

        # SCROLL: index + middle up, ring + pinky down, tips close
        s.scroll_mode = (
            s.index_up and s.middle_up and
            not s.ring_up and not s.pinky_up and
            s.scroll_d < config.SCROLL_THRESH_NORM
        )

        # VOLUME: 3-finger pinch — thumb close to index+middle average
        s.volume_mode = s.pinch_3f < config.VOL_PINCH_THRESH_NORM

        # ZOOM: hang-loose shape — thumb+pinky out, index+middle+ring curled
        s.zoom_shape = (
            s.thumb_up and s.pinky_up and
            not s.index_up and not s.middle_up and not s.ring_up and
            s.thumb_pinky > config.ZOOM_THRESH_NORM
        )

        return s

    def release(self):
        self._hands.close()