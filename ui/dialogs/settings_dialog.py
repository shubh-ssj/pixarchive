from __future__ import annotations
import subprocess

from PyQt6.QtWidgets import (
    QDialog, QHBoxLayout, QVBoxLayout, QListWidget, QListWidgetItem,
    QStackedWidget, QWidget, QLabel, QFormLayout, QLineEdit,
    QCheckBox, QSpinBox, QDoubleSpinBox, QComboBox, QPushButton,
    QFileDialog, QMessageBox, QFrame, QScrollArea, QSizePolicy,
    QButtonGroup, QApplication
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QColor, QPixmap, QPainter, QFont

from core.app_settings import get_settings, DEFAULTS
from ui.themes import list_themes, get_theme, build_stylesheet, Theme


# ── Helpers ───────────────────────────────────────────────────────────────────

def _section(text: str) -> QLabel:
    lbl = QLabel(text.upper())
    lbl.setStyleSheet(
        "color: palette(mid); font-size:8pt; font-weight:bold;"
        "letter-spacing:1px; margin-top:10px; margin-bottom:2px;"
    )
    return lbl


def _divider() -> QFrame:
    f = QFrame()
    f.setFrameShape(QFrame.Shape.HLine)
    f.setStyleSheet("background: palette(midlight); max-height:1px; border:none;")
    return f


def _scrollable(w: QWidget) -> QScrollArea:
    s = QScrollArea()
    s.setWidgetResizable(True)
    s.setFrameShape(QFrame.Shape.NoFrame)
    s.setWidget(w)
    return s


# ── Theme preview card ────────────────────────────────────────────────────────

def _make_theme_swatch(t: Theme, w: int = 180, h: int = 110) -> QPixmap:
    """Paint a mini mock-up of the theme onto a pixmap."""
    px = QPixmap(w, h)
    p = QPainter(px)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Background
    p.fillRect(0, 0, w, h, QColor(t.bg_base))

    # Sidebar strip
    p.fillRect(0, 0, 38, h, QColor(t.bg_mantle))

    # Sidebar "nav items" — three coloured dots
    for i, col in enumerate([t.accent, t.text_tertiary, t.text_tertiary]):
        p.setBrush(QColor(col))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(8, 14 + i * 16, 22, 8, 3, 3)

    # Main area — fake URL bar
    p.fillRect(40, 6, w - 46, 18, QColor(t.bg_mantle))
    p.setBrush(QColor(t.bg_surface0))
    p.drawRoundedRect(44, 9, w - 80, 12, 3, 3)

    # Accent "Download" button
    p.setBrush(QColor(t.accent))
    p.drawRoundedRect(w - 32, 9, 26, 12, 3, 3)

    # Card area — two fake job cards
    for i in range(2):
        y = 32 + i * 32
        p.setBrush(QColor(t.bg_surface0))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(42, y, w - 50, 26, 4, 4)

        # site badge
        p.setBrush(QColor(t.accent))
        p.drawRoundedRect(48, y + 7, 28, 10, 3, 3)

        # progress bar bg
        p.setBrush(QColor(t.bg_surface2))
        p.drawRoundedRect(82, y + 18, w - 96, 3, 1, 1)
        # progress fill (50% / 80%)
        fill = int((w - 96) * (0.5 if i == 0 else 0.8))
        p.setBrush(QColor(t.accent))
        p.drawRoundedRect(82, y + 18, fill, 3, 1, 1)

    # Status bar
    p.fillRect(0, h - 16, w, 16, QColor(t.log_bg))
    p.setBrush(QColor(t.success))
    p.drawEllipse(44, h - 11, 6, 6)

    p.end()
    return px


class ThemeCard(QFrame):
    def __init__(self, theme: Theme, selected: bool, parent=None):
        super().__init__(parent)
        self.theme = theme
        self._selected = selected
        self.setFixedSize(196, 158)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._refresh_border()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        # Swatch
        swatch_lbl = QLabel()
        swatch_lbl.setPixmap(_make_theme_swatch(theme))
        swatch_lbl.setFixedSize(180, 110)
        swatch_lbl.setScaledContents(True)
        layout.addWidget(swatch_lbl)

        # Name + dark/light badge
        row = QHBoxLayout()
        row.setSpacing(6)
        name_lbl = QLabel(theme.name)
        name_lbl.setStyleSheet("font-size:9pt; font-weight:bold;")
        row.addWidget(name_lbl)

        kind = "Dark" if theme.dark else "Light"
        kind_col = ("#1e3a5f", "#89b4fa") if theme.dark else ("#2a2010", "#f9e2af")
        badge = QLabel(kind)
        badge.setStyleSheet(
            f"background:{kind_col[0]}; color:{kind_col[1]}; border-radius:3px;"
            "padding:0px 5px; font-size:7pt; font-weight:bold;"
        )
        row.addWidget(badge)
        row.addStretch()
        layout.addLayout(row)

    def _refresh_border(self):
        if self._selected:
            self.setStyleSheet(
                "ThemeCard { border: 2px solid palette(highlight);"
                "border-radius: 10px; background: palette(base); }"
            )
        else:
            self.setStyleSheet(
                "ThemeCard { border: 1px solid palette(midlight);"
                "border-radius: 10px; background: palette(base); }"
                "ThemeCard:hover { border-color: palette(mid); }"
            )

    def set_selected(self, sel: bool):
        self._selected = sel
        self._refresh_border()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # Walk up the widget tree to find SettingsDialog regardless of
            # how many container layers the scroll area inserts.
            w = self.parent()
            while w is not None and not isinstance(w, SettingsDialog):
                w = w.parent()
            if w is not None:
                w._on_theme_card_clicked(self)
        super().mousePressEvent(event)


# ── Main dialog ───────────────────────────────────────────────────────────────

class SettingsDialog(QDialog):
    PAGES = [
        ("Appearance",    "🎨"),
        ("Downloads",     "⬇"),
        ("Network",       "🌐"),
        ("Notifications", "🔔"),
        ("Advanced",      "⚙"),
        ("Shortcuts",     "⌨"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings — PixArchive")
        self.setMinimumSize(760, 560)
        self.resize(820, 600)
        self._s = get_settings()
        self._theme_cards: list[ThemeCard] = []
        self._selected_theme_id: str = self._s.get("theme_id", "catppuccin-mocha")
        self._build_ui()
        self._load_values()

    # ── Layout ───────────────────────────────────────────────────────────────

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Header
        header = QWidget()
        header.setObjectName("dialog_header")
        header.setFixedHeight(48)
        hl = QHBoxLayout(header)
        hl.setContentsMargins(18, 0, 18, 0)
        title_lbl = QLabel("Settings")
        title_lbl.setStyleSheet("font-size:13pt; font-weight:bold;")
        hl.addWidget(title_lbl)
        hl.addStretch()
        outer.addWidget(header)

        # Body
        body = QWidget()
        bl = QHBoxLayout(body)
        bl.setContentsMargins(0, 0, 0, 0)
        bl.setSpacing(0)

        self.page_list = QListWidget()
        self.page_list.setFixedWidth(158)
        for label, icon in self.PAGES:
            item = QListWidgetItem(f"  {icon}  {label}")
            item.setSizeHint(QSize(0, 38))
            self.page_list.addItem(item)
        self.page_list.setCurrentRow(0)
        bl.addWidget(self.page_list)

        self.stack = QStackedWidget()
        self.stack.addWidget(self._page_appearance())
        self.stack.addWidget(self._page_downloads())
        self.stack.addWidget(self._page_network())
        self.stack.addWidget(self._page_notifications())
        self.stack.addWidget(self._page_advanced())
        self.stack.addWidget(self._page_shortcuts())
        bl.addWidget(self.stack, stretch=1)
        self.page_list.currentRowChanged.connect(self.stack.setCurrentIndex)
        outer.addWidget(body, stretch=1)

        # Footer
        footer = QWidget()
        footer.setObjectName("dialog_footer")
        fl = QHBoxLayout(footer)
        fl.setContentsMargins(16, 10, 16, 10)
        fl.setSpacing(8)
        self.btn_reset = QPushButton("Reset all to defaults")
        self.btn_reset.setStyleSheet("color: palette(bright-text);")
        self.btn_reset.clicked.connect(self._reset_all)
        fl.addWidget(self.btn_reset)
        fl.addStretch()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        fl.addWidget(btn_cancel)
        btn_save = QPushButton("Save")
        btn_save.setObjectName("btn_download")
        btn_save.setFixedWidth(90)
        btn_save.clicked.connect(self._save)
        fl.addWidget(btn_save)
        outer.addWidget(footer)

    # ── Appearance page ───────────────────────────────────────────────────────

    def _page_appearance(self) -> QWidget:
        container = QWidget()
        vbox = QVBoxLayout(container)
        vbox.setContentsMargins(24, 16, 24, 16)
        vbox.setSpacing(8)

        vbox.addWidget(_section("Theme"))

        # Theme grid — 3 cards per row
        themes = list_themes()
        row_widget = QWidget()
        grid = QHBoxLayout(row_widget)  # we'll wrap manually
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(10)

        # Wrap into rows of 3
        rows_container = QWidget()
        rows_layout = QVBoxLayout(rows_container)
        rows_layout.setContentsMargins(0, 0, 0, 0)
        rows_layout.setSpacing(10)

        row_h: QHBoxLayout | None = None
        for i, theme in enumerate(themes):
            if i % 3 == 0:
                row_w = QWidget()
                row_h = QHBoxLayout(row_w)
                row_h.setContentsMargins(0, 0, 0, 0)
                row_h.setSpacing(10)
                rows_layout.addWidget(row_w)

            selected = theme.id == self._selected_theme_id
            card = ThemeCard(theme, selected, rows_container)
            row_h.addWidget(card)
            self._theme_cards.append(card)

        # Fill last row if not complete
        last_row_count = len(themes) % 3
        if last_row_count and row_h:
            for _ in range(3 - last_row_count):
                spacer = QWidget()
                spacer.setFixedSize(196, 158)
                row_h.addWidget(spacer)
            row_h.addStretch()

        vbox.addWidget(rows_container)

        vbox.addWidget(_divider())
        vbox.addWidget(_section("Typography"))

        font_form = QFormLayout()
        font_form.setHorizontalSpacing(14)
        self.font_size = QSpinBox()
        self.font_size.setRange(8, 18)
        self.font_size.setSuffix(" pt")
        self.font_size.setFixedWidth(80)
        font_form.addRow("Interface font size", self.font_size)
        vbox.addLayout(font_form)

        vbox.addWidget(_divider())
        vbox.addWidget(_section("Layout"))

        self.show_banner    = QCheckBox("Show site detection banner when a URL is recognised")
        self.compact_cards  = QCheckBox("Compact queue cards  (reduces card height)")
        vbox.addWidget(self.show_banner)
        vbox.addWidget(self.compact_cards)

        lf = QFormLayout()
        lf.setHorizontalSpacing(14)
        self.log_max = QSpinBox()
        self.log_max.setRange(500, 20000)
        self.log_max.setSingleStep(500)
        self.log_max.setFixedWidth(100)
        lf.addRow("Max log lines retained", self.log_max)
        vbox.addLayout(lf)
        vbox.addStretch()

        return _scrollable(container)

    def _on_theme_card_clicked(self, clicked_card: ThemeCard):
        for card in self._theme_cards:
            card.set_selected(card is clicked_card)
        self._selected_theme_id = clicked_card.theme.id
        # Live preview — update palette AND stylesheet (reverted on Cancel)
        from ui.themes import apply_theme
        font_size = self.font_size.value() if hasattr(self, "font_size") else self._s.get("font_size", 10)
        apply_theme(QApplication.instance(), clicked_card.theme.id, font_size)

    # ── Downloads page ────────────────────────────────────────────────────────

    def _page_downloads(self) -> QWidget:
        w = QWidget()
        vbox = QVBoxLayout(w)
        vbox.setContentsMargins(24, 20, 24, 20)
        vbox.setSpacing(8)

        vbox.addWidget(_section("Default output location"))
        dir_row = QHBoxLayout()
        self.default_dir = QLineEdit()
        self.default_dir.setPlaceholderText("Leave blank to use gallery-dl config value")
        btn_browse = QPushButton("Browse…")
        btn_browse.clicked.connect(self._browse_dir)
        dir_row.addWidget(self.default_dir)
        dir_row.addWidget(btn_browse)
        vbox.addLayout(dir_row)

        vbox.addWidget(_section("Default filename pattern"))
        self.default_filename = QLineEdit()
        self.default_filename.setPlaceholderText("{filename}.{extension}  — blank = gallery-dl default")
        vbox.addWidget(self.default_filename)

        vbox.addWidget(_divider())
        vbox.addWidget(_section("Queue behaviour"))
        self.auto_start   = QCheckBox("Automatically start downloading when items are added to the queue")
        self.confirm_stop = QCheckBox("Ask for confirmation before stopping an active download")
        vbox.addWidget(self.auto_start)
        vbox.addWidget(self.confirm_stop)

        cf = QFormLayout()
        cf.setHorizontalSpacing(14)
        self.max_concurrent = QSpinBox()
        self.max_concurrent.setRange(1, 8)
        self.max_concurrent.setFixedWidth(80)
        self.max_concurrent.setToolTip("Most sites rate-limit aggressively — keep at 1 or 2.")
        cf.addRow("Max concurrent downloads", self.max_concurrent)
        vbox.addLayout(cf)
        vbox.addStretch()
        return _scrollable(w)

    # ── Network page ─────────────────────────────────────────────────────────

    def _page_network(self) -> QWidget:
        w = QWidget()
        form = QFormLayout(w)
        form.setContentsMargins(24, 20, 24, 20)
        form.setVerticalSpacing(10)
        form.setHorizontalSpacing(14)

        self.def_retries = QSpinBox()
        self.def_retries.setRange(0, 20)
        self.def_retries.setFixedWidth(80)
        form.addRow("Default retries", self.def_retries)

        self.def_timeout = QDoubleSpinBox()
        self.def_timeout.setRange(0, 300)
        self.def_timeout.setSuffix(" s")
        self.def_timeout.setFixedWidth(100)
        form.addRow("Default timeout", self.def_timeout)

        self.def_rate = QLineEdit()
        self.def_rate.setPlaceholderText("e.g.  500k   or   2M  (bytes/sec)")
        form.addRow("Default rate limit", self.def_rate)

        self.def_proxy = QLineEdit()
        self.def_proxy.setPlaceholderText("http://user:pass@host:port")
        form.addRow("Default proxy", self.def_proxy)

        note = QLabel("These pre-fill the Network tab in the Download panel. They don't override per-job settings.")
        note.setWordWrap(True)
        note.setStyleSheet("color: palette(mid); font-size:9pt; margin-top:12px;")
        form.addRow(note)
        return w

    # ── Notifications page ────────────────────────────────────────────────────

    def _page_notifications(self) -> QWidget:
        w = QWidget()
        vbox = QVBoxLayout(w)
        vbox.setContentsMargins(24, 20, 24, 20)
        vbox.setSpacing(8)

        vbox.addWidget(_section("Desktop notifications"))
        self.notify_complete = QCheckBox("Notify when a download finishes successfully")
        self.notify_error    = QCheckBox("Notify when a download fails")
        self.notify_sound    = QCheckBox("Play a sound with notifications  (system default)")
        self.notify_always   = QCheckBox("Notify even when the main window is visible")
        for cb in (self.notify_complete, self.notify_error, self.notify_sound, self.notify_always):
            vbox.addWidget(cb)

        vbox.addWidget(_divider())
        vbox.addWidget(_section("Window behaviour"))
        self.minimize_tray   = QCheckBox("Minimize to system tray instead of taskbar")
        self.start_minimized = QCheckBox("Start minimized to tray on launch")
        for cb in (self.minimize_tray, self.start_minimized):
            vbox.addWidget(cb)

        note = QLabel("Notifications only appear when the main window is hidden. Tray support requires a compatible desktop environment.")
        note.setWordWrap(True)
        note.setStyleSheet("color: palette(mid); font-size:9pt; margin-top:12px;")
        vbox.addWidget(note)
        vbox.addStretch()
        return w

    # ── Advanced page ─────────────────────────────────────────────────────────

    def _page_advanced(self) -> QWidget:
        w = QWidget()
        vbox = QVBoxLayout(w)
        vbox.setContentsMargins(24, 20, 24, 20)
        vbox.setSpacing(8)

        vbox.addWidget(_section("gallery-dl executable"))
        exe_row = QHBoxLayout()
        self.gdl_path = QLineEdit()
        self.gdl_path.setPlaceholderText("gallery-dl  (must be on PATH, or give full path)")
        btn_detect = QPushButton("Detect")
        btn_detect.clicked.connect(self._detect_gdl)
        exe_row.addWidget(self.gdl_path)
        exe_row.addWidget(btn_detect)
        vbox.addLayout(exe_row)
        self.gdl_version_lbl = QLabel()
        self.gdl_version_lbl.setStyleSheet("color: palette(mid); font-size:8pt;")
        vbox.addWidget(self.gdl_version_lbl)
        self._detect_gdl(silent=True)

        vbox.addWidget(_divider())
        vbox.addWidget(_section("Preferred browser"))
        bf = QFormLayout()
        bf.setHorizontalSpacing(14)
        self.preferred_browser = QComboBox()
        self.preferred_browser.addItems([
            "System default", "chrome", "edge", "firefox", "safari", "opera", "brave",
        ])
        self.preferred_browser.setToolTip(
            "Browser used when opening links from within the app (e.g. site pages, help links).\n"
            "This does not affect gallery-dl's own cookie extraction setting."
        )
        bf.addRow("Open links in", self.preferred_browser)
        vbox.addLayout(bf)

        vbox.addWidget(_divider())
        vbox.addWidget(_section("Logging"))
        lf = QFormLayout()
        lf.setHorizontalSpacing(14)
        self.log_level = QComboBox()
        self.log_level.addItems(["debug", "info", "warning", "error"])
        self.log_level.setFixedWidth(120)
        lf.addRow("Log level", self.log_level)
        vbox.addLayout(lf)

        vbox.addWidget(_divider())
        vbox.addWidget(_section("Clipboard & drag-drop"))
        self.clipboard_watch = QCheckBox("Auto-paste recognised URLs from clipboard when window is focused")
        self.drag_drop       = QCheckBox("Enable drag and drop of URLs onto the download panel")
        vbox.addWidget(self.clipboard_watch)
        vbox.addWidget(self.drag_drop)

        vbox.addWidget(_divider())
        vbox.addWidget(_section("Window"))
        self.remember_size = QCheckBox("Remember window size between sessions")
        vbox.addWidget(self.remember_size)

        vbox.addWidget(_divider())
        danger = QLabel("DANGER ZONE")
        danger.setStyleSheet("color: palette(bright-text); font-size:8pt; font-weight:bold; letter-spacing:1px; margin-top:10px;")
        vbox.addWidget(danger)

        btn_clr_hist = QPushButton("Clear all download history…")
        btn_clr_hist.setStyleSheet("color: palette(bright-text); border-color: palette(bright-text);")
        btn_clr_hist.clicked.connect(self._clear_history)
        vbox.addWidget(btn_clr_hist)

        btn_clr_creds = QPushButton("Clear all saved credentials…")
        btn_clr_creds.setStyleSheet("color: palette(bright-text); border-color: palette(bright-text);")
        btn_clr_creds.clicked.connect(self._clear_accounts)
        vbox.addWidget(btn_clr_creds)

        vbox.addStretch()
        return _scrollable(w)

    # ── Shortcuts page ────────────────────────────────────────────────────────

    def _page_shortcuts(self) -> QWidget:
        w = QWidget()
        vbox = QVBoxLayout(w)
        vbox.setContentsMargins(24, 20, 24, 20)
        vbox.setSpacing(4)
        vbox.addWidget(_section("Keyboard shortcuts"))

        shortcuts = [
            ("Ctrl+1",       "Switch to Download panel"),
            ("Ctrl+2",       "Switch to Queue panel"),
            ("Ctrl+3",       "Switch to History panel"),
            ("Ctrl+4",       "Switch to Sites panel"),
            ("Ctrl+5",       "Switch to Config panel"),
            ("Ctrl+6",       "Switch to Accounts panel"),
            ("Ctrl+Shift+V", "Paste clipboard URL into download bar"),
            ("Ctrl+,",       "Open Settings"),
            ("F1",           "Open Help"),
        ]
        for key, desc in shortcuts:
            row = QWidget()
            row.setFixedHeight(36)
            rl = QHBoxLayout(row)
            rl.setContentsMargins(10, 0, 10, 0)
            key_lbl = QLabel(key)
            key_lbl.setStyleSheet(
                "background: palette(mid); color: palette(window-text);"
                "font-family:monospace; font-size:9pt;"
                "border:1px solid palette(midlight); border-radius:4px; padding:1px 8px;"
            )
            key_lbl.setFixedWidth(140)
            rl.addWidget(key_lbl)
            desc_lbl = QLabel(desc)
            desc_lbl.setStyleSheet("color: palette(text); font-size:9pt;")
            rl.addWidget(desc_lbl, stretch=1)
            vbox.addWidget(row)
            vbox.addSpacing(2)

        vbox.addStretch()
        note = QLabel("Shortcut customisation is not yet supported.")
        note.setStyleSheet("color: palette(mid); font-size:8pt; margin-top:14px;")
        vbox.addWidget(note)
        return _scrollable(w)

    # ── Load / Save ───────────────────────────────────────────────────────────

    def _load_values(self):
        s = self._s
        # Theme cards
        self._selected_theme_id = s.get("theme_id", "catppuccin-mocha")
        for card in self._theme_cards:
            card.set_selected(card.theme.id == self._selected_theme_id)
        # Font / layout
        self.font_size.setValue(s.get("font_size", 10))
        self.show_banner.setChecked(s.get("show_site_banner", True))
        self.compact_cards.setChecked(s.get("compact_queue_cards", False))
        self.log_max.setValue(s.get("log_max_lines", 3000))
        # Downloads
        self.default_dir.setText(s.get("default_output_dir", ""))
        self.default_filename.setText(s.get("default_filename", ""))
        self.auto_start.setChecked(s.get("auto_start_queue", False))
        self.confirm_stop.setChecked(s.get("confirm_before_stop", True))
        self.max_concurrent.setValue(s.get("max_concurrent", 1))
        # Network
        self.def_retries.setValue(s.get("default_retries", 4))
        self.def_timeout.setValue(s.get("default_timeout", 30.0))
        self.def_rate.setText(s.get("default_rate_limit", ""))
        self.def_proxy.setText(s.get("default_proxy", ""))
        # Notifications
        self.notify_complete.setChecked(s.get("notify_on_complete", True))
        self.notify_error.setChecked(s.get("notify_on_error", True))
        self.notify_sound.setChecked(s.get("notify_sound", False))
        self.notify_always.setChecked(s.get("notify_always", False))
        self.minimize_tray.setChecked(s.get("minimize_to_tray", True))
        self.start_minimized.setChecked(s.get("start_minimized", False))
        # Advanced
        self.gdl_path.setText(s.get("gallery_dl_path", "gallery-dl"))
        pb = s.get("preferred_browser", "") or "System default"
        pb_idx = self.preferred_browser.findText(pb)
        self.preferred_browser.setCurrentIndex(pb_idx if pb_idx >= 0 else 0)
        idx = self.log_level.findText(s.get("log_level", "info"))
        if idx >= 0:
            self.log_level.setCurrentIndex(idx)
        self.clipboard_watch.setChecked(s.get("clipboard_watch", True))
        self.drag_drop.setChecked(s.get("drag_drop_enabled", True))
        self.remember_size.setChecked(s.get("remember_window_size", True))

    def _save(self):
        # Use set_many so the entire batch is written in a single disk flush,
        # and all changed signals fire after the write completes.
        self._s.set_many({
            "theme_id":             self._selected_theme_id,
            "font_size":            self.font_size.value(),
            "show_site_banner":     self.show_banner.isChecked(),
            "compact_queue_cards":  self.compact_cards.isChecked(),
            "log_max_lines":        self.log_max.value(),
            "default_output_dir":   self.default_dir.text().strip(),
            "default_filename":     self.default_filename.text().strip(),
            "auto_start_queue":     self.auto_start.isChecked(),
            "confirm_before_stop":  self.confirm_stop.isChecked(),
            "max_concurrent":       self.max_concurrent.value(),
            "default_retries":      self.def_retries.value(),
            "default_timeout":      self.def_timeout.value(),
            "default_rate_limit":   self.def_rate.text().strip(),
            "default_proxy":        self.def_proxy.text().strip(),
            "notify_on_complete":   self.notify_complete.isChecked(),
            "notify_on_error":      self.notify_error.isChecked(),
            "notify_sound":         self.notify_sound.isChecked(),
            "notify_always":        self.notify_always.isChecked(),
            "minimize_to_tray":     self.minimize_tray.isChecked(),
            "start_minimized":      self.start_minimized.isChecked(),
            "gallery_dl_path":      self.gdl_path.text().strip() or "gallery-dl",
            "preferred_browser":    "" if self.preferred_browser.currentText() == "System default"
                                       else self.preferred_browser.currentText(),
            "log_level":            self.log_level.currentText(),
            "clipboard_watch":      self.clipboard_watch.isChecked(),
            "drag_drop_enabled":    self.drag_drop.isChecked(),
            "remember_window_size": self.remember_size.isChecked(),
        })
        self.accept()

    def reject(self):
        # Revert live preview to the saved theme
        saved_id = self._s.get("theme_id", "catppuccin-mocha")
        from ui.themes import apply_theme
        apply_theme(QApplication.instance(), saved_id, self._s.get("font_size", 10))
        super().reject()

    def _reset_all(self):
        r = QMessageBox.question(
            self, "Reset settings",
            "Reset all settings to defaults?\nThis cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if r == QMessageBox.StandardButton.Yes:
            self._s.reset_all()
            self._load_values()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _browse_dir(self):
        path = QFileDialog.getExistingDirectory(self, "Select default output directory")
        if path:
            self.default_dir.setText(path)

    def _detect_gdl(self, silent: bool = False):
        cmd = self.gdl_path.text().strip() if hasattr(self, "gdl_path") and self.gdl_path.text().strip() else "gallery-dl"
        try:
            r = subprocess.run([cmd, "--version"], capture_output=True, text=True, timeout=5)
            v = (r.stdout or r.stderr).strip()
            if hasattr(self, "gdl_version_lbl"):
                # FIX #8: version warning
                import re as _re
                m = _re.search(r"(\d+)\.(\d+)\.(\d+)", v)
                if m and tuple(int(x) for x in m.groups()) < (1, 25, 0):
                    self.gdl_version_lbl.setText(f"Detected: {v}  ⚠ v1.25.0+ recommended")
                    self.gdl_version_lbl.setStyleSheet("color: palette(link); font-size:8pt;")
                else:
                    self.gdl_version_lbl.setText(f"Detected: {v}")
                    self.gdl_version_lbl.setStyleSheet("color: palette(highlight); font-size:8pt;")
        except FileNotFoundError:
            if hasattr(self, "gdl_version_lbl"):
                self.gdl_version_lbl.setText("Not found — install gallery-dl first")
                self.gdl_version_lbl.setStyleSheet("color: palette(bright-text); font-size:8pt;")
            if not silent:
                QMessageBox.warning(self, "Not found", f"'{cmd}' was not found.")
        except Exception as e:
            if hasattr(self, "gdl_version_lbl"):
                self.gdl_version_lbl.setText(f"Error: {e}")

    def _clear_history(self):
        import sqlite3
        from ui.panels.history_panel import DB_PATH
        r = QMessageBox.question(self, "Clear history", "Delete all history? Cannot be undone.",
                                 QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if r == QMessageBox.StandardButton.Yes:
            try:
                con = sqlite3.connect(DB_PATH)
                con.execute("DELETE FROM history")
                con.commit(); con.close()
                QMessageBox.information(self, "Done", "History cleared.")
            except Exception as e:
                QMessageBox.warning(self, "Error", str(e))

    def _clear_accounts(self):
        import os
        from ui.panels.accounts_panel import CREDS_PATH
        r = QMessageBox.question(self, "Clear credentials", "Delete all saved credentials? Cannot be undone.",
                                 QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if r == QMessageBox.StandardButton.Yes:
            try:
                if os.path.exists(CREDS_PATH):
                    os.remove(CREDS_PATH)
                QMessageBox.information(self, "Done", "Credentials cleared.")
            except Exception as e:
                QMessageBox.warning(self, "Error", str(e))

