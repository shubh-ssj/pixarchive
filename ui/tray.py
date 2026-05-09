from __future__ import annotations
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from PyQt6.QtGui import QIcon, QPixmap, QColor, QPainter
from PyQt6.QtCore import QObject, QTimer, pyqtSlot, Qt

from core.download_manager import DownloadManager
from core.job import DownloadJob, JobStatus


def _load_icon(active: bool = False) -> QIcon:
    """Load the PixArchive icon from assets. Falls back to a painted placeholder."""
    import sys, os
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS          # type: ignore[attr-defined]
    else:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Prefer ICO for best multi-size support on Windows, fall back to PNG
    for fname in ("icon.ico", "icon.png"):
        path = os.path.join(base, "assets", fname)
        if os.path.exists(path):
            icon = QIcon(path)
            if not icon.isNull():
                return icon

    return _make_painted_icon("#89b4fa" if active else "#a6adc8")


def _make_painted_icon(color: str = "#89b4fa") -> QIcon:
    px = QPixmap(22, 22)
    px.fill(Qt.GlobalColor.transparent)
    p = QPainter(px)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setBrush(QColor(color))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawRoundedRect(2, 2, 18, 18, 4, 4)
    p.setBrush(QColor("#1e1e2e"))
    p.drawRect(9, 4, 4, 8)
    from PyQt6.QtGui import QPolygon
    from PyQt6.QtCore import QPoint
    p.drawPolygon(QPolygon([QPoint(5, 11), QPoint(17, 11), QPoint(11, 17)]))
    p.end()
    return QIcon(px)


class TrayManager(QObject):
    """Manages the system tray icon and sends job-completion notifications."""

    def __init__(self, main_window, manager: DownloadManager):
        super().__init__()
        self._window = main_window
        self._manager = manager
        self._active_count = 0

        if not QSystemTrayIcon.isSystemTrayAvailable():
            self._tray = None
            return

        self._tray = QSystemTrayIcon(self)
        self._tray.setIcon(_load_icon(active=False))
        self._tray.setToolTip("PixArchive")

        menu = QMenu()
        act_show = menu.addAction("Show window")
        act_show.triggered.connect(self._show_window)
        menu.addSeparator()
        act_quit = menu.addAction("Quit")
        act_quit.triggered.connect(QApplication.quit)
        self._tray.setContextMenu(menu)

        self._tray.activated.connect(self._on_tray_activated)
        self._tray.show()

        manager.job_added.connect(self._on_job_added)

        # Batch notification: collect finished jobs for 3 seconds, then summarise
        self._pending_done:  list[DownloadJob] = []
        self._pending_error: list[DownloadJob] = []
        self._batch_timer = QTimer(self)
        self._batch_timer.setSingleShot(True)
        self._batch_timer.setInterval(3000)
        self._batch_timer.timeout.connect(self._flush_notifications)

    @pyqtSlot(object)
    def _on_job_added(self, job: DownloadJob):
        self._active_count += 1
        self._update_icon()
        job.finished.connect(lambda: self._on_job_finished(job))

    def _on_job_finished(self, job: DownloadJob):
        self._active_count = max(0, self._active_count - 1)
        self._update_icon()
        if not self._tray:
            return

        from core.app_settings import get_settings
        s = get_settings()

        if job.status == JobStatus.DONE and s.get("notify_on_complete", True):
            self._pending_done.append(job)
            self._batch_timer.start()   # restart window — more jobs may finish soon

        elif job.status == JobStatus.ERROR and s.get("notify_on_error", True):
            self._pending_error.append(job)
            self._batch_timer.start()

    def _flush_notifications(self):
        """Send one notification summarising all jobs that finished in the last 3 s."""
        if not self._tray:
            return

        from core.app_settings import get_settings
        s = get_settings()

        done_jobs  = self._pending_done[:]
        error_jobs = self._pending_error[:]
        self._pending_done.clear()
        self._pending_error.clear()

        # Decide whether to notify based on window visibility
        # When notify_always is False (default): only notify if window is hidden
        window_hidden = not self._window.isVisible()
        notify_always = s.get("notify_always", False)
        should_notify = notify_always or window_hidden

        if not should_notify:
            return

        if done_jobs:
            total_files  = sum(j.files_done for j in done_jobs)
            total_videos = sum(j.videos_done for j in done_jobs)
            images = total_files - total_videos

            if len(done_jobs) == 1:
                job = done_jobs[0]
                site = job.site or "Unknown"
                title = f"Download complete — {site}"
                parts = []
                img_count = job.files_done - job.videos_done
                if img_count > 0:
                    parts.append(f"{img_count} image{'s' if img_count != 1 else ''}")
                if job.videos_done > 0:
                    parts.append(f"{job.videos_done} video{'s' if job.videos_done != 1 else ''}")
                if job.files_skipped > 0:
                    parts.append(f"{job.files_skipped} skipped")
                body = ", ".join(parts) if parts else "No new files"
            else:
                title = f"{len(done_jobs)} downloads complete"
                parts = []
                if images > 0:
                    parts.append(f"{images} image{'s' if images != 1 else ''}")
                if total_videos > 0:
                    parts.append(f"{total_videos} video{'s' if total_videos != 1 else ''}")
                body = ", ".join(parts) if parts else f"{total_files} files"

            self._tray.showMessage(
                title, body,
                QSystemTrayIcon.MessageIcon.Information, 5000,
            )

        if error_jobs:
            if len(error_jobs) == 1:
                job = error_jobs[0]
                title = "Download failed"
                body  = job.site or job.url[:60]
            else:
                title = f"{len(error_jobs)} downloads failed"
                sites = ", ".join(
                    {j.site for j in error_jobs if j.site} or {j.url[:30] for j in error_jobs}
                )
                body = sites[:80]

            self._tray.showMessage(
                title, body,
                QSystemTrayIcon.MessageIcon.Warning, 5000,
            )

    def _update_icon(self):
        if not self._tray:
            return
        self._tray.setIcon(_load_icon(active=self._active_count > 0))
        suffix = f" ({self._active_count} active)" if self._active_count else ""
        self._tray.setToolTip(f"PixArchive{suffix}")

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self._show_window()

    def _show_window(self):
        from PyQt6.QtCore import Qt
        self._window.show()
        # If the window was minimized, restore it before raising
        if self._window.isMinimized():
            self._window.setWindowState(
                self._window.windowState() & ~Qt.WindowState.WindowMinimized
                | Qt.WindowState.WindowActive
            )
        self._window.raise_()
        self._window.activateWindow()
