"""
gm_overlay.py — All OpenCV drawing: HUD, badges, progress bars, fingertips.

CHANGES v3:
- REMOVED the line drawn between thumb and index tip (no more weird line)
- draw_fingertips: cleaner dot display, index tip pulses in cursor mode
- draw_pinch_indicator: shows a subtle arc-distance text only, no line
- All other drawing unchanged
"""

import cv2
import config

HUD_LINES = [
    " Index only            →  Move cursor",
    " Thumb+Index pinch     →  Left-click (release to fire)",
    " Quick pinch (<8f)     →  Right-click",
    " Two left-clicks       →  Double-click",
    " Long pinch + move     →  Drag",
    " Index+Middle close    →  Scroll (velocity)",
    " 3-finger pinch+move   →  Volume ±",
    " Thumb+Pinky spread    →  Zoom in/out",
    " Fist hold             →  Play / Pause",
    " Peace sign  (3f hold) →  Next track",
    " Thumbs-up   (3f hold) →  Prev track",
    " Palm spread  (hold)   →  Screenshot",
    " Q                     →  Quit",
]

BADGE_COLORS = {
    "cursor":     (200, 200, 200),
    "scroll":     (255, 220, 80),
    "volume":     (80,  255, 130),
    "zoom":       (80,  220, 255),
    "media":      (255, 160, 80),
    "screenshot": (200, 80,  255),
    "inactive":   (80,  80,  80),
    "none":       (100, 100, 100),
}

TIP_COLORS = {
    "index":  (0,   255, 255),
    "thumb":  (255, 100, 0),
    "middle": (100, 255, 100),
    "ring":   (180, 100, 255),
    "pinky":  (255, 180, 100),
}


def _put_text_bg(frame, text, pos, font_scale, color, thickness=1, bg_alpha=0.45):
    font = cv2.FONT_HERSHEY_SIMPLEX
    (tw, th), baseline = cv2.getTextSize(text, font, font_scale, thickness)
    x, y = pos
    pad = 3
    overlay = frame.copy()
    cv2.rectangle(overlay,
                  (x - pad, y - th - pad),
                  (x + tw + pad, y + baseline + pad),
                  (0, 0, 0), cv2.FILLED)
    cv2.addWeighted(overlay, bg_alpha, frame, 1 - bg_alpha, 0, frame)
    cv2.putText(frame, text, (x, y), font, font_scale, color, thickness,
                cv2.LINE_AA)


def draw_hud(frame):
    if not config.HUD_ENABLED:
        return
    for i, line in enumerate(HUD_LINES):
        cv2.putText(frame, line, (10, 22 + i * 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.43, (180, 180, 255), 1,
                    cv2.LINE_AA)


def draw_zone(frame, x0, y0, x1, y1):
    """Draw the active zone border — now effectively full frame."""
    # Only draw if there's actually a meaningful margin (skip if full screen)
    if x0 > 2 or y0 > 2:
        cv2.rectangle(frame, (x0, y0), (x1, y1), (100, 100, 100), 1)


def draw_fingertips(frame, state, mode="cursor"):
    """
    Draw coloured dots on each fingertip.
    NO line between thumb and index — removed in v3.
    Index tip pulses larger when cursor mode is active.
    """
    if not state.present:
        return

    # Index tip — larger when cursor mode (shows it's the control point)
    idx_r = 20 if mode == "cursor" else 12
    cv2.circle(frame, (state.r8x, state.r8y), idx_r,
               TIP_COLORS["index"], cv2.FILLED)
    cv2.circle(frame, (state.r8x, state.r8y), idx_r + 2,
               (255, 255, 255), 1)

    # Thumb tip
    cv2.circle(frame, (state.r4x,  state.r4y),  16,
               TIP_COLORS["thumb"],  cv2.FILLED)

    # Middle tip
    cv2.circle(frame, (state.r12x, state.r12y), 11,
               TIP_COLORS["middle"], cv2.FILLED)

    # Ring tip
    cv2.circle(frame, (state.r16x, state.r16y), 9,
               TIP_COLORS["ring"],   cv2.FILLED)

    # Pinky tip
    cv2.circle(frame, (state.r20x, state.r20y), 9,
               TIP_COLORS["pinky"],  cv2.FILLED)

    # ── Pinch proximity indicator ────────────────────────────────────────────
    # Instead of a line, show a small filled circle between thumb+index
    # that grows red as they approach (much cleaner visually)
    t = max(0.0, min(1.0, 1.0 - state.pinch_2f / 0.10))
    if t > 0.3:
        mid_x = (state.r4x + state.r8x) // 2
        mid_y = (state.r4y + state.r8y) // 2
        r     = max(3, int(t * 12))
        color = (int(t * 30), int((1 - t) * 220), int((1 - t) * 255))
        cv2.circle(frame, (mid_x, mid_y), r, color, cv2.FILLED)


def draw_overlay(frame, overlay_text):
    if not config.OVERLAY_ENABLED:
        return
    h = frame.shape[0]
    for i, (txt, col) in enumerate(overlay_text):
        _put_text_bg(frame, txt, (10, h - 15 - i * 24), 0.52, col)


def draw_mode_badge(frame, mode):
    h, w = frame.shape[:2]
    color = BADGE_COLORS.get(mode, (200, 200, 200))
    label = f"[ {mode.upper()} ]"
    font  = cv2.FONT_HERSHEY_SIMPLEX
    (tw, th), _ = cv2.getTextSize(label, font, 0.72, 2)
    x = w - tw - 14
    y = 32
    pad = 5
    overlay = frame.copy()
    cv2.rectangle(overlay, (x - pad, y - th - pad), (x + tw + pad, y + pad),
                  (0, 0, 0), cv2.FILLED)
    cv2.addWeighted(overlay, 0.5, frame, 0.5, 0, frame)
    cv2.putText(frame, label, (x, y), font, 0.72, color, 2, cv2.LINE_AA)


def draw_gesture_progress_bar(frame, current, maximum, label,
                               color=(120, 80, 255)):
    if maximum <= 0:
        return
    h, w = frame.shape[:2]
    bar_w  = int(w * 0.40)
    bar_h  = 14
    x0     = (w - bar_w) // 2
    y0     = h - 55
    ratio  = min(current / maximum, 1.0)
    filled = int(bar_w * ratio)
    pct    = int(ratio * 100)

    cv2.rectangle(frame, (x0, y0), (x0 + bar_w, y0 + bar_h),
                  (40, 40, 40), cv2.FILLED)
    if filled > 0:
        cv2.rectangle(frame, (x0, y0), (x0 + filled, y0 + bar_h),
                      color, cv2.FILLED)
    cv2.rectangle(frame, (x0, y0), (x0 + bar_w, y0 + bar_h),
                  (120, 120, 120), 1)
    cv2.putText(frame, f"{label}  {pct}%", (x0, y0 - 6),
                cv2.FONT_HERSHEY_SIMPLEX, 0.44, color, 1, cv2.LINE_AA)