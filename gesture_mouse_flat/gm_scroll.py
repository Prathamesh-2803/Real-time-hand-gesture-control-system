import pyautogui
import config


class ScrollGesture:
    def __init__(self):
        self._active    = False
        self._anchor_y  = 0
        self._last_dir  = 0   

    def update(self, state, active):
        overlay = []
        if not active:
            self._active   = False
            self._last_dir = 0
            return overlay

        if not self._active:
            self._active   = True
            self._anchor_y = state.s8y
            self._last_dir = 0
            return overlay

        delta = self._anchor_y - state.s8y  

        if abs(delta) < config.SCROLL_DEAD_ZONE:
           
            self._last_dir = 0
            direction = "SCROLL READY"
        else:
           
            magnitude = abs(delta)
            steps = max(1, int(magnitude / config.SCROLL_SPEED))

            if delta > 0:
                pyautogui.scroll(steps)
                self._last_dir = 1
                direction = f"SCROLL UP  ({steps})"
                overlay.append((direction, (255, 220, 0)))
            else:
                pyautogui.scroll(-steps)
                self._last_dir = -1
                direction = f"SCROLL DOWN ({steps})"
                overlay.append((direction, (255, 220, 0)))

           
            if magnitude > config.SCROLL_ANCHOR_RESET_PX:
                self._anchor_y = state.s8y

        overlay.append((f"2-finger scroll  d={state.scroll_d:.3f}", (255, 220, 100)))
        return overlay

    def reset(self):
        self._active   = False
        self._last_dir = 0