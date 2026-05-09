"""
Scheduler: run queued downloads at a specified time, optionally repeating.

Scheduled jobs are persisted to ~/.pixarchive/schedule.json.
The Scheduler polls once per minute via a QTimer.
"""
from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from typing import Optional

from PyQt6.QtCore import QObject, QTimer, pyqtSignal

from core.options import DownloadOptions

SCHEDULE_PATH = os.path.join(os.path.expanduser("~"), ".pixarchive", "schedule.json")

# Repeat interval options exposed to the UI
REPEAT_OPTIONS: list[tuple[str, Optional[int]]] = [
    ("Once",        None),
    ("Every hour",  60),
    ("Every 6 h",   360),
    ("Every 12 h",  720),
    ("Daily",       1440),
    ("Weekly",      10080),
]


@dataclass
class ScheduledJob:
    id:              str
    url:             str
    opts:            dict                  # DownloadOptions as plain dict
    next_run:        str                   # ISO-8601 datetime string
    repeat_minutes:  Optional[int] = None  # None = run once
    label:           str = ""             # optional human-readable name
    enabled:         bool = True

    # ── Helpers ──────────────────────────────────────────────────────────────

    def next_run_dt(self) -> datetime:
        return datetime.fromisoformat(self.next_run)

    def is_due(self) -> bool:
        return self.enabled and datetime.now() >= self.next_run_dt()

    def advance(self):
        """Move next_run forward by repeat_minutes, or disable if one-shot."""
        if self.repeat_minutes:
            nxt = self.next_run_dt() + timedelta(minutes=self.repeat_minutes)
            # If we've drifted (e.g. app was closed), skip to the next future slot
            now = datetime.now()
            while nxt <= now:
                nxt += timedelta(minutes=self.repeat_minutes)
            self.next_run = nxt.isoformat(timespec="seconds")
        else:
            self.enabled = False

    def display_next(self) -> str:
        if not self.enabled:
            return "Done"
        dt = self.next_run_dt()
        now = datetime.now()
        diff = dt - now
        if diff.total_seconds() < 0:
            return "Overdue"
        total_mins = int(diff.total_seconds() // 60)
        if total_mins < 60:
            return f"in {total_mins}m  ({dt.strftime('%H:%M')})"
        if total_mins < 1440:
            h, m = divmod(total_mins, 60)
            return f"in {h}h {m}m  ({dt.strftime('%H:%M')})"
        days = total_mins // 1440
        return f"in {days}d  ({dt.strftime('%a %H:%M')})"

    def repeat_label(self) -> str:
        for label, mins in REPEAT_OPTIONS:
            if mins == self.repeat_minutes:
                return label
        if self.repeat_minutes:
            return f"Every {self.repeat_minutes}m"
        return "Once"

    def to_download_options(self) -> DownloadOptions:
        from dataclasses import fields as dc_fields
        valid = {f.name for f in dc_fields(DownloadOptions)}
        filtered = {k: v for k, v in self.opts.items() if k in valid}
        return DownloadOptions(**filtered)


def _new_id() -> str:
    return uuid.uuid4().hex[:12]


def _load_jobs() -> list[ScheduledJob]:
    if not os.path.exists(SCHEDULE_PATH):
        return []
    try:
        with open(SCHEDULE_PATH, encoding="utf-8") as f:
            raw = json.load(f)
        return [ScheduledJob(**r) for r in raw]
    except Exception:
        return []


def _save_jobs(jobs: list[ScheduledJob]):
    os.makedirs(os.path.dirname(SCHEDULE_PATH), exist_ok=True)
    with open(SCHEDULE_PATH, "w", encoding="utf-8") as f:
        json.dump([asdict(j) for j in jobs], f, indent=2)


class Scheduler(QObject):
    """Holds scheduled jobs and fires them when due.

    Emits job_triggered(url, opts) — the MainWindow connects this to
    DownloadManager.enqueue().
    """

    job_triggered = pyqtSignal(str, object)   # (url, DownloadOptions)
    jobs_changed  = pyqtSignal()              # any mutation to the job list

    _TICK_MS = 60_000   # check every minute

    def __init__(self, parent=None):
        super().__init__(parent)
        self._jobs: list[ScheduledJob] = _load_jobs()
        self._timer = QTimer(self)
        self._timer.setInterval(self._TICK_MS)
        self._timer.timeout.connect(self._tick)
        self._timer.start()

    # ── Public API ────────────────────────────────────────────────────────────

    @property
    def jobs(self) -> list[ScheduledJob]:
        return list(self._jobs)

    def add(self, url: str, opts: DownloadOptions, next_run: datetime,
            repeat_minutes: Optional[int] = None, label: str = "") -> ScheduledJob:
        job = ScheduledJob(
            id=_new_id(),
            url=url,
            opts=asdict(opts),
            next_run=next_run.isoformat(timespec="seconds"),
            repeat_minutes=repeat_minutes,
            label=label or url[:60],
            enabled=True,
        )
        self._jobs.append(job)
        self._persist()
        self.jobs_changed.emit()
        return job

    def update(self, job: ScheduledJob):
        for i, j in enumerate(self._jobs):
            if j.id == job.id:
                self._jobs[i] = job
                break
        self._persist()
        self.jobs_changed.emit()

    def remove(self, job_id: str):
        self._jobs = [j for j in self._jobs if j.id != job_id]
        self._persist()
        self.jobs_changed.emit()

    def toggle_enabled(self, job_id: str):
        for job in self._jobs:
            if job.id == job_id:
                job.enabled = not job.enabled
                break
        self._persist()
        self.jobs_changed.emit()

    # ── Internal ─────────────────────────────────────────────────────────────

    def _tick(self):
        fired = False
        for job in self._jobs:
            if job.is_due():
                self.job_triggered.emit(job.url, job.to_download_options())
                job.advance()
                fired = True
        if fired:
            self._persist()
            self.jobs_changed.emit()

    def _persist(self):
        try:
            _save_jobs(self._jobs)
        except Exception:
            pass
