"""
Lightweight in-memory session statistics.
Shared singleton updated by jobs; read by the status bar.
"""
from __future__ import annotations
import time
from collections import deque
from PyQt6.QtCore import QObject, pyqtSignal


class SessionStats(QObject):
    updated = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._files_done    = 0
        self._files_skipped = 0
        self._jobs_done     = 0
        self._jobs_error    = 0
        self._active_jobs   = 0
        self._session_start = time.monotonic()
        # Rolling speed: deque of (timestamp, bytes) pairs over a 5-second window
        self._speed_window: deque[tuple[float, int]] = deque()
        self._bytes_total: int = 0

    # ── Mutators ──────────────────────────────────────────────────────────────

    def record_file(self):
        self._files_done += 1
        self.updated.emit()

    def record_bytes(self, n: int):
        """Record n bytes received; used to compute rolling download speed."""
        now = time.monotonic()
        self._bytes_total += n
        self._speed_window.append((now, n))
        # Prune entries older than 5 seconds
        cutoff = now - 5.0
        while self._speed_window and self._speed_window[0][0] < cutoff:
            self._speed_window.popleft()
        self.updated.emit()

    def clear_speed(self):
        """Call when no jobs are active so the speed reads 0."""
        self._speed_window.clear()
        self.updated.emit()

    def record_skip(self):
        self._files_skipped += 1
        self.updated.emit()

    def record_job_done(self):
        self._jobs_done += 1
        self._active_jobs = max(0, self._active_jobs - 1)
        self.updated.emit()

    def record_job_error(self):
        self._jobs_error += 1
        self._active_jobs = max(0, self._active_jobs - 1)
        self.updated.emit()

    def record_job_started(self):
        self._active_jobs += 1
        self.updated.emit()

    def record_job_cancelled(self):
        self._active_jobs = max(0, self._active_jobs - 1)
        self.updated.emit()

    # ── Accessors ─────────────────────────────────────────────────────────────

    @property
    def files_done(self) -> int:
        return self._files_done

    @property
    def files_skipped(self) -> int:
        return self._files_skipped

    @property
    def jobs_done(self) -> int:
        return self._jobs_done

    @property
    def jobs_error(self) -> int:
        return self._jobs_error

    @property
    def active_jobs(self) -> int:
        return self._active_jobs

    @property
    def bytes_per_sec(self) -> float:
        """Rolling average bytes/sec over the last 5 seconds."""
        if len(self._speed_window) < 2:
            return 0.0
        window_secs = self._speed_window[-1][0] - self._speed_window[0][0]
        if window_secs <= 0:
            return 0.0
        total_bytes = sum(b for _, b in self._speed_window)
        return total_bytes / window_secs

    @property
    def speed_str(self) -> str:
        bps = self.bytes_per_sec
        if bps <= 0:
            return ""
        if bps >= 1_048_576:
            return f"{bps / 1_048_576:.1f} MB/s"
        if bps >= 1024:
            return f"{bps / 1024:.0f} KB/s"
        return f"{bps:.0f} B/s"

    @property
    def elapsed_str(self) -> str:
        secs = int(time.monotonic() - self._session_start)
        h, rem = divmod(secs, 3600)
        m, s   = divmod(rem, 60)
        if h:
            return f"{h}h {m}m"
        if m:
            return f"{m}m {s}s"
        return f"{s}s"


# Global singleton
_stats = SessionStats()

def get_stats() -> SessionStats:
    return _stats
