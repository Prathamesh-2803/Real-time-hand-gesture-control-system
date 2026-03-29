"""
main.py — Gesture Mouse entry point.
Run:  python main.py

Flat layout — all files in same folder, prefixed gm_ to avoid
any conflicts with mediapipe's internal modules.

Gesture shapes (mutually exclusive, checked in priority order):
  inactive     hand not raised above wrist
  screenshot   all fingers open + spread wide (hold)
  zoom         thumb+pinky out, index+middle+ring curled (hang-loose)
  volume       3-finger pinch (thumb close to index+middle avg)
  scroll       index+middle up and close together
  media        full fist / peace / thumbs-up
  cursor       only index finger up  ← DEFAULT
"""

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


def determine_mode(state):
    """
    Map HandState → mode string.
    Uses shape flags computed inside HandTracker (normalised, robust).
    """
    if not state.present:
        return "none"

    if not state.hand_active:
        return "inactive"

    # Screenshot: full open palm, spread wide
    if state.palm_open and state.spread_all > config.SPREAD_THRESH:
        return "screenshot"

    # Zoom: hang-loose shape (thumb+pinky out, rest curled)
    if state.zoom_shape:
        return "zoom"

    # Volume: 3-finger pinch — thumb close to index+middle
    if state.volume_mode:
        return "volume"

    # Scroll: index+middle up + close
    if state.scroll_mode:
        return "scroll"

    # Media: fist
    if state.fingers_curled:
        return "media"

    # Cursor: only index up (the clean default)
    if state.cursor_mode:
        return "cursor"

    # Fallback: any other shape (e.g. 3 fingers up) → cursor still
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

    logger    = GestureLogger(config.LOG_FILE, enabled=config.LOG_GESTURES)
    prev_mode = "none"
    hand_prev = False

    print("Gesture Mouse — press Q to quit")
    print("Point only your index finger to move cursor.")
    print("Raise hand above wrist level to activate.")

    while True:
        ret, frame = cam.read()
        if not ret:
            print("Camera read failed.")
            break

        fh, fw = frame.shape[:2]
        mx  = int(fw * config.MARGIN_RATIO)
        my  = int(fh * config.MARGIN_RATIO)
        zx0, zx1 = mx, fw - mx
        zy0 = my
        zy1 = fh - int(fh * config.BOTTOM_BIAS)

        draw_zone(frame, zx0, zy0, zx1, zy1)
        draw_hud(frame)

        state   = tracker.process(frame, zx0, zx1, zy0, zy1)
        overlay = []

        if state.present:
            draw_fingertips(frame, state)
            mode = determine_mode(state)

            if mode != prev_mode:
                logger.log(mode, f"prev={prev_mode}")
                prev_mode = mode

            if mode == "inactive":
                # Reset everything so no gesture fires accidentally
                for g in [cursor_g, scroll_g, volume_g, media_g, screenshot_g, zoom_g]:
                    g.reset()
                overlay.append(("Raise hand to activate", (90, 90, 90)))

            else:
                overlay += cursor_g.update(    state, mode == "cursor")
                overlay += scroll_g.update(    state, mode == "scroll")
                overlay += volume_g.update(    state, mode == "volume")
                overlay += zoom_g.update(      state, mode == "zoom")
                overlay += screenshot_g.update(state, mode == "screenshot")
                overlay += media_g.update(     state, tracker.last_landmarks,
                                               mode == "media")

                if mode == "screenshot":
                    draw_gesture_progress_bar(
                        frame, screenshot_g._hold, config.SPREAD_HOLD_FRAMES,
                        "Spread palm - hold to screenshot", (200, 80, 255))
                elif mode == "media" and media_g._fist_frames > 0:
                    draw_gesture_progress_bar(
                        frame, media_g._fist_frames, config.FIST_HOLD_FRAMES,
                        "Fist - hold to play/pause", (255, 180, 0))

            draw_mode_badge(frame, mode)
            hand_prev = True

        else:
            if hand_prev:
                for g in [cursor_g, scroll_g, volume_g, media_g, screenshot_g, zoom_g]:
                    g.reset()
                logger.log("hand_lost")
            hand_prev = False
            draw_mode_badge(frame, "none")

        draw_overlay(frame, overlay)
        cv2.imshow("Gesture Mouse", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    pyautogui.mouseUp(button="left")
    logger.close()
    tracker.release()
    cam.release()
    cv2.destroyAllWindows()
    print("Stopped.")


if __name__ == "__main__":
    main()