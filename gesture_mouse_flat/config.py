CAMERA_INDEX             = 0
CAMERA_WIDTH             = 1280
CAMERA_HEIGHT            = 720
CAMERA_FPS               = 60


MAX_HANDS                = 1
MODEL_COMPLEXITY         = 1
MIN_DETECTION_CONFIDENCE = 0.75   # raised: fewer false detections
MIN_TRACKING_CONFIDENCE  = 0.65   # raised: more stable tracking


MARGIN_RATIO = 0.08
BOTTOM_BIAS  = 0.0


CURSOR_OEF_MIN_CUTOFF  = 0.8    # slightly higher = less lag when still
CURSOR_OEF_BETA        = 0.04   # much higher = faster response on fast moves
CURSOR_OEF_D_CUTOFF    = 1.0
DEAD_ZONE              = 3      # px — suppresses micro-tremor noise


HAND_ACTIVE_MARGIN       = 0.02
HAND_ACTIVE_HYSTERESIS   = 2
HAND_INACTIVE_HYSTERESIS = 4


CLICK_THRESH_NORM      = 0.055  # pinch-in threshold (left click arm)
CLICK_RELEASE_NORM     = 0.100  # must open this far to confirm release
RIGHT_CLICK_THRESH     = 0.050  # tighter — right click needs a more deliberate quick pinch
CLICK_COOLDOWN         = 15     # frames before another click can fire
PINCH_FRAMES           = 10     # frames pinched to count as "held" (not right-click)
DOUBLE_CLICK_WINDOW    = 28
DRAG_HOLD_FRAMES       = 30
DRAG_MIN_MOVE_PX       = 12

MODE_HYSTERESIS_FRAMES = 3


SCROLL_THRESH_NORM     = 0.075
SCROLL_EXIT_NORM       = 0.11
SCROLL_SPEED           = 5
SCROLL_DEAD_ZONE       = 10
SCROLL_ANCHOR_RESET_PX = 70


VOL_PINCH_THRESH_NORM  = 0.075
VOL_EXIT_NORM          = 0.11
VOL_REPEAT_DELAY       = 5
VOL_DEAD_ZONE          = 12


# --- Zoom (thumb + index pinch distance) ---
# Shape active when thumb_up + index_up only, distance > ZOOM_SHAPE_MIN_DIST
ZOOM_SHAPE_MIN_DIST    = 0.04   # min thumb-index dist to enter zoom mode (not a pinch)
ZOOM_SHAPE_MAX_DIST    = 0.45   # sanity cap — ignore if fingers are impossibly far
ZOOM_DELTA_THRESH      = 0.018  # min change in normalised dist per frame to fire
ZOOM_COOLDOWN          = 14     # frames between consecutive zoom events
ZOOM_HIST_LEN          = 4      # smoothing history length (frames)

# Legacy — kept for backwards compat, no longer used for shape detection
ZOOM_THRESH_NORM       = 0.30


SPREAD_THRESH          = 0.26
SPREAD_HOLD_FRAMES     = 30


FIST_HOLD_FRAMES       = 20


DIST_SMOOTH_ALPHA      = 0.40


HUD_ENABLED     = False
OVERLAY_ENABLED = True


LOG_GESTURES = True
LOG_FILE     = "gesture_log.csv"


CURSOR_EMA_ALPHA      = 0.40
CURSOR_EMA_ALPHA_FAST = 0.70
CURSOR_FAST_MOVE_PX   = 60