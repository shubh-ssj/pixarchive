from __future__ import annotations
import time
import os

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QProgressBar, QPushButton, QScrollArea, QFrame, QSizePolicy,
    QMenu, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSlot, pyqtSignal
from PyQt6.QtGui import QAction

from core.download_manager import DownloadManager
from core.job import DownloadJob, JobStatus


class JobCard(QFrame):
    retry_requested = pyqtSignal(object)   # emits the original DownloadJob

    def __init__(self, job: DownloadJob, parent=None):
        super().__init__(parent)
        self.job = job
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self._start_time: float | None = None
        self._last_total: int = 0
        self._build_ui()
        self._connect_signals()
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        # Top row
        top = QHBoxLayout()
        top.setSpacing(8)

        self.site_badge = QLabel(self.job.site or "url")
        self.site_badge.setStyleSheet(
            "background: palette(shadow); color: palette(link);"
            "border-radius:4px; padding:1px 7px; font-size:8pt; font-weight:bold; border-left: 2px solid palette(link);"
        )
        top.addWidget(self.site_badge)

        self.url_label = QLabel(self.job.url)
        self.url_label.setStyleSheet("color: palette(mid); font-size:9pt;")
        self.url_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.url_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.url_label.setWordWrap(False)
        top.addWidget(self.url_label, stretch=1)

        self.status_label = QLabel(self.job.status.value)
        top.addWidget(self.status_label)
        self._update_status_badge()

        layout.addLayout(top)

        # Progress bar
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setFixedHeight(5)
        self.progress.setTextVisible(False)
        layout.addWidget(self.progress)

        # Bottom row
        bottom = QHBoxLayout()
        bottom.setSpacing(12)

        self.files_label = QLabel("—")
        self.files_label.setStyleSheet("color: palette(mid); font-size:8pt;")
        bottom.addWidget(self.files_label)

        log_hint = QLabel("double-click for log")
        log_hint.setStyleSheet("color: palette(shadow); font-size:7pt; font-style:italic;")
        bottom.addWidget(log_hint)

        self.eta_label = QLabel("")
        self.eta_label.setStyleSheet("color: palette(mid); font-size:8pt;")
        bottom.addWidget(self.eta_label)

        bottom.addStretch()

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setObjectName("btn_stop")
        self.btn_cancel.setFixedHeight(22)
        self.btn_cancel.setStyleSheet("font-size:8pt; padding:0 8px;")
        bottom.addWidget(self.btn_cancel)

        layout.addLayout(bottom)

    def _connect_signals(self):
        self.job.progress_updated.connect(self._on_progress)
        self.job.file_downloaded.connect(self._on_file_downloaded)
        self.job.video_downloaded.connect(self._on_file_downloaded)
        self.job.file_skipped.connect(self._on_file_downloaded)   # skipped also refreshes label
        self.job.status_changed.connect(self._on_status_changed)
        self.btn_cancel.clicked.connect(self._on_cancel_clicked)

    def mouseDoubleClickEvent(self, event):
        self._open_log()
        super().mouseDoubleClickEvent(event)

    def _open_log(self):
        from ui.dialogs.job_log_dialog import JobLogDialog
        dlg = JobLogDialog(self.job, self)
        dlg.exec()

    def _on_cancel_clicked(self):
        from core.app_settings import get_settings
        if get_settings().get("confirm_before_stop", True):
            resp = QMessageBox.question(
                self, "Cancel download",
                f"Cancel this download?\n{self.job.url[:80]}",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if resp != QMessageBox.StandardButton.Yes:
                return
        self.job.cancel()

    def _show_context_menu(self, pos):
        menu = QMenu(self)

        terminal = self.job.status in (JobStatus.DONE, JobStatus.ERROR, JobStatus.CANCELLED)
        running  = self.job.status == JobStatus.RUNNING
        queued   = self.job.status == JobStatus.QUEUED

        # View log
        act_log = QAction("View log…", self)
        act_log.triggered.connect(self._open_log)
        menu.addAction(act_log)

        menu.addSeparator()

        # Copy URL
        act_copy = QAction("Copy URL", self)
        act_copy.triggered.connect(lambda: self._copy_url())
        menu.addAction(act_copy)

        menu.addSeparator()

        # Open output folder
        act_folder = QAction("Open output folder", self)
        out = self.job.opts.output_dir or ""
        act_folder.setEnabled(bool(out and os.path.isdir(out)))
        act_folder.triggered.connect(lambda: self._open_folder(out))
        menu.addAction(act_folder)

        menu.addSeparator()

        # Retry (only for failed/cancelled)
        act_retry = QAction("Retry", self)
        act_retry.setEnabled(self.job.status in (JobStatus.ERROR, JobStatus.CANCELLED))
        act_retry.triggered.connect(lambda: self.retry_requested.emit(self.job))
        menu.addAction(act_retry)

        # Cancel (only if active)
        act_cancel = QAction("Cancel", self)
        act_cancel.setEnabled(running or queued)
        act_cancel.triggered.connect(self._on_cancel_clicked)
        menu.addAction(act_cancel)

        menu.exec(self.mapToGlobal(pos))

    def _copy_url(self):
        from PyQt6.QtWidgets import QApplication
        QApplication.clipboard().setText(self.job.url)

    def _open_folder(self, path: str):
        import sys, subprocess
        if os.name == "nt":
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])

    def _format_file_counts(self, done: int) -> str:
        """Return a file count string, splitting images/videos and noting skipped files."""
        videos = self.job.videos_done
        images = done - videos
        if videos > 0 and images > 0:
            base = f"{images} image{'s' if images != 1 else ''}, {videos} video{'s' if videos != 1 else ''}"
        elif videos > 0:
            base = f"{videos} video{'s' if videos != 1 else ''}"
        else:
            base = f"{done} file{'s' if done != 1 else ''}"
        skipped = self.job.files_skipped
        if skipped > 0:
            base += f"  ({skipped} skipped)"
        return base

    @pyqtSlot()
    def _on_file_downloaded(self):
        """Refresh the files label on every completed file so the split stays live."""
        done = self.job.files_done
        total_label = f" / {self._last_total}" if getattr(self, "_last_total", 0) > 0 else ""
        self.files_label.setText(self._format_file_counts(done) + total_label)

    @pyqtSlot(int, int)
    def _on_progress(self, done: int, total: int):
        if self._start_time is None:
            self._start_time = time.monotonic()
        self._last_total = total
        if total > 0:
            self.progress.setValue(int(done / total * 100))
            self.files_label.setText(self._format_file_counts(done) + f" / {total}")
            elapsed = time.monotonic() - self._start_time
            if done > 0 and elapsed > 1:
                rate = done / elapsed
                remaining = total - done
                eta_secs = int(remaining / rate) if rate > 0 else 0
                if eta_secs < 60:
                    eta_str = f"ETA {eta_secs}s"
                else:
                    eta_str = f"ETA {eta_secs // 60}m {eta_secs % 60}s"
                self.eta_label.setText(eta_str)
            else:
                self.eta_label.setText("")
        else:
            self.files_label.setText(self._format_file_counts(done))
            self.eta_label.setText("")

    @pyqtSlot(str)
    def _on_status_changed(self, status_str: str):
        self.status_label.setText(status_str)
        self._update_status_badge()
        if status_str in ("done", "error", "cancelled"):
            self.btn_cancel.setEnabled(False)
            self.eta_label.setText("")
            if status_str == "done":
                self.progress.setValue(100)
                # Show final split counts on completion
                done = self.job.files_done
                if done > 0:
                    self.files_label.setText(self._format_file_counts(done))

    def _update_status_badge(self):
        STATUS_QSS = {
            JobStatus.QUEUED:    "background: palette(midlight); color: palette(text);",
            JobStatus.RUNNING:   "background: palette(highlight); color: palette(highlighted-text);",
            JobStatus.DONE:      "background: palette(shadow); color: palette(highlighted-text);",
            JobStatus.ERROR:     "background: palette(bright-text); color: palette(base);",
            JobStatus.CANCELLED: "background: palette(shadow); color: palette(mid);",
        }
        qss = STATUS_QSS.get(self.job.status, "background: palette(mid); color: palette(window-text);")
        self.status_label.setStyleSheet(
            f"{qss} border-radius:4px; padding:1px 7px; font-size:8pt; font-weight:bold;"
        )


class QueuePanel(QWidget):
    def __init__(self, manager: DownloadManager):
        super().__init__()
        self.manager = manager
        self._cards: list[JobCard] = []
        self._build_ui()
        self.manager.job_added.connect(self._add_card)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Toolbar
        toolbar = QWidget()
        toolbar.setObjectName("dialog_header")
        tb = QHBoxLayout(toolbar)
        tb.setContentsMargins(12, 8, 12, 8)
        tb.setSpacing(8)

        title = QLabel("Download queue")
        title.setStyleSheet("font-weight:bold; font-size:11pt; color: palette(link);")
        tb.addWidget(title)

        self.count_label = QLabel("")
        self.count_label.setStyleSheet("color: palette(mid); font-size:9pt;")
        tb.addWidget(self.count_label)

        tb.addStretch()

        btn_clear = QPushButton("Clear finished")
        btn_clear.setFixedHeight(28)
        btn_clear.clicked.connect(self._clear_finished)
        tb.addWidget(btn_clear)

        btn_start = QPushButton("Start all")
        btn_start.setObjectName("btn_download")
        btn_start.setFixedHeight(28)
        btn_start.clicked.connect(self.manager.start_queued)
        tb.addWidget(btn_start)

        layout.addWidget(toolbar)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        self.card_container = QWidget()
        self.cards_layout = QVBoxLayout(self.card_container)
        self.cards_layout.setContentsMargins(12, 12, 12, 12)
        self.cards_layout.setSpacing(8)
        self.cards_layout.addStretch()

        scroll.setWidget(self.card_container)
        layout.addWidget(scroll, stretch=1)

        self.empty_label = QLabel("No downloads queued yet.\nPaste a URL in the Download tab.")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet("color: palette(mid); font-size:10pt;")
        layout.addWidget(self.empty_label)
        self.empty_label.setVisible(True)
        scroll.setVisible(False)
        self._scroll = scroll

    @pyqtSlot(object)
    def _add_card(self, job: DownloadJob):
        card = JobCard(job)
        card.retry_requested.connect(self._on_retry)
        job.status_changed.connect(lambda _: self._update_count())
        self._cards.append(card)
        self.cards_layout.insertWidget(self.cards_layout.count() - 1, card)
        self.empty_label.setVisible(False)
        self._scroll.setVisible(True)
        self._update_count()

    def _on_retry(self, job: DownloadJob):
        """Re-enqueue a failed/cancelled job with the same URL and options."""
        self.manager.enqueue(job.url, job.opts)

    def _update_count(self):
        running  = sum(1 for c in self._cards if c.job.status == JobStatus.RUNNING)
        queued   = sum(1 for c in self._cards if c.job.status == JobStatus.QUEUED)
        total    = len(self._cards)
        parts = []
        if running:
            parts.append(f"{running} running")
        if queued:
            parts.append(f"{queued} queued")
        if total:
            parts.append(f"{total} total")
        self.count_label.setText("  ·  ".join(parts))

        # Update window title with active count
        try:
            win = self.window()
            if running > 0:
                win.setWindowTitle(f"PixArchive  ({running} active)")
            else:
                win.setWindowTitle("PixArchive")
        except Exception:
            pass

    def _clear_finished(self):
        terminal = {JobStatus.DONE, JobStatus.ERROR, JobStatus.CANCELLED}
        for i in reversed(range(self.cards_layout.count())):
            item = self.cards_layout.itemAt(i)
            if item and isinstance(item.widget(), JobCard):
                card = item.widget()
                if card.job.status in terminal:
                    if card in self._cards:
                        self._cards.remove(card)
                    card.deleteLater()
                    self.cards_layout.removeItem(item)
        self.manager.clear_finished()
        has_cards = bool(self._cards)
        self.empty_label.setVisible(not has_cards)
        self._scroll.setVisible(has_cards)
        self._update_count()
