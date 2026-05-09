"""
Scheduler panel — view, add, edit, and delete scheduled downloads.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QDialog, QFormLayout, QLineEdit, QComboBox, QDateTimeEdit,
    QCheckBox, QDialogButtonBox, QMessageBox, QFrame, QSizePolicy,
)
from PyQt6.QtCore import Qt, pyqtSlot, QDateTime, QDate, QTime
from PyQt6.QtGui import QColor

from core.scheduler import Scheduler, ScheduledJob, REPEAT_OPTIONS, _new_id
from core.options import DownloadOptions
from core import presets as preset_mgr


# ── Add / Edit dialog ─────────────────────────────────────────────────────────

class ScheduleDialog(QDialog):
    """Dialog for creating or editing a scheduled job."""

    def __init__(self, scheduler: Scheduler, job: Optional[ScheduledJob] = None,
                 prefill_url: str = "", parent=None):
        super().__init__(parent)
        self.scheduler = scheduler
        self.job = job
        self.setWindowTitle("Edit scheduled download" if job else "Schedule a download")
        self.setMinimumWidth(460)
        self._build_ui(prefill_url)

    def _build_ui(self, prefill_url: str):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        form = QFormLayout()
        form.setVerticalSpacing(10)
        form.setHorizontalSpacing(14)

        # URL
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("https://…")
        if self.job:
            self.url_edit.setText(self.job.url)
        elif prefill_url:
            self.url_edit.setText(prefill_url)
        form.addRow("URL", self.url_edit)

        # Label
        self.label_edit = QLineEdit()
        self.label_edit.setPlaceholderText("Optional name for this job")
        if self.job:
            self.label_edit.setText(self.job.label)
        form.addRow("Label", self.label_edit)

        # Preset
        self.preset_combo = QComboBox()
        self.preset_combo.addItem("— no preset —")
        for name in preset_mgr.list_presets():
            self.preset_combo.addItem(name)
        form.addRow("Preset", self.preset_combo)

        # Run at
        self.dt_edit = QDateTimeEdit()
        self.dt_edit.setCalendarPopup(True)
        self.dt_edit.setDisplayFormat("yyyy-MM-dd  HH:mm")
        # Only block past times for new jobs; editing an existing job
        # may legitimately need to show a past next_run time.
        if not self.job:
            self.dt_edit.setMinimumDateTime(QDateTime.currentDateTime())
        if self.job:
            dt = self.job.next_run_dt()
            self.dt_edit.setDateTime(QDateTime(
                QDate(dt.year, dt.month, dt.day),
                QTime(dt.hour, dt.minute)
            ))
        else:
            # Default: next round hour
            nxt = datetime.now().replace(second=0, microsecond=0) + timedelta(hours=1)
            nxt = nxt.replace(minute=0)
            self.dt_edit.setDateTime(QDateTime(
                QDate(nxt.year, nxt.month, nxt.day),
                QTime(nxt.hour, nxt.minute)
            ))
        form.addRow("Run at", self.dt_edit)

        # Repeat
        self.repeat_combo = QComboBox()
        for label, _ in REPEAT_OPTIONS:
            self.repeat_combo.addItem(label)
        if self.job and self.job.repeat_minutes is not None:
            for i, (_, mins) in enumerate(REPEAT_OPTIONS):
                if mins == self.job.repeat_minutes:
                    self.repeat_combo.setCurrentIndex(i)
                    break
        form.addRow("Repeat", self.repeat_combo)

        # Enabled
        self.enabled_check = QCheckBox("Enabled")
        self.enabled_check.setChecked(self.job.enabled if self.job else True)
        form.addRow("", self.enabled_check)

        layout.addLayout(form)

        # Buttons
        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self._accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _accept(self):
        url = self.url_edit.text().strip()
        if not url.startswith(("http://", "https://")):
            QMessageBox.warning(self, "Invalid URL", "Please enter a valid http(s) URL.")
            return

        qdt  = self.dt_edit.dateTime().toPyDateTime()
        _, repeat_mins = REPEAT_OPTIONS[self.repeat_combo.currentIndex()]
        label = self.label_edit.text().strip()

        # Build options from selected preset (or defaults)
        preset_name = self.preset_combo.currentText()
        if preset_name.startswith("—"):
            opts = DownloadOptions()
        else:
            opts = preset_mgr.load_preset(preset_name) or DownloadOptions()

        if self.job:
            from dataclasses import asdict
            self.job.url            = url
            self.job.label          = label or url[:60]
            self.job.opts           = asdict(opts)
            self.job.next_run       = qdt.isoformat(timespec="seconds")
            self.job.repeat_minutes = repeat_mins
            self.job.enabled        = self.enabled_check.isChecked()
            self.scheduler.update(self.job)
        else:
            self.scheduler.add(url, opts, qdt, repeat_mins, label)

        self.accept()


# ── Scheduler panel ───────────────────────────────────────────────────────────

class SchedulerPanel(QWidget):
    """Main scheduler panel shown in the nav sidebar."""

    def __init__(self, scheduler: Scheduler):
        super().__init__()
        self.scheduler = scheduler
        self._build_ui()
        self._connect_signals()
        self._refresh()

    # ── UI ────────────────────────────────────────────────────────────────────

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

        title = QLabel("Scheduled downloads")
        title.setStyleSheet("font-weight:bold; font-size:11pt; color: palette(link);")
        tb.addWidget(title)

        tb.addStretch()

        self.btn_add = QPushButton("+ Add")
        self.btn_add.setObjectName("btn_download")
        self.btn_add.setFixedHeight(28)
        self.btn_add.clicked.connect(self._on_add)
        tb.addWidget(self.btn_add)

        self.btn_edit = QPushButton("Edit")
        self.btn_edit.setFixedHeight(28)
        self.btn_edit.setEnabled(False)
        self.btn_edit.clicked.connect(self._on_edit)
        tb.addWidget(self.btn_edit)

        self.btn_toggle = QPushButton("Enable / Disable")
        self.btn_toggle.setFixedHeight(28)
        self.btn_toggle.setEnabled(False)
        self.btn_toggle.clicked.connect(self._on_toggle)
        tb.addWidget(self.btn_toggle)

        self.btn_delete = QPushButton("Delete")
        self.btn_delete.setObjectName("btn_stop")
        self.btn_delete.setFixedHeight(28)
        self.btn_delete.setEnabled(False)
        self.btn_delete.clicked.connect(self._on_delete)
        tb.addWidget(self.btn_delete)

        layout.addWidget(toolbar)

        # Table
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Label / URL", "Next run", "Repeat", "Enabled", "ID"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setColumnHidden(4, True)   # ID hidden, used for lookups
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setFrameShape(QFrame.Shape.NoFrame)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        self.table.doubleClicked.connect(self._on_edit)
        layout.addWidget(self.table, stretch=1)

        # Empty state
        self.empty_label = QLabel(
            "No scheduled downloads.\n\nClick  + Add  to schedule a URL to download automatically."
        )
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet("color: palette(mid); font-size:10pt;")
        layout.addWidget(self.empty_label)

        # Hint bar
        hint = QWidget()
        hint.setObjectName("dialog_header")
        hl = QHBoxLayout(hint)
        hl.setContentsMargins(12, 6, 12, 6)
        hint_lbl = QLabel(
            "Scheduled jobs fire within one minute of their due time. "
            "The app must be running for jobs to trigger."
        )
        hint_lbl.setStyleSheet("color: palette(mid); font-size:8pt;")
        hl.addWidget(hint_lbl)
        layout.addWidget(hint)

    def _connect_signals(self):
        self.scheduler.jobs_changed.connect(self._refresh)

    # ── Slots ─────────────────────────────────────────────────────────────────

    @pyqtSlot()
    def _refresh(self):
        jobs = self.scheduler.jobs
        self.table.setRowCount(0)

        for job in jobs:
            row = self.table.rowCount()
            self.table.insertRow(row)

            # Label / URL
            display = job.label if job.label else job.url
            lbl_item = QTableWidgetItem(display)
            lbl_item.setToolTip(job.url)
            self.table.setItem(row, 0, lbl_item)

            # Next run
            next_item = QTableWidgetItem(job.display_next())
            next_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 1, next_item)

            # Repeat
            rep_item = QTableWidgetItem(job.repeat_label())
            rep_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 2, rep_item)

            # Enabled
            enabled_item = QTableWidgetItem("✓" if job.enabled else "✗")
            enabled_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if not job.enabled:
                enabled_item.setForeground(QColor("gray"))
            self.table.setItem(row, 3, enabled_item)

            # Hidden ID
            self.table.setItem(row, 4, QTableWidgetItem(job.id))

            # Dim entire row if disabled
            if not job.enabled:
                for col in range(4):
                    item = self.table.item(row, col)
                    if item:
                        item.setForeground(QColor("gray"))

        has_jobs = bool(jobs)
        self.table.setVisible(has_jobs)
        self.empty_label.setVisible(not has_jobs)
        self._on_selection_changed()

    @pyqtSlot()
    def _on_selection_changed(self):
        has_sel = bool(self.table.selectedItems())
        self.btn_edit.setEnabled(has_sel)
        self.btn_toggle.setEnabled(has_sel)
        self.btn_delete.setEnabled(has_sel)

    def _selected_job(self) -> Optional[ScheduledJob]:
        rows = self.table.selectedItems()
        if not rows:
            return None
        row = self.table.currentRow()
        job_id = self.table.item(row, 4)
        if not job_id:
            return None
        for job in self.scheduler.jobs:
            if job.id == job_id.text():
                return job
        return None

    @pyqtSlot()
    def _on_add(self):
        dlg = ScheduleDialog(self.scheduler, parent=self)
        dlg.exec()

    @pyqtSlot()
    def _on_edit(self):
        job = self._selected_job()
        if job:
            dlg = ScheduleDialog(self.scheduler, job=job, parent=self)
            dlg.exec()

    @pyqtSlot()
    def _on_toggle(self):
        job = self._selected_job()
        if job:
            self.scheduler.toggle_enabled(job.id)

    @pyqtSlot()
    def _on_delete(self):
        job = self._selected_job()
        if not job:
            return
        resp = QMessageBox.question(
            self, "Delete scheduled job",
            f"Delete this scheduled download?\n\n{job.label or job.url[:80]}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if resp == QMessageBox.StandardButton.Yes:
            self.scheduler.remove(job.id)

    def schedule_url(self, url: str):
        """Open the add dialog pre-filled with a URL (called from download panel)."""
        dlg = ScheduleDialog(self.scheduler, prefill_url=url, parent=self)
        dlg.exec()
