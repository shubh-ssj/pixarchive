from __future__ import annotations
import subprocess

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QWidget, QTextBrowser, QFrame
)
from PyQt6.QtCore import Qt, QSize, QThread, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPixmap, QIcon, QFont

from ui.themes import build_stylesheet, get_theme, DEFAULT_THEME_ID


APP_VERSION = "1.6.0"
GALLERY_DL_URL = "https://github.com/mikf/gallery-dl"
GUI_URL        = "https://github.com/shubh-ssj/pixarchive"
AUTHOR         = "SSJ"
AUTHOR_EMAIL   = "magnusshadowmend@gmail.com"

CHANGELOG = """
<h3>v1.6.0  <span style="color:#6c7086; font-weight:normal; font-size:9pt;">PixArchive rebrand + improvements</span></h3>
<ul>
  <li>Rebranded as PixArchive — an image downloader utility for 200+ sites</li>
  <li>Live URL detection with site banner (70+ regex patterns)</li>
  <li>Download panel with Output, Filters, Behaviour, and Network tabs</li>
  <li>19 built-in presets covering major sites and common workflows</li>
  <li>Clipboard watcher and drag-and-drop support</li>
  <li>Queue panel with live job cards and progress bars</li>
  <li>History panel backed by SQLite</li>
  <li>Searchable Sites panel (200+ sites, categorised)</li>
  <li>Config panel with form editor + raw JSON editor</li>
  <li>Accounts panel for per-site auth management</li>
  <li>System tray with completion notifications</li>
  <li>Persistent bottom status bar (session stats)</li>
  <li>Keyboard shortcuts for all panels</li>
  <li>Settings dialog (Appearance, Downloads, Network, Notifications, Advanced)</li>
  <li>Help reference with 12 sections and full-text search</li>
</ul>
"""

LICENSES = """
<h3>PixArchive</h3>
<p>MIT License — Copyright © 2026 SSJ (<a href="https://github.com/shubh-ssj">github.com/shubh-ssj</a>)</p>

<h3>gallery-dl</h3>
<p>MIT License — Copyright © 2015-2025 Mike Fährmann<br>
<a href="https://github.com/mikf/gallery-dl">https://github.com/mikf/gallery-dl</a></p>

<h3>PyQt6</h3>
<p>GPL v3 / Commercial — Copyright © Riverbank Computing Limited<br>
<a href="https://riverbankcomputing.com/software/pyqt/">https://riverbankcomputing.com/software/pyqt/</a></p>

<h3>Qt</h3>
<p>LGPL v3 — Copyright © The Qt Company<br>
<a href="https://www.qt.io/">https://www.qt.io/</a></p>
"""


def _make_logo(size: int = 72) -> QPixmap:
    """Load the PixArchive logo from assets, falling back to a painted placeholder.
    Result is cached at module level so the file is only read once.
    """
    global _LOGO_CACHE
    if _LOGO_CACHE is not None:
        return _LOGO_CACHE.scaled(
            size, size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
    import os
    base = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    path = os.path.join(base, "assets", "icon.png")
    if os.path.exists(path):
        px = QPixmap(path)
        if not px.isNull():
            _LOGO_CACHE = px
            return px.scaled(size, size,
                             Qt.AspectRatioMode.KeepAspectRatio,
                             Qt.TransformationMode.SmoothTransformation)
    # Fallback — plain coloured square with a P
    px = QPixmap(size, size)
    px.fill(Qt.GlobalColor.transparent)
    p = QPainter(px)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setBrush(QColor("#7C3AED"))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawRoundedRect(0, 0, size, size, size // 6, size // 6)
    p.setPen(QColor("white"))
    f = QFont()
    f.setPixelSize(size // 2)
    f.setBold(True)
    p.setFont(f)
    p.drawText(px.rect(), Qt.AlignmentFlag.AlignCenter, "P")
    p.end()
    _LOGO_CACHE = px
    return px

_LOGO_CACHE: QPixmap | None = None


class _GdlVersionThread(QThread):
    """Background thread to fetch gallery-dl version without blocking UI."""
    result = pyqtSignal(str)

    def __init__(self, cmd: str = "gallery-dl"):
        super().__init__()
        self._cmd = cmd

    def run(self):
        try:
            r = subprocess.run(
                [self._cmd, "--version"],
                capture_output=True, text=True, timeout=5
            )
            v = (r.stdout or r.stderr).strip()
            self.result.emit(v or "unknown")
        except FileNotFoundError:
            self.result.emit("not found — install gallery-dl")
        except Exception as e:
            self.result.emit(f"error: {e}")


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About — PixArchive")
        self.setFixedSize(540, 440)
        self._build_ui()
        self._fetch_gdl_version()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── Hero section ─────────────────────────────────────────────────────
        hero = QWidget()
        hero.setFixedHeight(140)
        hero.setObjectName("dialog_header")
        hero_layout = QHBoxLayout(hero)
        hero_layout.setContentsMargins(28, 0, 28, 0)
        hero_layout.setSpacing(20)

        logo_lbl = QLabel()
        logo_lbl.setFixedSize(100, 100)
        logo_lbl.setScaledContents(False)
        logo_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Pre-scale to exact 100x100 so Qt never re-scales during repaints
        logo_px = _make_logo(100)
        logo_lbl.setPixmap(logo_px.scaled(
            100, 100,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        ))
        hero_layout.addWidget(logo_lbl)

        text_col = QVBoxLayout()
        text_col.setSpacing(4)

        app_name = QLabel("PixArchive")
        app_name.setStyleSheet("font-size:18pt; font-weight:bold;")
        text_col.addWidget(app_name)

        ver_lbl = QLabel(f"Version {APP_VERSION}")
        ver_lbl.setStyleSheet("color: palette(highlight); font-size:10pt;")
        text_col.addWidget(ver_lbl)

        self.gdl_ver_lbl = QLabel("gallery-dl: checking…")
        self.gdl_ver_lbl.setStyleSheet("color: palette(mid); font-size:9pt;")
        text_col.addWidget(self.gdl_ver_lbl)

        hero_layout.addLayout(text_col)
        hero_layout.addStretch()
        outer.addWidget(hero)

        # Divider
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        outer.addWidget(line)

        # ── Tabs ─────────────────────────────────────────────────────────────
        tabs = QTabWidget()
        tabs.setDocumentMode(True)
        tabs.addTab(self._tab_about(),     "About")
        tabs.addTab(self._tab_changelog(), "Changelog")
        tabs.addTab(self._tab_licenses(),  "Licenses")
        outer.addWidget(tabs, stretch=1)

        # ── Buttons ──────────────────────────────────────────────────────────
        btn_bar = QWidget()
        btn_bar.setObjectName("dialog_footer")
        bl = QHBoxLayout(btn_bar)
        bl.setContentsMargins(16, 10, 16, 10)
        bl.setSpacing(8)

        gdl_btn = QPushButton("gallery-dl on GitHub")
        gdl_btn.clicked.connect(lambda: self._open_url(GALLERY_DL_URL))
        bl.addWidget(gdl_btn)

        bl.addStretch()

        close_btn = QPushButton("Close")
        close_btn.setObjectName("btn_download")
        close_btn.setFixedWidth(80)
        close_btn.clicked.connect(self.accept)
        bl.addWidget(close_btn)

        outer.addWidget(btn_bar)

    def _tab_about(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(24, 18, 24, 18)
        layout.setSpacing(10)

        desc = QLabel(
            "An image downloader utility for archiving galleries and collections "
            "from 200+ websites. Powered by <b>gallery-dl</b>."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: palette(text); font-size:10pt;")
        desc.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(desc)

        def _link_row(label: str, url: str) -> QWidget:
            row = QWidget()
            rl = QHBoxLayout(row)
            rl.setContentsMargins(0, 0, 0, 0)
            lbl = QLabel(f"<b>{label}</b>")
            lbl.setStyleSheet("color: palette(mid); font-size:9pt;")
            lbl.setFixedWidth(100)
            rl.addWidget(lbl)
            link = QLabel(f'<a href="{url}">{url}</a>')
            link.setOpenExternalLinks(True)
            link.setStyleSheet("font-size:9pt;")
            rl.addWidget(link)
            rl.addStretch()
            return row

        layout.addWidget(_link_row("GUI repo",    GUI_URL))
        layout.addWidget(_link_row("gallery-dl", GALLERY_DL_URL))

        layout.addSpacing(8)

        info_pairs = [
            ("Author",        "SSJ"),
            ("Email",         "magnusshadowmend@gmail.com"),
            ("Built with",    "Python · PyQt6 · gallery-dl"),
            ("Config stored", "~/.pixarchive/"),
            ("License",       "MIT"),
        ]
        for label, value in info_pairs:
            row = QWidget()
            rl = QHBoxLayout(row)
            rl.setContentsMargins(0, 0, 0, 0)
            k = QLabel(f"<b>{label}</b>")
            k.setStyleSheet("color: palette(mid); font-size:9pt;")
            k.setFixedWidth(100)
            rl.addWidget(k)
            v = QLabel(value)
            v.setStyleSheet("color: palette(text); font-size:9pt;")
            rl.addWidget(v)
            rl.addStretch()
            layout.addWidget(row)

        layout.addStretch()
        return w

    def _tab_changelog(self) -> QWidget:
        return self._make_browser(CHANGELOG)

    def _tab_licenses(self) -> QWidget:
        return self._make_browser(LICENSES)

    def _make_browser(self, html: str) -> QTextBrowser:
        browser = QTextBrowser()
        browser.setOpenExternalLinks(True)
        # No hardcoded colors — inherits from app stylesheet QTextBrowser rules
        browser.setHtml(f"""
        <html><head><style>
          body {{ font-family:'Segoe UI',sans-serif; font-size:9pt; }}
          li {{ margin-bottom:3px; }}
        </style></head><body>{html}</body></html>
        """)
        return browser

    def _fetch_gdl_version(self):
        self._ver_thread = _GdlVersionThread()
        self._ver_thread.result.connect(self._on_version)
        self._ver_thread.result.connect(self._ver_thread.deleteLater)
        self._ver_thread.start()

    def _on_version(self, version: str):
        MIN_VERSION = (1, 25, 0)
        self.gdl_ver_lbl.setText(f"gallery-dl {version}")
        if "not found" in version or "error" in version:
            self.gdl_ver_lbl.setStyleSheet("color: palette(bright-text); font-size:9pt;")
            return
        import re
        m = re.search(r"(\d+)\.(\d+)\.(\d+)", version)
        if m:
            parsed = tuple(int(x) for x in m.groups())
            if parsed < MIN_VERSION:
                self.gdl_ver_lbl.setText(
                    f"gallery-dl {version}  ⚠ v{'.'.join(str(x) for x in MIN_VERSION)}+ recommended"
                )
                self.gdl_ver_lbl.setStyleSheet("color: palette(mid); font-size:9pt;")
                return
        self.gdl_ver_lbl.setStyleSheet("color: palette(highlight); font-size:9pt;")

    def _open_url(self, url: str):
        import webbrowser
        from core.app_settings import get_settings
        browser = get_settings().get("preferred_browser", "")
        if browser:
            try:
                webbrowser.get(browser).open(url)
                return
            except webbrowser.Error:
                pass
        webbrowser.open(url)
