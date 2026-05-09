from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QScrollArea, QFrame, QGridLayout, QSizePolicy,
    QPushButton, QToolTip
)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtGui import QCursor

from core.sites import SUPPORTED_SITES, CATEGORIES, SITE_CATEGORIES


# Auth badge text only — background/foreground driven by objectName QSS
AUTH_STYLES = {
    "oauth":     ("OAuth",     "palette(dark)", "palette(highlight)"),
    "cookies":   ("Cookies",   "palette(shadow)", "palette(text)"),
    "required":  ("Required",  "palette(shadow)", "palette(bright-text)"),
    "supported": ("Optional",  "palette(dark)", "palette(link)"),
    None:        ("Public",    "palette(base)", "palette(mid)"),
}


class SiteCard(QFrame):
    url_clicked = pyqtSignal(str)

    def __init__(self, name: str, url: str, capabilities: str, auth: str | None, parent=None):
        super().__init__(parent)
        self.url = url
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFixedHeight(88)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setStyleSheet(
            "SiteCard { background-color: palette(base); border: 1px solid palette(midlight); border-radius: 8px; }"
            "SiteCard:hover { border-color: palette(highlight); background-color: palette(alternateBase); }"
        )
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)

        # Top row: name + auth badge
        top = QHBoxLayout()
        name_lbl = QLabel(name)
        name_lbl.setStyleSheet("font-weight:bold; font-size:10pt;")
        top.addWidget(name_lbl, stretch=1)

        auth_text, auth_bg, auth_fg = AUTH_STYLES.get(auth, AUTH_STYLES[None])
        badge = QLabel(auth_text)
        badge.setStyleSheet(
            f"background:{auth_bg}; color:{auth_fg}; border-radius:4px;"
            "padding:1px 6px; font-size:8pt; font-weight:bold;"
        )
        top.addWidget(badge)
        layout.addLayout(top)

        # URL
        url_lbl = QLabel(url)
        url_lbl.setStyleSheet("color: palette(highlight); font-size: 8pt;")
        url_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(url_lbl)

        # Capabilities (truncated)
        cap_lbl = QLabel(capabilities)
        cap_lbl.setStyleSheet("color: palette(mid); font-size: 8pt;")
        cap_lbl.setWordWrap(False)
        metrics = cap_lbl.fontMetrics()
        elided = metrics.elidedText(capabilities, Qt.TextElideMode.ElideRight, 320)
        cap_lbl.setText(elided)
        cap_lbl.setToolTip(capabilities)
        layout.addWidget(cap_lbl)

        layout.addStretch()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.url_clicked.emit(self.url)
        super().mousePressEvent(event)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Space):
            self.url_clicked.emit(self.url)
        else:
            super().keyPressEvent(event)


class SitesPanel(QWidget):
    """Browse all supported gallery-dl sites with search and category filter."""

    url_selected = pyqtSignal(str)   # emitted when user clicks "use this URL"

    def __init__(self):
        super().__init__()
        self._all_sites = SUPPORTED_SITES
        self._build_ui()
        self._populate(self._all_sites)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Toolbar ──────────────────────────────────────────────────────────
        toolbar = QWidget()
        toolbar.setObjectName("dialog_header")
        tb = QHBoxLayout(toolbar)
        tb.setContentsMargins(12, 10, 12, 10)
        tb.setSpacing(10)

        title = QLabel("Supported Sites")
        title.setStyleSheet("font-weight:bold; font-size:11pt; color: palette(link);")
        tb.addWidget(title)

        self.count_lbl = QLabel()
        self.count_lbl.setStyleSheet("color: palette(mid); font-size:9pt;")
        tb.addWidget(self.count_lbl)

        tb.addStretch()

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search sites…")
        self.search_box.setFixedWidth(200)
        self.search_box.setFixedHeight(30)
        self.search_box.textChanged.connect(self._on_filter_changed)
        tb.addWidget(self.search_box)

        self.cat_combo = QComboBox()
        self.cat_combo.addItems(CATEGORIES)
        self.cat_combo.setFixedHeight(30)
        self.cat_combo.setFixedWidth(210)
        self.cat_combo.currentTextChanged.connect(self._on_filter_changed)
        tb.addWidget(self.cat_combo)

        layout.addWidget(toolbar)

        # ── Auth legend ───────────────────────────────────────────────────────
        legend = QWidget()
        legend.setObjectName("dialog_header")
        leg = QHBoxLayout(legend)
        leg.setContentsMargins(12, 6, 12, 6)
        leg.setSpacing(14)
        key_lbl = QLabel("Auth key:")
        key_lbl.setStyleSheet("color: palette(mid); font-size:8pt;")
        leg.addWidget(key_lbl)
        for key, (text, bg, fg) in AUTH_STYLES.items():
            display = "Public (no auth)" if key is None else text
            lbl = QLabel(display)
            lbl.setStyleSheet(f"background:{bg}; color:{fg}; border-radius:4px; padding:1px 7px; font-size:8pt;")
            leg.addWidget(lbl)
        leg.addStretch()
        layout.addWidget(legend)

        # ── Cards grid ────────────────────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        self.grid_widget = QWidget()
        self.grid_widget.setStyleSheet("background-color: palette(base);")
        self.grid = QGridLayout(self.grid_widget)
        self.grid.setContentsMargins(12, 12, 12, 12)
        self.grid.setSpacing(8)

        scroll.setWidget(self.grid_widget)
        layout.addWidget(scroll, stretch=1)

    def _populate(self, sites):
        # Clear existing cards
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        cols = 3
        for i, (name, url, caps, auth) in enumerate(sites):
            card = SiteCard(name, url, caps, auth)
            card.url_clicked.connect(self.url_selected)
            self.grid.addWidget(card, i // cols, i % cols)

        # Fill last row
        remainder = len(sites) % cols
        if remainder:
            row = len(sites) // cols
            for c in range(remainder, cols):
                spacer = QWidget()
                spacer.setFixedHeight(88)
                self.grid.addWidget(spacer, row, c)

        self.count_lbl.setText(f"{len(sites)} sites")
        # Allow Tab navigation through cards
        for i in range(self.grid.count()):
            w = self.grid.itemAt(i).widget()
            if w:
                w.setFocusPolicy(Qt.FocusPolicy.TabFocus)

    def _on_filter_changed(self):
        query = self.search_box.text().strip().lower()
        category = self.cat_combo.currentText()

        results = []
        for entry in self._all_sites:
            name, url, caps, auth = entry
            if category != "All":
                site_cat = SITE_CATEGORIES.get(name, "Other / Misc")
                if site_cat != category:
                    continue
            if query and query not in name.lower() and query not in url.lower() and query not in caps.lower():
                continue
            results.append(entry)

        self._populate(results)


