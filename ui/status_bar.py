from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QFrame
from PyQt6.QtCore import QTimer

from core.stats import get_stats
from core.app_settings import get_settings


class StatusBar(QWidget):
    """Persistent bottom status bar showing live session stats."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(28)
        self.setObjectName("dialog_footer")   # themed by QSS as bg_mantle + top border
        self._build_ui()

        self._timer = QTimer()
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._refresh)
        self._timer.start()

        stats = get_stats()
        stats.updated.connect(self._refresh)

        # Surface settings save failures as a transient status-bar warning
        get_settings().save_failed.connect(self._on_save_failed)

        self._refresh()

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 0, 14, 0)
        layout.setSpacing(20)

        def stat_pair(label_text: str) -> tuple[QLabel, QLabel]:
            lbl = QLabel(label_text)
            lbl.setStyleSheet("color: palette(mid); font-size:8pt;")
            val = QLabel("—")
            val.setStyleSheet("color: palette(highlight); font-size:8pt; font-weight:bold;")
            layout.addWidget(lbl)
            layout.addWidget(val)
            return lbl, val

        _, self.val_active   = stat_pair("Active jobs:")
        _, self.val_speed    = stat_pair("Speed:")
        _, self.val_files    = stat_pair("Files this session:")
        _, self.val_skipped  = stat_pair("Skipped:")
        _, self.val_done     = stat_pair("Completed jobs:")
        _, self.val_errors   = stat_pair("Errors:")
        _, self.val_elapsed  = stat_pair("Session:")

        layout.addStretch()

        self.ready_lbl = QLabel("Ready")
        self.ready_lbl.setStyleSheet("color: palette(mid); font-size:8pt;")
        layout.addWidget(self.ready_lbl)

    def _refresh(self):
        s = get_stats()
        self.val_active.setText(str(s.active_jobs))
        self.val_active.setStyleSheet(
            "color: palette(highlight); font-size:8pt; font-weight:bold;"
            if s.active_jobs > 0 else
            "color: palette(text); font-size:8pt; font-weight:bold;"
        )
        speed = s.speed_str
        self.val_speed.setText(speed if speed else "—")
        self.val_speed.setStyleSheet(
            "color: palette(highlight); font-size:8pt; font-weight:bold;"
            if speed else
            "color: palette(text); font-size:8pt; font-weight:bold;"
        )
        self.val_files.setText(str(s.files_done))
        self.val_skipped.setText(str(s.files_skipped))
        self.val_done.setText(str(s.jobs_done))
        self.val_errors.setText(str(s.jobs_error))
        self.val_errors.setStyleSheet(
            "color: palette(bright-text); font-size:8pt; font-weight:bold;"
            if s.jobs_error > 0 else
            "color: palette(text); font-size:8pt; font-weight:bold;"
        )
        self.val_elapsed.setText(s.elapsed_str)

        if s.active_jobs > 0:
            self.ready_lbl.setText("Downloading…")
            self.ready_lbl.setStyleSheet("color: palette(highlight); font-size:8pt;")
        else:
            self.ready_lbl.setText("Ready")
            self.ready_lbl.setStyleSheet("color: palette(mid); font-size:8pt;")

    def _on_save_failed(self, error: str):
        """Show a brief warning when settings could not be written to disk."""
        self.ready_lbl.setText(f"⚠ Settings not saved: {error}")
        self.ready_lbl.setStyleSheet(
            "color: palette(bright-text); font-size:8pt; font-weight:bold;"
        )
        # Clear the warning after 6 seconds and let _refresh() restore normal state
        QTimer.singleShot(6000, self._refresh)
