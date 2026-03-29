"""gm_overlay.py — All OpenCV drawing: HUD, badges, progress bars, fingertips."""

import cv2
import config

HUD_LINES = [
    " Index tip move          ->  Cursor",
    " Thumb+Index hold        ->  Left-click / Drag",
    " Thumb+Index quick       ->  Right-click",
    " Two rapid clicks        ->  Double-click",
    " Index+Middle close      ->  Scroll up/down",
    " 3-finger pinch + move   ->  Volume +/-",
    " Thumb+Pinky spread      ->  Zoom in/out",
    " Fist (hold)             ->  Play / Pause",
    " Peace sign              ->  Next track",
    " Thumbs up               ->  Prev track",
    " Palm spread (hold)      ->  Screenshot",
    " Q                       ->  Quit",
]

BADGE_COLORS = {
    "cursor":     (200, 200, 200),
    "scroll":     (255, 220, 80),
    "volume":     (80,  255, 130),
    "zoom":       (80,  220, 255),
    "media":      (255, 160, 80),
    "screenshot": (200, 80,  255),
    "inactive":   (60,  60,  60),
    "none":       (100, 100, 100),
}


def draw_hud(frame):
    if not config.HUD_ENABLED:
        return
    for i, line in enumerate(HUD_LINES):
        cv2.putText(frame, line, (10, 22 + i * 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.46, (180, 180, 255), 1)


def draw_zone(frame, x0, y0, x1, y1):
    cv2.rectangle(frame, (x0, y0), (x1, y1), (180, 180, 180), 1)


def draw_fingertips(frame, state):
    if not state.present:
        return
    cv2.circle(frame, (state.r8x,  state.r8y),  20, (0,   255, 255), cv2.FILLED)
    cv2.circle(frame, (state.r4x,  state.r4y),  20, (255, 100, 0),   cv2.FILLED)
    cv2.circle(frame, (state.r12x, state.r12y), 14, (100, 255, 100), cv2.FILLED)
    cv2.circle(frame, (state.r16x, state.r16y), 10, (180, 100, 255), cv2.FILLED)
    cv2.circle(frame, (state.r20x, state.r20y), 10, (255, 180, 100), cv2.FILLED)


def draw_overlay(frame, overlay_text):
    if not config.OVERLAY_ENABLED:
        return
    h = frame.shape[0]
    for i, (txt, col) in enumerate(overlay_text):
        cv2.putText(frame, txt, (10, h - 15 - i * 22),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.52, col, 1)


def draw_mode_badge(frame, mode):
    h, w = frame.shape[:2]
    color = BADGE_COLORS.get(mode, (200, 200, 200))
    label = f"[ {mode.upper()} ]"
    (tw, _), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
    cv2.putText(frame, label, (w - tw - 12, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)


def draw_gesture_progress_bar(frame, current, maximum, label, color=(120, 80, 255)):
    h, w = frame.shape[:2]
    bar_w  = int(w * 0.4)
    bar_h  = 12
    x0, y0 = (w - bar_w) // 2, h - 50
    ratio  = min(current / max(maximum, 1), 1.0)
    filled = int(bar_w * ratio)
    cv2.rectangle(frame, (x0, y0), (x0 + bar_w, y0 + bar_h), (60, 60, 60), cv2.FILLED)
    if filled > 0:
        cv2.rectangle(frame, (x0, y0), (x0 + filled, y0 + bar_h), color, cv2.FILLED)
    cv2.putText(frame, label, (x0, y0 - 5),
                cv2.FONT_HERSHEY_SIMPLEX, 0.44, color, 1)