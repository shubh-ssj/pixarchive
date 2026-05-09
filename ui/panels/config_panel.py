import json
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QFormLayout, QLineEdit, QSpinBox, QDoubleSpinBox,
    QCheckBox, QComboBox, QPlainTextEdit, QFileDialog, QMessageBox,
    QScrollArea, QFrame, QGroupBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


# ── Config schema validator ──────────────────────────────────────────────────

# Known top-level gallery-dl config keys with their expected value types.
# This isn't exhaustive but catches the most common typos/mistakes.
_KNOWN_EXTRACTOR_KEYS = {
    "base-directory", "filename", "directory", "skip", "sleep", "sleep-request",
    "retries", "timeout", "verify", "proxies", "user-agent", "browser",
    "cookies", "cookies-update", "archive", "archive-format", "archive-prefix",
    "archive-suffix", "archive-pragma", "path-restrict", "path-remove",
    "path-strip", "extension-map", "postprocessors", "filter", "image-filter",
    "range", "skip-filter", "chapter-filter", "chapter-range",
}
_KNOWN_DOWNLOADER_KEYS = {"http", "ytdl", "text"}
_KNOWN_HTTP_KEYS = {
    "rate", "retries", "timeout", "verify", "mtime", "adjust-extensions",
    "headers", "proxies", "user-agent",
}
_KNOWN_OUTPUT_KEYS = {"mode", "progress", "shorten", "colors", "skip", "log", "logfile", "unsupportedfile"}


def _validate_config(cfg: dict) -> list[str]:
    """Return a list of warning strings, empty if all looks good."""
    warnings = []
    if not isinstance(cfg, dict):
        return ["Config root must be a JSON object."]

    known_top = {"extractor", "downloader", "output", "cache", "netrc"}
    for key in cfg:
        if key not in known_top:
            warnings.append(f"Unknown top-level key: '{key}' (expected one of: {', '.join(sorted(known_top))})")

    ext = cfg.get("extractor", {})
    if not isinstance(ext, dict):
        warnings.append("'extractor' must be a JSON object.")
    else:
        for k in ext:
            if k not in _KNOWN_EXTRACTOR_KEYS and not k.startswith("#"):
                # Could be a site-specific override like "pixiv" — allow nested dicts
                if not isinstance(ext[k], dict):
                    warnings.append(f"extractor.{k}: unrecognised key (check spelling)")

    dl = cfg.get("downloader", {})
    if not isinstance(dl, dict):
        warnings.append("'downloader' must be a JSON object.")
    else:
        http = dl.get("http", {})
        if isinstance(http, dict):
            for k in http:
                if k not in _KNOWN_HTTP_KEYS:
                    warnings.append(f"downloader.http.{k}: unrecognised key")

    out = cfg.get("output", {})
    if not isinstance(out, dict):
        warnings.append("'output' must be a JSON object.")
    else:
        for k in out:
            if k not in _KNOWN_OUTPUT_KEYS:
                warnings.append(f"output.{k}: unrecognised key")

    return warnings


def _config_path() -> str:
    if os.name == "nt":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
        return os.path.join(base, "gallery-dl", "config.json")
    return os.path.join(os.path.expanduser("~"), ".config", "gallery-dl", "config.json")


class ConfigPanel(QWidget):
    def __init__(self):
        super().__init__()
        self._config: dict = {}
        self._build_ui()
        self._load_config()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Toolbar
        toolbar = QWidget()
        toolbar.setStyleSheet("background: palette(base); border-bottom: 1px solid palette(midlight);")
        tb = QHBoxLayout(toolbar)
        tb.setContentsMargins(12, 10, 12, 10)
        tb.setSpacing(8)

        title = QLabel("Configuration")
        title.setStyleSheet("font-weight:bold; font-size:11pt; color: palette(link);")
        tb.addWidget(title)

        self.path_lbl = QLabel(_config_path())
        self.path_lbl.setStyleSheet("color: palette(mid); font-size:8pt;")
        self.path_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        tb.addWidget(self.path_lbl)
        tb.addStretch()

        btn_open = QPushButton("Open config file")
        btn_open.setFixedHeight(28)
        btn_open.clicked.connect(self._open_file)
        tb.addWidget(btn_open)

        btn_reload = QPushButton("Reload")
        btn_reload.setFixedHeight(28)
        btn_reload.clicked.connect(self._load_config)
        tb.addWidget(btn_reload)

        btn_validate = QPushButton("Validate")
        btn_validate.setFixedHeight(28)
        btn_validate.setToolTip("Check config for common mistakes without saving")
        btn_validate.clicked.connect(self._validate_only)
        tb.addWidget(btn_validate)

        btn_save = QPushButton("Save")
        btn_save.setObjectName("btn_download")
        btn_save.setFixedHeight(28)
        btn_save.clicked.connect(self._save_config)
        tb.addWidget(btn_save)

        layout.addWidget(toolbar)

        # Tabs: GUI form + per-site overrides + raw JSON editor
        tabs = QTabWidget()
        tabs.setDocumentMode(True)
        tabs.addTab(self._build_form_tab(),      "Common Settings")
        tabs.addTab(self._build_overrides_tab(), "Per-site Overrides")
        tabs.addTab(self._build_raw_tab(),       "Raw JSON")
        layout.addWidget(tabs, stretch=1)

    # ── Form tab ─────────────────────────────────────────────────────────────

    def _build_form_tab(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget()
        vbox = QVBoxLayout(container)
        vbox.setContentsMargins(16, 12, 16, 12)
        vbox.setSpacing(16)

        # ── Extractor defaults ────────────────────────────────────────────────
        ext_box = QGroupBox("EXTRACTOR DEFAULTS")
        ext_form = QFormLayout(ext_box)
        ext_form.setVerticalSpacing(8)
        ext_form.setHorizontalSpacing(14)

        self.cfg_base_dir = QLineEdit()
        self.cfg_base_dir.setPlaceholderText("e.g. ~/Downloads/gallery-dl")
        ext_form.addRow("Base directory", self.cfg_base_dir)

        self.cfg_filename = QLineEdit()
        self.cfg_filename.setPlaceholderText("{filename}.{extension}")
        ext_form.addRow("Filename pattern", self.cfg_filename)

        self.cfg_sleep = QDoubleSpinBox()
        self.cfg_sleep.setRange(0, 60)
        self.cfg_sleep.setSingleStep(0.5)
        self.cfg_sleep.setSuffix(" s")
        ext_form.addRow("Sleep between requests", self.cfg_sleep)

        self.cfg_retries = QSpinBox()
        self.cfg_retries.setRange(0, 20)
        self.cfg_retries.setValue(4)
        ext_form.addRow("Retries", self.cfg_retries)

        self.cfg_skip = QCheckBox("Skip already-downloaded files")
        self.cfg_skip.setChecked(True)
        ext_form.addRow("", self.cfg_skip)

        self.cfg_write_metadata = QCheckBox("Write metadata .json files")
        ext_form.addRow("", self.cfg_write_metadata)

        self.cfg_write_info = QCheckBox("Write info.json per gallery")
        ext_form.addRow("", self.cfg_write_info)

        vbox.addWidget(ext_box)

        # ── Downloader settings ───────────────────────────────────────────────
        dl_box = QGroupBox("DOWNLOADER")
        dl_form = QFormLayout(dl_box)
        dl_form.setVerticalSpacing(8)
        dl_form.setHorizontalSpacing(14)

        self.cfg_rate = QLineEdit()
        self.cfg_rate.setPlaceholderText("e.g. 500k, 2M")
        dl_form.addRow("Rate limit (bytes/s)", self.cfg_rate)

        self.cfg_timeout = QDoubleSpinBox()
        self.cfg_timeout.setRange(0, 120)
        self.cfg_timeout.setValue(30)
        self.cfg_timeout.setSuffix(" s")
        dl_form.addRow("HTTP timeout", self.cfg_timeout)

        self.cfg_retries_dl = QSpinBox()
        self.cfg_retries_dl.setRange(0, 20)
        self.cfg_retries_dl.setValue(4)
        dl_form.addRow("Retries", self.cfg_retries_dl)

        vbox.addWidget(dl_box)

        # ── Output / Postprocessing ────────────────────────────────────────────
        pp_box = QGroupBox("POSTPROCESSORS")
        pp_form = QFormLayout(pp_box)
        pp_form.setVerticalSpacing(8)
        pp_form.setHorizontalSpacing(14)

        self.cfg_ugoira = QComboBox()
        self.cfg_ugoira.addItems(["webm", "mp4", "gif", "zip (raw frames)"])
        pp_form.addRow("Pixiv ugoira format", self.cfg_ugoira)

        self.cfg_archive = QLineEdit()
        self.cfg_archive.setPlaceholderText("Path to archive SQLite DB (avoid re-downloads)")
        btn_arc_browse = QPushButton("Browse…")
        btn_arc_browse.clicked.connect(
            lambda: self.cfg_archive.setText(
                QFileDialog.getSaveFileName(self, "Archive DB", filter="SQLite (*.db)")[0]
            )
        )
        row = QHBoxLayout()
        row.addWidget(self.cfg_archive)
        row.addWidget(btn_arc_browse)
        pp_form.addRow("Archive DB", row)

        vbox.addWidget(pp_box)
        vbox.addStretch()

        scroll.setWidget(container)
        return scroll

    # ── Per-site overrides tab ───────────────────────────────────────────────

    def _build_overrides_tab(self) -> QWidget:
        from ui.panels.site_overrides_widget import SiteOverridesWidget
        return SiteOverridesWidget()

    # ── Raw JSON tab ──────────────────────────────────────────────────────────

    def _build_raw_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        info = QLabel(
            "  Direct JSON editor. Changes here override the form above when saved."
        )
        info.setStyleSheet("background: palette(alternateBase); color: palette(mid); font-size:8pt; padding:6px 12px;")
        layout.addWidget(info)

        self.raw_editor = QPlainTextEdit()
        self.raw_editor.setFont(QFont("Consolas", 10))
        self.raw_editor.setStyleSheet(
            "background: palette(base); color: palette(text); border: 1px solid palette(mid);"
            "font-family:'Consolas','Cascadia Code',monospace; font-size:10pt; padding:8px;"
        )
        layout.addWidget(self.raw_editor, stretch=1)
        return w

    # ── Config I/O ────────────────────────────────────────────────────────────

    def _load_config(self):
        path = _config_path()
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    self._config = json.load(f)
            except Exception as e:
                QMessageBox.warning(self, "Load error", f"Could not parse config:\n{e}")
                self._config = {}
        else:
            self._config = {}

        self._populate_form()
        self.raw_editor.setPlainText(json.dumps(self._config, indent=2))

    def _populate_form(self):
        ext = self._config.get("extractor", {})
        dl  = self._config.get("downloader", {}).get("http", {})

        self.cfg_base_dir.setText(str(ext.get("base-directory", "")))
        self.cfg_filename.setText(str(ext.get("filename", "")))
        self.cfg_sleep.setValue(float(ext.get("sleep", 0)))
        self.cfg_retries.setValue(int(ext.get("retries", 4)))
        self.cfg_skip.setChecked(bool(ext.get("skip", True)))
        self.cfg_write_metadata.setChecked(bool(ext.get("postprocessors", [{}])[0].get("name") == "metadata" if ext.get("postprocessors") else False))

        self.cfg_rate.setText(str(dl.get("rate", "")))
        self.cfg_timeout.setValue(float(dl.get("timeout", 30)))
        self.cfg_retries_dl.setValue(int(dl.get("retries", 4)))

    def _save_config(self):
        # Prefer raw editor if it's been modified
        raw_text = self.raw_editor.toPlainText().strip()
        if raw_text:
            try:
                cfg = json.loads(raw_text)
            except json.JSONDecodeError as e:
                QMessageBox.critical(self, "JSON error", f"Invalid JSON:\n{e}")
                return
        else:
            cfg = self._build_config_from_form()

        # ── Validate ─────────────────────────────────────────────────────────
        issues = _validate_config(cfg)
        if issues:
            bullet_list = "\n".join(f"  • {w}" for w in issues)
            resp = QMessageBox.warning(
                self, "Config warnings",
                f"The following potential issues were found:\n\n{bullet_list}\n\n"
                "Save anyway?",
                QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Cancel,
            )
            if resp != QMessageBox.StandardButton.Save:
                return

        path = _config_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(cfg, f, indent=2)
            self._config = cfg
            self.raw_editor.setPlainText(json.dumps(cfg, indent=2))
            QMessageBox.information(self, "Saved", f"Config saved to:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Save error", str(e))

    def _build_config_from_form(self) -> dict:
        cfg: dict = dict(self._config)  # preserve existing keys

        ext = cfg.setdefault("extractor", {})
        if self.cfg_base_dir.text():
            ext["base-directory"] = self.cfg_base_dir.text()
        if self.cfg_filename.text():
            ext["filename"] = self.cfg_filename.text()
        if self.cfg_sleep.value():
            ext["sleep"] = self.cfg_sleep.value()
        ext["retries"] = self.cfg_retries.value()
        ext["skip"] = self.cfg_skip.isChecked()

        dl = cfg.setdefault("downloader", {}).setdefault("http", {})
        if self.cfg_rate.text():
            dl["rate"] = self.cfg_rate.text()
        dl["timeout"] = self.cfg_timeout.value()
        dl["retries"] = self.cfg_retries_dl.value()

        if self.cfg_archive.text():
            cfg.setdefault("extractor", {})["archive"] = self.cfg_archive.text()

        return cfg

    def _validate_only(self):
        raw_text = self.raw_editor.toPlainText().strip()
        if raw_text:
            try:
                cfg = json.loads(raw_text)
            except json.JSONDecodeError as e:
                QMessageBox.critical(self, "JSON error", f"Invalid JSON:\n{e}")
                return
        else:
            cfg = self._build_config_from_form()
        issues = _validate_config(cfg)
        if issues:
            bullet_list = "\n".join(f"  • {w}" for w in issues)
            QMessageBox.warning(self, "Config warnings",
                f"Potential issues found:\n\n{bullet_list}")
        else:
            QMessageBox.information(self, "Config looks good",
                "No obvious issues found in your configuration.")

    def _open_file(self):
        path = _config_path()
        if os.name == "nt":
            os.startfile(path)
        else:
            os.system(f'xdg-open "{path}"')
