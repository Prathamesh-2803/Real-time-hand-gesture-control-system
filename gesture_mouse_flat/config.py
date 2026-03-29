"""
config.py — All tunable parameters.

IMPORTANT: Distance thresholds are now in NORMALISED landmark space (0.0–1.0).
This makes them independent of screen resolution and camera distance.

Typical normalised distances at ~60cm from webcam:
  Relaxed pinch (thumb near index): ~0.05–0.08
  Wide pinch (fingers apart):       ~0.15–0.25
  Thumb to pinky spread:            ~0.30–0.50
"""

# ── Camera ────────────────────────────────────────────────────────────────────
CAMERA_INDEX             = 0
CAMERA_WIDTH             = 1280
CAMERA_HEIGHT            = 720
CAMERA_FPS               = 60

# ── MediaPipe ─────────────────────────────────────────────────────────────────
MAX_HANDS                = 1
MODEL_COMPLEXITY         = 1
MIN_DETECTION_CONFIDENCE = 0.80
MIN_TRACKING_CONFIDENCE  = 0.70

# ── Active zone — crop frame edges so hand doesn't need to reach corners ──────
MARGIN_RATIO = 0.10   # 10% margin on each side
BOTTOM_BIAS  = 0.10

# ── Cursor ────────────────────────────────────────────────────────────────────
CURSOR_EMA_ALPHA = 0.35   # 0.1=very smooth/laggy  0.5=responsive/jittery
DEAD_ZONE        = 4      # px — ignore movements smaller than this

# ── Hand activation gate ──────────────────────────────────────────────────────
# Index tip must be this far ABOVE wrist (normalised y, higher = stricter).
# 0.04 means index tip must be at least 4% of frame height above wrist.
HAND_ACTIVE_MARGIN = 0.04

# ── Click thresholds (normalised 0.0–1.0) ────────────────────────────────────
CLICK_THRESH_NORM   = 0.06   # thumb+index tip distance to trigger click
CLICK_COOLDOWN      = 15     # frames before next click allowed
PINCH_FRAMES        = 5      # frames — quick pinch (<5f) = right-click
DOUBLE_CLICK_WINDOW = 22     # frames between two clicks = double-click
DRAG_HOLD_FRAMES    = 20     # frames holding pinch before drag starts

# ── Scroll (normalised) ───────────────────────────────────────────────────────
SCROLL_THRESH_NORM = 0.07   # index+middle tip closeness to enter scroll mode
SCROLL_SPEED       = 8      # scroll units per frame-delta
SCROLL_DEAD_ZONE   = 10     # px screen delta before scroll fires

# ── Volume (normalised) ───────────────────────────────────────────────────────
VOL_PINCH_THRESH_NORM = 0.07   # thumb to avg(index+middle) distance
VOL_REPEAT_DELAY      = 6      # frames between repeated volume steps
VOL_DEAD_ZONE         = 10     # px screen delta before volume fires

# ── Zoom (normalised) ─────────────────────────────────────────────────────────
ZOOM_THRESH_NORM = 0.35   # thumb+pinky spread must exceed this

# ── Screenshot ────────────────────────────────────────────────────────────────
SPREAD_THRESH      = 0.30   # normalised mean spread of all tips
SPREAD_HOLD_FRAMES = 25

# ── Media controls ────────────────────────────────────────────────────────────
FIST_HOLD_FRAMES = 18

# ── HUD ───────────────────────────────────────────────────────────────────────
HUD_ENABLED     = True
OVERLAY_ENABLED = True

# ── Logging ───────────────────────────────────────────────────────────────────
LOG_GESTURES = True
LOG_FILE     = "gesture_log.csv"