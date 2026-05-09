from __future__ import annotations
import re
import subprocess
import time
from enum import Enum
from PyQt6.QtCore import QObject, QThread, pyqtSignal, pyqtSlot

from core.options import DownloadOptions
from core.url_detector import detect_site


class JobStatus(Enum):
    QUEUED    = "queued"
    RUNNING   = "running"
    DONE      = "done"
    ERROR     = "error"
    CANCELLED = "cancelled"


class _Worker(QObject):
    """Runs gallery-dl in a background thread, parsing stdout into typed signals."""

    log_line      = pyqtSignal(str, str)   # (level, text)
    progress_tick = pyqtSignal(int, int)   # (files_done, files_total)
    file_done     = pyqtSignal()           # emitted for every completed file
    video_done    = pyqtSignal()           # emitted specifically for video files
    file_skipped  = pyqtSignal()           # emitted for skipped/already-exists files
    bytes_received = pyqtSignal(int)       # bytes downloaded for a single file
    finished      = pyqtSignal(int)        # exit code

    # gallery-dl log format: [gallery-dl][level] message
    _LOG_RE   = re.compile(r"\[gallery-dl\]\[(\w+)\]\s*(.*)")
    # Progress embedded in log:  Downloading image (N/M)  or  # N
    _PROG_RE  = re.compile(r"\((\d+)/(\d+)\)")
    # "Skipping" lines
    _SKIP_RE  = re.compile(r"Skipping|already exists", re.IGNORECASE)
    # Completed file download lines
    _FILE_RE  = re.compile(r"^Downloading\b", re.IGNORECASE)
    # Video file extensions — used to split image vs video counts
    _VIDEO_EXT_RE = re.compile(
        r"\.(mp4|webm|mov|avi|mkv|m4v|flv|ts|wmv|3gp)\b", re.IGNORECASE
    )
    # Byte count in gallery-dl download lines, e.g. "(1234567 bytes)" or "1.23 MiB"
    _BYTES_RE = re.compile(
        r"(?:(\d+)\s*bytes|([\d.]+)\s*(KiB|MiB|GiB|KB|MB|GB))",
        re.IGNORECASE,
    )

    def __init__(self, cmd: list[str]):
        super().__init__()
        self._cmd = cmd
        self._proc: subprocess.Popen | None = None
        self._cancelled = False

    def run(self):
        try:
            self._proc = subprocess.Popen(
                self._cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            for raw in self._proc.stdout:
                line = raw.rstrip()
                if not line:
                    continue

                m = self._LOG_RE.match(line)
                level = m.group(1).lower() if m else "info"
                text  = m.group(2)         if m else line
                self.log_line.emit(level, text)

                # Progress counter
                pm = self._PROG_RE.search(text)
                if pm:
                    self.progress_tick.emit(int(pm.group(1)), int(pm.group(2)))

                # Count each completed or skipped file
                if self._FILE_RE.search(text):
                    if self._SKIP_RE.search(text):
                        self.file_skipped.emit()
                    else:
                        self.file_done.emit()
                        if self._VIDEO_EXT_RE.search(text):
                            self.video_done.emit()
                        # Parse file size for speed tracking
                        bm = self._BYTES_RE.search(text)
                        if bm:
                            if bm.group(1):   # raw bytes
                                self.bytes_received.emit(int(bm.group(1)))
                            else:
                                val  = float(bm.group(2))
                                unit = bm.group(3).upper()
                                mult = {"KIB": 1024, "KB": 1024,
                                        "MIB": 1048576, "MB": 1048576,
                                        "GIB": 1073741824, "GB": 1073741824}
                                self.bytes_received.emit(int(val * mult.get(unit, 1)))

            self._proc.stdout.close()
            try:
                self._proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                # Process ignored SIGTERM — escalate to SIGKILL
                self._proc.kill()
                self._proc.wait()
            code = self._proc.returncode if not self._cancelled else -1
            self.finished.emit(code)

        except Exception as exc:
            self.log_line.emit("error", str(exc))
            self.finished.emit(1)

    def cancel(self):
        self._cancelled = True
        if self._proc and self._proc.poll() is None:
            self._proc.terminate()


class DownloadJob(QObject):
    """Public-facing job object. Owns the worker thread."""

    log_line         = pyqtSignal(str, str)
    progress_updated = pyqtSignal(int, int)   # (done, total)
    file_downloaded  = pyqtSignal()            # one per completed file (image or video)
    video_downloaded = pyqtSignal()            # one per completed video file (public API — not used internally)
    file_skipped     = pyqtSignal()            # one per skipped/already-exists file
    bytes_received   = pyqtSignal(int)         # bytes for each completed file
    status_changed   = pyqtSignal(str)
    finished         = pyqtSignal()

    def __init__(self, url: str, opts: DownloadOptions, gdl_cmd: str = "gallery-dl"):
        super().__init__()
        self.url         = url
        self.opts        = opts
        self.status      = JobStatus.QUEUED
        self.site        = self._extract_site(url)
        self.files_done  = 0
        self.videos_done = 0
        self.files_skipped = 0

        # FIX #3: use the configured executable, not a hardcoded string
        cmd = [gdl_cmd] + opts.to_argv() + [url]
        self._worker = _Worker(cmd)
        self._thread = QThread()
        self._worker.moveToThread(self._thread)

        self.log_lines: list[tuple[str, str]] = []   # (level, text) — per-job history

        self._thread.started.connect(self._worker.run)
        self._worker.log_line.connect(self._store_log)
        self._worker.log_line.connect(self.log_line)
        self._worker.progress_tick.connect(self.progress_updated)
        self._worker.file_done.connect(self._on_file_done)
        self._worker.video_done.connect(self._on_video_done)
        self._worker.file_skipped.connect(self._on_file_skipped)
        self._worker.bytes_received.connect(self.bytes_received)
        self._worker.finished.connect(self._on_finished)
        # Clean up the worker and thread objects once the thread exits so that
        # cleared/GC'd jobs don't leave dangling QThread instances behind.
        self._thread.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)

    # ── Public ───────────────────────────────────────────────────────────────

    def start(self):
        self._set_status(JobStatus.RUNNING)
        self._thread.start()

    def cancel(self):
        self._worker.cancel()
        self._set_status(JobStatus.CANCELLED)

    # ── Internal ─────────────────────────────────────────────────────────────

    @pyqtSlot(str, str)
    def _store_log(self, level: str, text: str):
        self.log_lines.append((level, text))

    @pyqtSlot()
    def _on_file_done(self):
        self.files_done += 1
        self.file_downloaded.emit()

    @pyqtSlot()
    def _on_video_done(self):
        self.videos_done += 1
        self.video_downloaded.emit()

    @pyqtSlot()
    def _on_file_skipped(self):
        self.files_skipped += 1
        self.file_skipped.emit()

    @pyqtSlot(int)
    def _on_finished(self, code: int):
        if self.status != JobStatus.CANCELLED:
            self._set_status(JobStatus.DONE if code == 0 else JobStatus.ERROR)
        self._thread.quit()
        self.finished.emit()

    def _set_status(self, s: JobStatus):
        self.status = s
        self.status_changed.emit(s.value)

    @staticmethod
    def _extract_site(url: str) -> str:
        """Return a human-readable site name, matching what the download banner shows."""
        match = detect_site(url)
        if match:
            return match.name
        # Fallback: strip www. and TLD from the hostname
        try:
            from urllib.parse import urlparse
            host = urlparse(url).netloc
            parts = host.split(".")
            return parts[-2] if len(parts) >= 2 else host
        except Exception:
            return "Unknown"
