"""gm_logger.py — CSV gesture event logger."""

import csv, time
from pathlib import Path


class GestureLogger:
    def __init__(self, filepath, enabled=True):
        self.enabled = enabled
        self._file = self._writer = None
        if enabled:
            self._file = open(filepath, "w", newline="")
            self._writer = csv.writer(self._file)
            self._writer.writerow(["timestamp", "gesture", "detail"])

    def log(self, gesture, detail=""):
        if self.enabled and self._writer:
            self._writer.writerow([f"{time.time():.3f}", gesture, detail])
            self._file.flush()

    def close(self):
        if self._file:
            self._file.close()