import time
import cv2
import pyautogui

import config
from gm_camera     import Camera
from gm_tracker    import HandTracker
from gm_cursor     import CursorGesture
from gm_scroll     import ScrollGesture
from gm_volume     import VolumeGesture
from gm_media      import MediaGesture
from gm_screenshot import ScreenshotGesture
from gm_zoom       import ZoomGesture
from gm_overlay    import (
    draw_hud, draw_zone, draw_fingertips,
    draw_overlay, draw_mode_badge, draw_gesture_progress_bar,
)
from gm_logger import GestureLogger


pyautogui.FAILSAFE = True
pyautogui.PAUSE    = 0

screen_w, screen_h = pyautogui.size()


def _raw_mode(state):
    """Compute candidate mode from HandState. Hysteresis applied in main()."""
    if not state.present:
        return "none"
    if not state.hand_active:
        return "inactive"
    if state.palm_open and state.spread_all > config.SPREAD_THRESH:
        return "screenshot"
    # Zoom: thumb + index only (zoom_shape gate already includes hysteresis)
    if state.zoom_shape:
        return "zoom"
    if state.volume_mode:
        return "volume"
    if state.scroll_mode:
        return "scroll"
    if state.fingers_curled:
        return "media"
    if state.cursor_mode:
        return "cursor"
    return "cursor"


def main():
    cam     = Camera()
    tracker = HandTracker(screen_w, screen_h)

    cursor_g     = CursorGesture()
    scroll_g     = ScrollGesture()
    volume_g     = VolumeGesture()
    media_g      = MediaGesture()
    screenshot_g = ScreenshotGesture()
    zoom_g       = ZoomGesture()

    all_gestures = [cursor_g, scroll_g, volume_g, media_g,
                    screenshot_g, zoom_g]

    logger = GestureLogger(config.LOG_FILE, enabled=config.LOG_GESTURES)

    _candidate_mode   = "none"
    _candidate_frames = 0
    mode              = "none"
    prev_mode         = "none"
    hand_prev         = False

    _fps_t      = time.time()
    _fps_frames = 0
    _fps        = 0.0

    print("=" * 50)
    print("  Gesture Mouse v3")
    print("  Full-screen active zone")
    print("  Point index finger       → move cursor")
    print("  Thumb+Index spread/close → zoom in/out")
    print("  Raise hand above wrist   → activate")
    print("  Press Q to quit")
    print("=" * 50)

    while True:
        ret, frame = cam.read()
        if not ret:
            print("[ERROR] Camera read failed — check CAMERA_INDEX in config.py")
            break

        _fps_frames += 1
        now = time.time()
        if now - _fps_t >= 1.0:
            _fps        = _fps_frames / (now - _fps_t)
            _fps_frames = 0
            _fps_t      = now
        cv2.setWindowTitle("Gesture Mouse v3", f"Gesture Mouse v3  |  {_fps:.0f} fps")

        fh, fw = frame.shape[:2]

        mx  = int(fw * config.MARGIN_RATIO)
        my  = int(fh * config.MARGIN_RATIO)
        zx0, zx1 = mx, fw - mx
        zy0 = my
        zy1 = fh - int(fh * config.BOTTOM_BIAS)

        if config.MARGIN_RATIO > 0.01 or config.BOTTOM_BIAS > 0.01:
            draw_zone(frame, zx0, zy0, zx1, zy1)

        draw_hud(frame)

        state   = tracker.process(frame, zx0, zx1, zy0, zy1)
        overlay = []

        raw = _raw_mode(state)
        if raw == _candidate_mode:
            _candidate_frames += 1
        else:
            _candidate_mode   = raw
            _candidate_frames = 1

        if raw in ("none", "inactive") or \
                _candidate_frames >= config.MODE_HYSTERESIS_FRAMES:
            mode = raw

        if state.present:
            draw_fingertips(frame, state, mode)

            if mode != prev_mode:
                logger.log(mode, f"prev={prev_mode}")
                _reset_map = {
                    "cursor":     cursor_g,
                    "scroll":     scroll_g,
                    "volume":     volume_g,
                    "zoom":       zoom_g,
                    "screenshot": screenshot_g,
                    "media":      media_g,
                }
                if prev_mode in _reset_map:
                    _reset_map[prev_mode].reset()
                prev_mode = mode

            if mode == "inactive":
                for g in all_gestures:
                    g.reset()
                overlay.append(("Raise hand to activate", (90, 90, 90)))

            else:
                overlay += cursor_g.update(     state, mode == "cursor")
                overlay += scroll_g.update(     state, mode == "scroll")
                overlay += volume_g.update(     state, mode == "volume")
                overlay += zoom_g.update(       state, mode == "zoom")
                overlay += screenshot_g.update( state, mode == "screenshot")
                overlay += media_g.update(      state, tracker.last_landmarks,
                                                mode == "media")

                if mode == "screenshot":
                    draw_gesture_progress_bar(
                        frame, screenshot_g._hold,
                        config.SPREAD_HOLD_FRAMES,
                        "Spread palm — hold to screenshot", (200, 80, 255))

                elif mode == "media" and media_g._fist_frames > 0:
                    draw_gesture_progress_bar(
                        frame, media_g._fist_frames,
                        config.FIST_HOLD_FRAMES,
                        "Fist — hold to play/pause", (255, 180, 0))

                elif mode == "cursor" and hasattr(cursor_g, '_pinch_frames') \
                        and cursor_g._pinch_frames > 0 \
                        and cursor_g._state == cursor_g._ST_PINCHED:
                    pct_frames = cursor_g._pinch_frames
                    if pct_frames > config.PINCH_FRAMES:
                        draw_gesture_progress_bar(
                            frame, pct_frames,
                            config.DRAG_HOLD_FRAMES,
                            "Hold pinch for drag", (0, 180, 255))

            draw_mode_badge(frame, mode)
            hand_prev = True

        else:
            if hand_prev:
                for g in all_gestures:
                    g.reset()
                logger.log("hand_lost")
            hand_prev         = False
            mode              = "none"
            _candidate_mode   = "none"
            _candidate_frames = 0
            prev_mode         = "none"
            draw_mode_badge(frame, "none")

        cv2.putText(frame, f"{_fps:.0f} fps",
                    (fw - 80, fh - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (100, 100, 100), 1,
                    cv2.LINE_AA)

        draw_overlay(frame, overlay)
        cv2.imshow("Gesture Mouse v3", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == ord('Q'):
            break

    try:
        pyautogui.mouseUp(button="left")
    except Exception:
        pass
    logger.close()
    tracker.release()
    cam.release()
    cv2.destroyAllWindows()
    print("Gesture Mouse stopped.")


if __name__ == "__main__":
    main()