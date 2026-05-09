"""
Per-site overrides editor — embedded as a tab inside ConfigPanel.
"""
from __future__ import annotations

from typing import Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QStackedWidget, QFormLayout,
    QLineEdit, QSpinBox, QDoubleSpinBox, QCheckBox, QComboBox,
    QFrame, QSplitter, QMessageBox, QAbstractItemView,
)
from PyQt6.QtCore import Qt, pyqtSlot

import core.site_overrides as overrides_mgr
from core.site_overrides import OVERRIDABLE_FIELDS


# Friendly labels for each overridable field
_FIELD_LABELS: dict[str, str] = {
    "output_dir":           "Save directory",
    "filename_pattern":     "Filename pattern",
    "skip_existing":        "Skip existing files",
    "set_mtime":            "Set mtime from metadata",
    "write_metadata":       "Write metadata .json",
    "write_tags":           "Write tags to XMP/EXIF",
    "write_info_json":      "Write info.json",
    "item_filter":          "Item filter expression",
    "image_filter":         "Image filter expression",
    "retries":              "Retries",
    "timeout":              "Timeout (s)",
    "rate_limit":           "Rate limit",
    "cookies_from_browser": "Cookies from browser",
    "cookies_file":         "Cookies file path",
    "proxy":                "Proxy URL",
}

_BROWSERS = ["None", "chrome", "firefox", "edge", "safari", "opera", "brave"]


class SiteOverridesWidget(QWidget):
    """Tab widget for editing per-site download overrides."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_site: Optional[str] = None
        self._build_ui()
        self._refresh_list()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Info banner
        info = QLabel(
            "  Per-site overrides apply automatically whenever a URL matches that site. "
            "They win over defaults but lose to anything you explicitly set in the Download panel."
        )
        info.setWordWrap(True)
        info.setStyleSheet(
            "background: palette(alternateBase); color: palette(mid); "
            "font-size:8pt; padding:8px 12px;"
        )
        layout.addWidget(info)

        # Splitter: site list left, editor right
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(1)

        # ── Left: site list ───────────────────────────────────────────────────
        left = QWidget()
        left.setFixedWidth(200)
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        list_header = QWidget()
        list_header.setObjectName("dialog_header")
        lh = QHBoxLayout(list_header)
        lh.setContentsMargins(10, 6, 10, 6)
        lh.setSpacing(6)
        lh_title = QLabel("Sites with overrides")
        lh_title.setStyleSheet("font-size:9pt; font-weight:bold; color:palette(mid);")
        lh.addWidget(lh_title, stretch=1)
        btn_add = QPushButton("+")
        btn_add.setFixedSize(22, 22)
        btn_add.setToolTip("Add override for a new site")
        btn_add.clicked.connect(self._on_add_site)
        lh.addWidget(btn_add)
        left_layout.addWidget(list_header)

        self.site_list = QListWidget()
        self.site_list.setFrameShape(QFrame.Shape.NoFrame)
        self.site_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.site_list.currentTextChanged.connect(self._on_site_selected)
        left_layout.addWidget(self.site_list, stretch=1)

        self.btn_delete_site = QPushButton("Remove site")
        self.btn_delete_site.setObjectName("btn_stop")
        self.btn_delete_site.setEnabled(False)
        self.btn_delete_site.clicked.connect(self._on_delete_site)
        left_layout.addWidget(self.btn_delete_site)

        splitter.addWidget(left)

        # ── Right: field editor ───────────────────────────────────────────────
        self.right_stack = QStackedWidget()

        # Empty state
        empty = QLabel("Select a site from the list,\nor click  +  to add one.")
        empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty.setStyleSheet("color: palette(mid); font-size:10pt;")
        self.right_stack.addWidget(empty)   # index 0

        # Editor form (index 1)
        editor_wrapper = QWidget()
        ev = QVBoxLayout(editor_wrapper)
        ev.setContentsMargins(0, 0, 0, 0)
        ev.setSpacing(0)

        editor_header = QWidget()
        editor_header.setObjectName("dialog_header")
        eh = QHBoxLayout(editor_header)
        eh.setContentsMargins(14, 8, 14, 8)
        self.editor_title = QLabel("Site overrides")
        self.editor_title.setStyleSheet("font-weight:bold; font-size:10pt;")
        eh.addWidget(self.editor_title, stretch=1)
        btn_save = QPushButton("Save overrides")
        btn_save.setObjectName("btn_download")
        btn_save.setFixedHeight(26)
        btn_save.clicked.connect(self._on_save)
        eh.addWidget(btn_save)
        btn_clear = QPushButton("Clear all")
        btn_clear.setFixedHeight(26)
        btn_clear.clicked.connect(self._on_clear)
        eh.addWidget(btn_clear)
        ev.addWidget(editor_header)

        form_container = QWidget()
        form = QFormLayout(form_container)
        form.setContentsMargins(16, 14, 16, 14)
        form.setVerticalSpacing(10)
        form.setHorizontalSpacing(14)

        self._field_widgets: dict[str, QWidget] = {}

        for field in OVERRIDABLE_FIELDS:
            label = _FIELD_LABELS.get(field, field)
            widget = self._make_widget(field)
            self._field_widgets[field] = widget
            form.addRow(label, widget)

        ev.addWidget(form_container, stretch=1)
        self.right_stack.addWidget(editor_wrapper)   # index 1

        splitter.addWidget(self.right_stack)
        splitter.setStretchFactor(1, 1)

        layout.addWidget(splitter, stretch=1)

    def _make_widget(self, field: str) -> QWidget:
        if field in ("skip_existing", "set_mtime", "write_metadata",
                     "write_tags", "write_info_json"):
            cb = QCheckBox()
            cb.setTristate(True)   # unchecked=not set, partial=True, checked=True... use None trick
            # We use a QCheckBox with a "use default" concept via tristate:
            # Qt.CheckState.PartiallyChecked → "don't override" (no tick, greyed)
            # Qt.CheckState.Unchecked  → override to False
            # Qt.CheckState.Checked    → override to True
            cb.setCheckState(Qt.CheckState.PartiallyChecked)
            cb.setToolTip(
                "Greyed = don't override (use job/preset value)\n"
                "Unchecked = force OFF\n"
                "Checked = force ON"
            )
            return cb
        elif field == "retries":
            sb = QSpinBox()
            sb.setRange(-1, 20)
            sb.setSpecialValueText("— don't override —")
            sb.setValue(-1)
            return sb
        elif field == "timeout":
            sb = QDoubleSpinBox()
            sb.setRange(-1, 300)
            sb.setSpecialValueText("— don't override —")
            sb.setValue(-1)
            sb.setSuffix(" s")
            return sb
        elif field == "cookies_from_browser":
            cb = QComboBox()
            cb.addItems(["— don't override —"] + _BROWSERS[1:])
            return cb
        else:
            le = QLineEdit()
            le.setPlaceholderText("Leave blank to not override")
            return le

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _refresh_list(self):
        self.site_list.blockSignals(True)
        current = self.site_list.currentItem()
        current_text = current.text() if current else None
        self.site_list.clear()
        for site in sorted(overrides_mgr.list_overrides().keys()):
            self.site_list.addItem(site)
        # Re-select
        if current_text:
            items = self.site_list.findItems(current_text, Qt.MatchFlag.MatchExactly)
            if items:
                self.site_list.setCurrentItem(items[0])
        self.site_list.blockSignals(False)

    def _load_site(self, site_name: str):
        self._current_site = site_name
        self.editor_title.setText(f"Overrides for  {site_name}")
        override = overrides_mgr.get_override(site_name)

        for field, widget in self._field_widgets.items():
            val = override.get(field)   # None = not set

            if isinstance(widget, QCheckBox):
                if val is None:
                    widget.setCheckState(Qt.CheckState.PartiallyChecked)
                elif val:
                    widget.setCheckState(Qt.CheckState.Checked)
                else:
                    widget.setCheckState(Qt.CheckState.Unchecked)

            elif isinstance(widget, QSpinBox):
                widget.setValue(val if val is not None else -1)

            elif isinstance(widget, QDoubleSpinBox):
                widget.setValue(val if val is not None else -1.0)

            elif isinstance(widget, QComboBox):
                text = val if val else "— don't override —"
                idx = widget.findText(text)
                widget.setCurrentIndex(max(0, idx))

            else:  # QLineEdit
                widget.setText(val or "")

        self.right_stack.setCurrentIndex(1)
        self.btn_delete_site.setEnabled(True)

    def _collect_overrides(self) -> dict:
        result = {}
        for field, widget in self._field_widgets.items():
            if isinstance(widget, QCheckBox):
                state = widget.checkState()
                if state == Qt.CheckState.PartiallyChecked:
                    continue   # not overriding
                result[field] = (state == Qt.CheckState.Checked)

            elif isinstance(widget, QSpinBox):
                if widget.value() >= 0:
                    result[field] = widget.value()

            elif isinstance(widget, QDoubleSpinBox):
                if widget.value() >= 0:
                    result[field] = widget.value()

            elif isinstance(widget, QComboBox):
                val = widget.currentText()
                if not val.startswith("—"):
                    result[field] = val

            else:  # QLineEdit
                val = widget.text().strip()
                if val:
                    result[field] = val

        return result

    # ── Slots ─────────────────────────────────────────────────────────────────

    @pyqtSlot(str)
    def _on_site_selected(self, site_name: str):
        if site_name:
            self._load_site(site_name)
        else:
            self.right_stack.setCurrentIndex(0)
            self.btn_delete_site.setEnabled(False)

    @pyqtSlot()
    def _on_add_site(self):
        from PyQt6.QtWidgets import QInputDialog
        # Build site name list from url_detector for convenience
        try:
            from core.url_detector import _PATTERNS
            # _PATTERNS tuples: (pattern, name, url, capabilities, auth, filename)
            # index 1 is the human-readable site name
            known = sorted({p[1] for p in _PATTERNS})
        except Exception:
            known = []

        site, ok = QInputDialog.getItem(
            self, "Add site override",
            "Select a site (or type any name):",
            known, editable=True
        )
        if not ok or not site.strip():
            return
        site = site.strip()
        # Create a blank entry so it appears in the list
        overrides_mgr.set_override(site, {})
        self._refresh_list()
        # Select it
        items = self.site_list.findItems(site, Qt.MatchFlag.MatchExactly)
        if items:
            self.site_list.setCurrentItem(items[0])

    @pyqtSlot()
    def _on_delete_site(self):
        if not self._current_site:
            return
        resp = QMessageBox.question(
            self, "Remove site override",
            f"Remove all overrides for  {self._current_site}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if resp == QMessageBox.StandardButton.Yes:
            overrides_mgr.delete_override(self._current_site)
            self._current_site = None
            self.right_stack.setCurrentIndex(0)
            self.btn_delete_site.setEnabled(False)
            self._refresh_list()

    @pyqtSlot()
    def _on_save(self):
        if not self._current_site:
            return
        data = self._collect_overrides()
        overrides_mgr.set_override(self._current_site, data)
        self._refresh_list()
        # Brief visual confirmation without a modal
        self.editor_title.setText(f"Overrides for  {self._current_site}  ✓ saved")

    @pyqtSlot()
    def _on_clear(self):
        """Reset all fields to 'don't override' without saving."""
        for field, widget in self._field_widgets.items():
            if isinstance(widget, QCheckBox):
                widget.setCheckState(Qt.CheckState.PartiallyChecked)
            elif isinstance(widget, QSpinBox):
                widget.setValue(-1)
            elif isinstance(widget, QDoubleSpinBox):
                widget.setValue(-1.0)
            elif isinstance(widget, QComboBox):
                widget.setCurrentIndex(0)
            else:
                widget.clear()
