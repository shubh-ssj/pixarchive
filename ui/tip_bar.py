"""
TipBar — a dismissible banner shown once per app version to highlight
features the user might not have discovered yet.

Shown at the top of the main content area, dismissed by clicking ✕ or
clicking a feature link. Records dismissal in settings so it only appears once.
"""
from __future__ import annotations

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import pyqtSignal, Qt

from core.app_settings import get_settings

# Reads the app version from QApplication at runtime — no hardcoded duplicate.
def _current_app_version() -> str:
    from PyQt6.QtWidgets import QApplication
    app = QApplication.instance()
    return app.applicationVersion() if app else "0.0.0"

# Tips to show — each is (icon, text, optional nav index to jump to)
# nav_index matches NAV_ITEMS order in main_window.py:
#   0=Download, 1=Queue, 2=History, 3=Scheduler, 4=Sites, 5=Config, 6=Accounts
_TIPS: list[tuple[str, str, int | None]] = [
    ("⏱", "New: Schedule downloads to run automatically — try the Scheduler tab.", 3),
    ("◈", "New: Set per-site defaults (cookies, filename, folder) in Config → Per-site Overrides.", 5),
    ("📦", "New: Back up your presets & settings via File → Export config bundle.", None),
]


class TipBar(QWidget):
    """Dismissible feature tip banner."""

    nav_requested = pyqtSignal(int)   # emitted when user clicks a tip link

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("dialog_header")
        self._tips = list(_TIPS)
        self._current = 0
        self._build_ui()
        self._show_tip()

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 6, 10, 6)
        layout.setSpacing(10)

        # Bulb icon
        bulb = QLabel("💡")
        bulb.setStyleSheet("font-size:11pt;")
        layout.addWidget(bulb)

        # Tip text (clickable if has nav target)
        self._tip_lbl = QLabel()
        self._tip_lbl.setStyleSheet("font-size:8.5pt;")
        self._tip_lbl.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextBrowserInteraction
        )
        self._tip_lbl.linkActivated.connect(self._on_link)
        layout.addWidget(self._tip_lbl, stretch=1)

        # Prev / Next when multiple tips
        self._btn_prev = QPushButton("‹")
        self._btn_prev.setFixedSize(20, 20)
        self._btn_prev.setStyleSheet("color: palette(mid); border:none; font-size:11pt;")
        self._btn_prev.clicked.connect(self._prev)
        layout.addWidget(self._btn_prev)

        self._page_lbl = QLabel()
        self._page_lbl.setStyleSheet("color: palette(mid); font-size:8pt;")
        layout.addWidget(self._page_lbl)

        self._btn_next = QPushButton("›")
        self._btn_next.setFixedSize(20, 20)
        self._btn_next.setStyleSheet("color: palette(mid); border:none; font-size:11pt;")
        self._btn_next.clicked.connect(self._next)
        layout.addWidget(self._btn_next)

        # Dismiss
        btn_dismiss = QPushButton("✕ Got it")
        btn_dismiss.setFixedHeight(22)
        btn_dismiss.setStyleSheet("color: palette(mid); font-size:8pt;")
        btn_dismiss.setToolTip("Dismiss — won't show again for this version")
        btn_dismiss.clicked.connect(self._dismiss)
        layout.addWidget(btn_dismiss)

    def _show_tip(self):
        if not self._tips:
            self.setVisible(False)
            return
        icon, text, nav_idx = self._tips[self._current]
        if nav_idx is not None:
            self._tip_lbl.setText(
                f'{icon}  <a href="nav:{nav_idx}" style="color:palette(link);">{text}</a>'
            )
        else:
            self._tip_lbl.setText(f"{icon}  {text}")

        n = len(self._tips)
        self._page_lbl.setText(f"{self._current + 1} / {n}")
        self._btn_prev.setEnabled(self._current > 0)
        self._btn_next.setEnabled(self._current < n - 1)
        multi = n > 1
        self._btn_prev.setVisible(multi)
        self._btn_next.setVisible(multi)
        self._page_lbl.setVisible(multi)

    def _prev(self):
        if self._current > 0:
            self._current -= 1
            self._show_tip()

    def _next(self):
        if self._current < len(self._tips) - 1:
            self._current += 1
            self._show_tip()

    def _on_link(self, href: str):
        if href.startswith("nav:"):
            try:
                idx = int(href[4:])
                self.nav_requested.emit(idx)
            except ValueError:
                pass
        self._dismiss()

    def _dismiss(self):
        get_settings().set("tips_seen_version", _current_app_version())
        self.setVisible(False)

    @staticmethod
    def should_show() -> bool:
        """Return True if the tip bar should be shown for this version."""
        seen = get_settings().get("tips_seen_version", "")
        return seen != _current_app_version()
