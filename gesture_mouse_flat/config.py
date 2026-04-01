"""
config.py — All tunable parameters. v3 — Full screen, smooth cursor, reliable clicks.

KEY CHANGES v3:
- MARGIN_RATIO = 0.0  → Full screen coverage, no border crop
- BOTTOM_BIAS  = 0.0  → Full vertical range
- One-Euro filter tuned for maximum smoothness (lower beta, lower min_cutoff)
- Click thresholds relaxed for reliable detection
- Dead zone reduced to 0 so cursor follows every movement
- All gesture thresholds recalibrated
"""

# ── Camera ────────────────────────────────────────────────────────────────────
CAMERA_INDEX             = 0
CAMERA_WIDTH             = 1280
CAMERA_HEIGHT            = 720
CAMERA_FPS               = 60

# ── MediaPipe ─────────────────────────────────────────────────────────────────
MAX_HANDS                = 1
MODEL_COMPLEXITY         = 1
MIN_DETECTION_CONFIDENCE = 0.70
MIN_TRACKING_CONFIDENCE  = 0.60

# ── Active zone — FULL SCREEN, no margins ─────────────────────────────────────
MARGIN_RATIO = 0.0    # 0% margin = full screen coverage
BOTTOM_BIAS  = 0.0    # 0% bottom bias = full vertical range

# ── Cursor ────────────────────────────────────────────────────────────────────
# One-Euro filter params — lower min_cutoff = smoother at rest
# higher beta = less lag when moving fast
CURSOR_OEF_MIN_CUTOFF  = 0.5    # Hz — lower = more smoothing at rest
CURSOR_OEF_BETA        = 0.006  # lower = less lag at speed (sweet spot)
CURSOR_OEF_D_CUTOFF    = 1.0    # Hz
DEAD_ZONE              = 0      # px — set to 0: cursor follows all movement

# ── Hand activation gate ──────────────────────────────────────────────────────
HAND_ACTIVE_MARGIN       = 0.02   # index tip above wrist (normalised y) — relaxed
HAND_ACTIVE_HYSTERESIS   = 2      # frames to activate (faster response)
HAND_INACTIVE_HYSTERESIS = 4      # frames to deactivate

# ── Click thresholds (normalised 0.0–1.0) ────────────────────────────────────
CLICK_THRESH_NORM      = 0.065  # thumb+index tip distance to ENTER pinch
CLICK_RELEASE_NORM     = 0.110  # must EXCEED this to exit pinch (wide gap = no flicker)
CLICK_COOLDOWN         = 12     # frames before next click allowed
PINCH_FRAMES           = 14     # frames — pinch held LESS than this = right-click
                                 # pinch held MORE than this = left-click
DOUBLE_CLICK_WINDOW    = 30     # frames between two left-clicks = double-click
DRAG_HOLD_FRAMES       = 28     # frames holding pinch before drag starts
DRAG_MIN_MOVE_PX       = 10     # px — drag only fires if cursor moved this far

# ── Mode-switch hysteresis ────────────────────────────────────────────────────
MODE_HYSTERESIS_FRAMES = 3

# ── Scroll (normalised) ───────────────────────────────────────────────────────
SCROLL_THRESH_NORM     = 0.075
SCROLL_EXIT_NORM       = 0.11
SCROLL_SPEED           = 5
SCROLL_DEAD_ZONE       = 10
SCROLL_ANCHOR_RESET_PX = 70

# ── Volume (normalised) ───────────────────────────────────────────────────────
VOL_PINCH_THRESH_NORM  = 0.075
VOL_EXIT_NORM          = 0.11
VOL_REPEAT_DELAY       = 5
VOL_DEAD_ZONE          = 12

# ── Zoom (normalised) ─────────────────────────────────────────────────────────
ZOOM_THRESH_NORM       = 0.30
ZOOM_DELTA_THRESH      = 0.016
ZOOM_COOLDOWN          = 12

# ── Screenshot ────────────────────────────────────────────────────────────────
SPREAD_THRESH          = 0.26
SPREAD_HOLD_FRAMES     = 30

# ── Media controls ────────────────────────────────────────────────────────────
FIST_HOLD_FRAMES       = 20

# ── Smoothing for gesture distances ───────────────────────────────────────────
DIST_SMOOTH_ALPHA      = 0.40

# ── HUD ───────────────────────────────────────────────────────────────────────
HUD_ENABLED     = True
OVERLAY_ENABLED = True

# ── Logging ───────────────────────────────────────────────────────────────────
LOG_GESTURES = True
LOG_FILE     = "gesture_log.csv"

# ── Legacy EMA (kept for backward compat) ─────────────────────────────────────
CURSOR_EMA_ALPHA      = 0.40
CURSOR_EMA_ALPHA_FAST = 0.70
CURSOR_FAST_MOVE_PX   = 60