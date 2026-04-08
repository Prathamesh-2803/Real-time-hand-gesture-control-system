import pyautogui
import config


class VolumeGesture:
    def __init__(self):
        self._active       = False
        self._anchor_y     = 0
        self._repeat_timer = 0

    def update(self, state, active):
        overlay = []
        if not active:
            self._active = False
            return overlay

        if not self._active:
            self._active       = True
            self._anchor_y     = state.s8y
            self._repeat_timer = 0
            return overlay

        delta = self._anchor_y - state.s8y   

        if abs(delta) < config.VOL_DEAD_ZONE:
            self._repeat_timer = 0
            overlay.append((f"3-finger pinch  d={state.pinch_3f:.3f}", (160, 255, 160)))
            return overlay

       
        magnitude = abs(delta)
        if magnitude > config.VOL_DEAD_ZONE * 4:
            delay = max(2, config.VOL_REPEAT_DELAY - 2)
        elif magnitude > config.VOL_DEAD_ZONE * 2:
            delay = max(3, config.VOL_REPEAT_DELAY - 1)
        else:
            delay = config.VOL_REPEAT_DELAY

        self._repeat_timer += 1
        if self._repeat_timer >= delay:
            self._repeat_timer = 0
            steps = max(1, int(magnitude / (config.VOL_DEAD_ZONE * 2)))
            steps = min(steps, 3)  

            if delta > 0:
                for _ in range(steps):
                    pyautogui.press('volumeup')
                overlay.append((f"VOL +{steps}", (0, 230, 100)))
            else:
                for _ in range(steps):
                    pyautogui.press('volumedown')
                overlay.append((f"VOL -{steps}", (0, 100, 230)))

           
            if magnitude > config.VOL_DEAD_ZONE * 5:
                self._anchor_y = state.s8y

        overlay.append((f"3-finger pinch  d={state.pinch_3f:.3f}", (160, 255, 160)))
        return overlay

    def reset(self):
        self._active = False