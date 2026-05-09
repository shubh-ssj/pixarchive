from __future__ import annotations

from PyQt6.QtCore import QObject, pyqtSignal

from core.job import DownloadJob, JobStatus
from core.options import DownloadOptions


class DownloadManager(QObject):
    """
    Manages the full list of DownloadJobs and respects a concurrency limit.

    - start()         → create + immediately start a job (bypasses queue limit)
    - enqueue()       → add to queue; auto-starts if a slot is free
    - start_queued()  → start as many queued jobs as slots allow
    """

    job_added = pyqtSignal(object)   # DownloadJob

    def __init__(self):
        super().__init__()
        self._jobs: list[DownloadJob] = []
        self._max_concurrent: int = 1
        self._gdl_cmd: str = "gallery-dl"
        self._auto_start: bool = False

    # ── Settings integration ──────────────────────────────────────────────────

    def set_max_concurrent(self, n: int):
        self._max_concurrent = max(1, n)

    def set_gdl_cmd(self, cmd: str):
        self._gdl_cmd = cmd.strip() or "gallery-dl"

    def set_auto_start(self, enabled: bool):
        """When True, enqueue() immediately starts jobs up to the concurrency limit."""
        self._auto_start = enabled

    # ── Public API ───────────────────────────────────────────────────────────

    def start(self, url: str, opts: DownloadOptions) -> DownloadJob:
        """Create and immediately start a job (ignores concurrency limit)."""
        job = self._make_job(url, opts)
        job.start()
        return job

    def enqueue(self, url: str, opts: DownloadOptions) -> DownloadJob:
        """Add a job to the queue.

        With auto_start on:  start immediately if a concurrency slot is free,
                             otherwise leave as QUEUED (start_queued() will pick it up).
        With auto_start off: always leave as QUEUED; user must press Start all.
        """
        job = self._make_job(url, opts)
        if self._auto_start and self._running_count() < self._max_concurrent:
            job.start()
        return job

    def start_queued(self):
        """Start queued jobs up to the concurrency limit."""
        for job in self._jobs:
            if job.status == JobStatus.QUEUED:
                if self._running_count() >= self._max_concurrent:
                    break
                job.start()

    def stop_active(self):
        """Cancel the most recently started running job."""
        for job in reversed(self._jobs):
            if job.status == JobStatus.RUNNING:
                job.cancel()
                break

    def stop_all(self):
        for job in self._jobs:
            if job.status == JobStatus.RUNNING:
                job.cancel()

    def clear_finished(self):
        terminal = {JobStatus.DONE, JobStatus.ERROR, JobStatus.CANCELLED}
        self._jobs = [j for j in self._jobs if j.status not in terminal]

    @property
    def jobs(self) -> list[DownloadJob]:
        return list(self._jobs)

    # ── Internal ─────────────────────────────────────────────────────────────

    def _make_job(self, url: str, opts: DownloadOptions) -> DownloadJob:
        # Apply per-site overrides before creating the job
        from core.url_detector import detect_site
        from core.site_overrides import apply_to_options
        match = detect_site(url)
        opts = apply_to_options(match.name if match else None, opts)
        job = DownloadJob(url, opts, gdl_cmd=self._gdl_cmd)
        self._jobs.append(job)
        self.job_added.emit(job)
        job.finished.connect(lambda: self._on_job_finished(job))
        from core.stats import get_stats
        stats = get_stats()
        job.file_downloaded.connect(stats.record_file)
        job.file_skipped.connect(stats.record_skip)
        job.bytes_received.connect(stats.record_bytes)
        job.status_changed.connect(lambda s, _stats=stats, _job=job: (
            _stats.record_job_started()   if s == "running"   else
            _stats.record_job_done()      if s == "done"      else
            _stats.record_job_error()     if s == "error"     else
            _stats.record_job_cancelled() if s == "cancelled" else
            None
        ))
        # Clear speed display when the last job finishes
        job.finished.connect(lambda _s=stats: _s.clear_speed() if _s.active_jobs == 0 else None)
        return job

    def _on_job_finished(self, finished_job: DownloadJob):
        """After any job completes, fill free slots from the queue."""
        self.start_queued()

    def _running_count(self) -> int:
        return sum(1 for j in self._jobs if j.status == JobStatus.RUNNING)
