"""
Per-job log viewer dialog.
Shows the full output for a single DownloadJob, with live updates
if the job is still running, and level filter buttons.
"""
from __future__ import annotations
import html as html_mod
from datetime import datetime

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QPlainTextEdit, QWidget, QLineEdit, QApplication
)
from PyQt6.QtCore import Qt, pyqtSlot, QTimer
from PyQt6.QtGui import QFont, QTextCursor

from core.job import DownloadJob, JobStatus


_LEVEL_COLOR = {
    "error":   "color:#f38ba8;",
    "warning": "color:#fab387;",
    "info":    "color:palette(text);",
    "debug":   "color:palette(mid);",
}


class JobLogDialog(QDialog):
    def __init__(self, job: DownloadJob, parent=None):
        super().__init__(parent)
        self.job = job
        self.setWindowTitle(f"Log — {job.site}  {job.url[:60]}{'…' if len(job.url)>60 else ''}")
        self.resize(820, 520)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowMaximizeButtonHint)

        self._active_filters: set[str] = {"error", "warning", "info", "debug"}
        self._rendered_count = 0   # how many job.log_lines we've rendered

        self._build_ui()
        self._render_existing()

        # Live updates if still running
        if job.status == JobStatus.RUNNING:
            job.log_line.connect(self._on_new_line)
            job.status_changed.connect(self._on_status_changed)

        self._update_status_badge()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Header
        header = QWidget()
        header.setObjectName("dialog_header")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(14, 8, 14, 8)
        hl.setSpacing(10)

        site_lbl = QLabel(self.job.site or "url")
        site_lbl.setStyleSheet(
            "background: palette(highlight); color: palette(highlighted-text);"
            "border-radius:4px; padding:1px 8px; font-size:8pt; font-weight:bold;"
        )
        hl.addWidget(site_lbl)

        url_lbl = QLabel(self.job.url)
        url_lbl.setStyleSheet("font-size:9pt; color: palette(mid);")
        url_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        hl.addWidget(url_lbl, stretch=1)

        self.status_badge = QLabel(self.job.status.value)
        self.status_badge.setStyleSheet("border-radius:4px; padding:1px 8px; font-size:8pt; font-weight:bold;")
        hl.addWidget(self.status_badge)

        outer.addWidget(header)

        # Toolbar: level filters + search + copy
        tb_widget = QWidget()
        tb_widget.setObjectName("dialog_header")
        tb = QHBoxLayout(tb_widget)
        tb.setContentsMargins(10, 4, 10, 4)
        tb.setSpacing(6)

        self._filter_btns: dict[str, QPushButton] = {}
        for level, label in [("error","Err"), ("warning","Warn"), ("info","Info"), ("debug","Debug")]:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setChecked(True)
            btn.setFixedHeight(22)
            btn.setStyleSheet("font-size:7pt; padding:0 6px;")
            btn.toggled.connect(lambda checked, l=level: self._toggle_filter(l, checked))
            self._filter_btns[level] = btn
            tb.addWidget(btn)

        tb.addStretch()

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search log…")
        self.search_box.setFixedHeight(24)
        self.search_box.setFixedWidth(180)
        self.search_box.setStyleSheet("font-size:8pt;")
        self.search_box.textChanged.connect(self._rerender)
        tb.addWidget(self.search_box)

        btn_copy = QPushButton("Copy all")
        btn_copy.setFixedHeight(24)
        btn_copy.setStyleSheet("font-size:8pt; padding:0 8px;")
        btn_copy.clicked.connect(self._copy_all)
        tb.addWidget(btn_copy)

        outer.addWidget(tb_widget)

        # Log output
        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setObjectName("log_output")
        self.log_view.setFont(QFont("Consolas", 9))
        self.log_view.setMaximumBlockCount(10000)
        outer.addWidget(self.log_view, stretch=1)

        # Footer
        footer = QWidget()
        footer.setObjectName("dialog_footer")
        fl = QHBoxLayout(footer)
        fl.setContentsMargins(14, 8, 14, 8)

        self.files_lbl = QLabel(f"Files downloaded: {self.job.files_done}")
        self.files_lbl.setStyleSheet("color: palette(mid); font-size:8pt;")
        fl.addWidget(self.files_lbl)

        fl.addStretch()

        btn_close = QPushButton("Close")
        btn_close.setFixedWidth(80)
        btn_close.clicked.connect(self.accept)
        fl.addWidget(btn_close)

        outer.addWidget(footer)

    def _render_existing(self):
        """Render all lines already stored on the job."""
        for level, text in self.job.log_lines:
            self._render_line(level, text)
        self._rendered_count = len(self.job.log_lines)
        self.log_view.moveCursor(QTextCursor.MoveOperation.End)

    def _render_line(self, level: str, text: str):
        if level not in self._active_filters:
            return
        query = self.search_box.text().strip().lower()
        if query and query not in text.lower():
            return
        color = _LEVEL_COLOR.get(level, "color:palette(text);")
        ts = datetime.now().strftime("%H:%M:%S")
        entry = (
            f'<span style="color:palette(mid); font-size:8pt;">[{ts}]</span> '
            f'<span style="{color}">{html_mod.escape(text)}</span>'
        )
        self.log_view.appendHtml(entry)

    def _rerender(self):
        """Re-render everything when filter or search changes."""
        self.log_view.clear()
        for level, text in self.job.log_lines:
            self._render_line(level, text)
        self.log_view.moveCursor(QTextCursor.MoveOperation.End)

    def _toggle_filter(self, level: str, checked: bool):
        if checked:
            self._active_filters.add(level)
        else:
            self._active_filters.discard(level)
        self._rerender()

    @pyqtSlot(str, str)
    def _on_new_line(self, level: str, text: str):
        """Called live while job is running."""
        self._render_line(level, text)
        self.log_view.moveCursor(QTextCursor.MoveOperation.End)
        self.files_lbl.setText(f"Files downloaded: {self.job.files_done}")

    @pyqtSlot(str)
    def _on_status_changed(self, status: str):
        self._update_status_badge()
        self.files_lbl.setText(f"Files downloaded: {self.job.files_done}")

    def _update_status_badge(self):
        STATUS_QSS = {
            JobStatus.QUEUED:    "background: palette(midlight); color: palette(text);",
            JobStatus.RUNNING:   "background: palette(highlight); color: palette(highlighted-text);",
            JobStatus.DONE:      "background: palette(shadow); color: palette(highlighted-text);",
            JobStatus.ERROR:     "background: palette(bright-text); color: palette(base);",
            JobStatus.CANCELLED: "background: palette(shadow); color: palette(mid);",
        }
        qss = STATUS_QSS.get(self.job.status, "")
        self.status_badge.setText(self.job.status.value)
        self.status_badge.setStyleSheet(
            f"{qss} border-radius:4px; padding:1px 8px; font-size:8pt; font-weight:bold;"
        )

    def _copy_all(self):
        lines = [f"[{l}] {t}" for l, t in self.job.log_lines]
        QApplication.clipboard().setText("\n".join(lines))
