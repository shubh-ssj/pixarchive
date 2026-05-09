from __future__ import annotations
import html

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QTabWidget, QFormLayout, QLabel, QCheckBox,
    QSpinBox, QDoubleSpinBox, QComboBox, QPlainTextEdit,
    QFileDialog, QSplitter, QSizePolicy, QInputDialog, QMessageBox,
    QFrame, QMenu, QButtonGroup
)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot, QTimer, QMimeData
from PyQt6.QtGui import QTextCursor, QDragEnterEvent, QDropEvent, QAction

from core.download_manager import DownloadManager
from core.options import DownloadOptions
from core.url_detector import detect_site, SiteMatch, AUTH_LABELS
from core import presets as preset_mgr
from core.app_settings import get_settings


class DownloadPanel(QWidget):
    """Main download panel: URL input, site detection, options, presets, live log."""

    queued = pyqtSignal()

    def __init__(self, manager: DownloadManager):
        super().__init__()
        self.manager = manager
        self.setAcceptDrops(True)
        self._url_check_timer = QTimer()
        self._url_check_timer.setSingleShot(True)
        self._url_check_timer.setInterval(350)   # debounce ms
        self._build_ui()
        self._connect_signals()
        self._load_preset_list()
        self._apply_settings_defaults()   # FIX #5

    # ── UI ───────────────────────────────────────────────────────────────────

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self._build_url_bar())
        layout.addWidget(self._build_site_banner())   # collapsible site info

        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setHandleWidth(1)
        splitter.addWidget(self._build_options())
        splitter.addWidget(self._build_log_area())
        splitter.setSizes([400, 200])
        layout.addWidget(splitter, stretch=1)

    # ── URL bar ──────────────────────────────────────────────────────────────

    def _build_url_bar(self) -> QWidget:
        container = QWidget()
        container.setObjectName("dialog_header")
        outer = QVBoxLayout(container)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Single-URL row
        self._single_bar = QWidget()
        layout = QHBoxLayout(self._single_bar)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Paste or drop a gallery / image URL here…")
        self.url_input.setMinimumHeight(34)
        layout.addWidget(self.url_input, stretch=1)

        self.btn_paste = QPushButton("Paste")
        self.btn_paste.setMinimumHeight(34)
        self.btn_paste.setToolTip("Paste URL from clipboard")
        layout.addWidget(self.btn_paste)

        self.btn_multi = QPushButton("Multi-URL")
        self.btn_multi.setMinimumHeight(34)
        self.btn_multi.setToolTip("Switch to multi-URL batch input")
        self.btn_multi.setCheckable(True)
        layout.addWidget(self.btn_multi)

        self.btn_queue = QPushButton("+ Queue")
        self.btn_queue.setMinimumHeight(34)
        layout.addWidget(self.btn_queue)

        self.btn_download = QPushButton("Download Now")
        self.btn_download.setObjectName("btn_download")
        self.btn_download.setMinimumHeight(34)
        layout.addWidget(self.btn_download)

        self.btn_stop = QPushButton("Stop")
        self.btn_stop.setObjectName("btn_stop")
        self.btn_stop.setMinimumHeight(34)
        self.btn_stop.setEnabled(False)
        layout.addWidget(self.btn_stop)

        outer.addWidget(self._single_bar)

        # Multi-URL panel (hidden by default)
        self._multi_bar = QWidget()
        ml = QVBoxLayout(self._multi_bar)
        ml.setContentsMargins(12, 8, 12, 8)
        ml.setSpacing(6)

        multi_hint = QLabel(
            "One URL per line. Blank lines and # comments are ignored. "
            "Drag and drop a .txt file to load it directly."
        )
        multi_hint.setStyleSheet("color: palette(mid); font-size:8pt;")
        multi_hint.setWordWrap(True)
        ml.addWidget(multi_hint)

        self.url_multi_input = QPlainTextEdit()
        self.url_multi_input.setPlaceholderText(
            "https://www.pixiv.net/en/users/12345\n"
            "https://www.deviantart.com/someartist\n"
            "https://reddit.com/r/art/…"
        )
        self.url_multi_input.setFixedHeight(90)
        ml.addWidget(self.url_multi_input)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        self.btn_multi_paste = QPushButton("Paste all")
        self.btn_multi_paste.setFixedHeight(28)
        self.btn_multi_paste.clicked.connect(self._multi_paste)
        btn_row.addWidget(self.btn_multi_paste)

        self.btn_import_file = QPushButton("Import from file…")
        self.btn_import_file.setFixedHeight(28)
        self.btn_import_file.setToolTip(
            "Load URLs from a .txt or .csv file (one URL per line).\n"
            "You can also drag and drop a file onto this panel."
        )
        self.btn_import_file.clicked.connect(self._import_urls_from_file)
        btn_row.addWidget(self.btn_import_file)

        btn_row.addStretch()

        self.btn_multi_queue = QPushButton("Queue all URLs")
        self.btn_multi_queue.setObjectName("btn_download")
        self.btn_multi_queue.setFixedHeight(28)
        self.btn_multi_queue.clicked.connect(self._queue_multi)
        btn_row.addWidget(self.btn_multi_queue)

        ml.addLayout(btn_row)
        self._multi_bar.setVisible(False)
        outer.addWidget(self._multi_bar)

        # Per-job folder override strip
        self._folder_bar = QWidget()
        self._folder_bar.setObjectName("dialog_header")
        fl = QHBoxLayout(self._folder_bar)
        fl.setContentsMargins(12, 5, 12, 5)
        fl.setSpacing(8)

        folder_icon = QLabel("\U0001f4c1")
        folder_icon.setStyleSheet("font-size:10pt;")
        fl.addWidget(folder_icon)

        self._folder_label = QLabel("Saving to default folder")
        self._folder_label.setStyleSheet("color: palette(mid); font-size:8pt;")
        self._folder_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        fl.addWidget(self._folder_label, stretch=1)

        self._btn_folder_change = QPushButton("Save to\u2026")
        self._btn_folder_change.setFixedHeight(22)
        self._btn_folder_change.setToolTip(
            "Override the save folder for this job only.\n"
            "Does not affect your global default setting."
        )
        self._btn_folder_change.clicked.connect(self._pick_job_folder)
        fl.addWidget(self._btn_folder_change)

        self._btn_folder_clear = QPushButton("\u2715")
        self._btn_folder_clear.setFixedSize(22, 22)
        self._btn_folder_clear.setToolTip("Reset to default save folder")
        self._btn_folder_clear.setVisible(False)
        self._btn_folder_clear.clicked.connect(self._clear_job_folder)
        fl.addWidget(self._btn_folder_clear)

        outer.addWidget(self._folder_bar)

        self._job_output_dir = None   # None = use global default

        return container

    # ── Site detection banner ─────────────────────────────────────────────────

    def _build_site_banner(self) -> QWidget:
        self.banner = QWidget()
        self.banner.setVisible(False)
        self.banner.setObjectName("dialog_header")
        layout = QHBoxLayout(self.banner)
        layout.setContentsMargins(14, 7, 14, 7)
        layout.setSpacing(10)

        self.banner_icon = QLabel("◈")
        self.banner_icon.setStyleSheet("color: palette(highlight); font-size:14pt;")
        layout.addWidget(self.banner_icon)

        info_col = QVBoxLayout()
        info_col.setSpacing(1)
        self.banner_site = QLabel()
        self.banner_site.setStyleSheet("font-weight:bold; font-size:10pt;")
        info_col.addWidget(self.banner_site)
        self.banner_caps = QLabel()
        self.banner_caps.setStyleSheet("color: palette(mid); font-size:8pt;")
        info_col.addWidget(self.banner_caps)
        layout.addLayout(info_col, stretch=1)

        self.banner_auth = QLabel()
        self.banner_auth.setStyleSheet("border-radius:4px; padding:2px 8px; font-size:8pt; font-weight:bold;")
        layout.addWidget(self.banner_auth)

        self.banner_cat = QLabel()
        self.banner_cat.setStyleSheet("color: palette(mid); font-size:8pt;")
        layout.addWidget(self.banner_cat)

        return self.banner

    # ── Options tabs ─────────────────────────────────────────────────────────

    def _build_options(self) -> QWidget:
        container = QWidget()
        vbox = QVBoxLayout(container)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(0)

        # Preset toolbar
        vbox.addWidget(self._build_preset_bar())

        tabs = QTabWidget()
        tabs.setDocumentMode(True)
        tabs.addTab(self._tab_output(),    "Output")
        tabs.addTab(self._tab_filters(),   "Filters")
        tabs.addTab(self._tab_behaviour(), "Behaviour")
        tabs.addTab(self._tab_network(),   "Network")
        vbox.addWidget(tabs, stretch=1)

        return container

    def _build_preset_bar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("dialog_header")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(8)

        lbl = QLabel("Preset:")
        lbl.setStyleSheet("color: palette(mid); font-size:9pt;")
        layout.addWidget(lbl)

        self.preset_combo = QComboBox()
        self.preset_combo.setFixedHeight(26)
        self.preset_combo.setMinimumWidth(220)
        layout.addWidget(self.preset_combo)

        self.btn_load_preset = QPushButton("Load")
        self.btn_load_preset.setFixedHeight(26)
        self.btn_load_preset.setStyleSheet("font-size:8pt; padding:0 10px;")
        layout.addWidget(self.btn_load_preset)

        self.btn_save_preset = QPushButton("Save current…")
        self.btn_save_preset.setFixedHeight(26)
        self.btn_save_preset.setStyleSheet("font-size:8pt; padding:0 10px;")
        layout.addWidget(self.btn_save_preset)

        self.btn_delete_preset = QPushButton("Delete")
        self.btn_delete_preset.setFixedHeight(26)
        self.btn_delete_preset.setStyleSheet(
            "font-size:8pt; padding:0 10px; color: palette(bright-text);"
        )
        layout.addWidget(self.btn_delete_preset)

        layout.addStretch()

        self.btn_reset = QPushButton("Reset to defaults")
        self.btn_reset.setFixedHeight(26)
        self.btn_reset.setStyleSheet("font-size:8pt; padding:0 10px; color: palette(mid);")
        layout.addWidget(self.btn_reset)

        return bar

    def _tab_output(self) -> QWidget:
        w = QWidget()
        form = QFormLayout(w)
        form.setContentsMargins(16, 14, 16, 14)
        form.setVerticalSpacing(10)
        form.setHorizontalSpacing(14)

        self.out_dir = QLineEdit()
        self.out_dir.setPlaceholderText("~/Downloads/gallery-dl  (leave blank for config default)")
        self.out_dir.setToolTip(
            "Root folder where files are saved.\n"
            "Leave blank to use the base-directory in your gallery-dl config file.\n"
            "Supports ~ for your home directory."
        )
        btn_browse = QPushButton("Browse…")
        btn_browse.clicked.connect(self._browse_output_dir)
        row = QHBoxLayout()
        row.addWidget(self.out_dir)
        row.addWidget(btn_browse)
        form.addRow("Save directory", row)

        self.filename_pattern = QLineEdit()
        self.filename_pattern.setPlaceholderText("{extractor[category]}/{title}/{filename}.{extension}")
        self.filename_pattern.setToolTip(
            "gallery-dl format string. Available keys depend on the extractor.\n"
            "Common tokens:\n"
            "  {filename}      original filename\n"
            "  {extension}     file extension\n"
            "  {category}      site name (e.g. pixiv)\n"
            "  {subcategory}   e.g. 'user', 'tag'\n"
            "  {id}            item ID\n"
            "  {title}         gallery/post title\n"
            "  {date:%Y-%m-%d} formatted date\n"
            "  {num}           sequence number (e.g. for manga pages)"
        )
        form.addRow("Filename pattern", self.filename_pattern)

        self.zip_check = QCheckBox("Pack downloads into a .zip archive")
        self.zip_check.setToolTip(
            "gallery-dl --zip\n"
            "All downloaded files are stored inside a single .zip archive\n"
            "instead of as individual files on disk."
        )
        form.addRow("", self.zip_check)

        self.mtime_check = QCheckBox("Set file modification time from metadata")
        self.mtime_check.setToolTip(
            "gallery-dl --mtime\n"
            "Sets each file's last-modified timestamp to the date the post\n"
            "was originally published, rather than the current download time."
        )
        form.addRow("", self.mtime_check)

        return w

    def _tab_filters(self) -> QWidget:
        w = QWidget()
        form = QFormLayout(w)
        form.setContentsMargins(16, 14, 16, 14)
        form.setVerticalSpacing(10)
        form.setHorizontalSpacing(14)

        self.filter_expr = QLineEdit()
        self.filter_expr.setPlaceholderText('e.g.  width >= 1920 and "landscape" in tags')
        self.filter_expr.setToolTip(
            "Python expression evaluated against each item's metadata.\n"
            "Examples:\n"
            "  width >= 1920\n"
            '  extension in ("jpg", "png")\n'
            '  "scenery" in tags and score > 100\n'
            "  date > datetime(2023, 1, 1)"
        )
        form.addRow("Item filter", self.filter_expr)

        self.image_filter = QLineEdit()
        self.image_filter.setPlaceholderText("e.g.  width > 500 or extension == 'gif'")
        self.image_filter.setToolTip(
            "Like item filter but applied to each individual image.\n"
            "Useful when a post has multiple images."
        )
        form.addRow("Image filter", self.image_filter)

        self.range_input = QLineEdit()
        self.range_input.setPlaceholderText("e.g.  1-20   or   1,5,10-15")
        self.range_input.setToolTip("Download only items at these 1-based indices.")
        form.addRow("Index range", self.range_input)

        self.chapter_range = QLineEdit()
        self.chapter_range.setPlaceholderText("e.g.  1-5   (for manga / chapter extractors)")
        self.chapter_range.setToolTip(
            "gallery-dl --chapter-range\n"
            "Download only the specified chapters. Uses 1-based indexing.\n"
            "Example: 1-3 downloads chapters 1, 2 and 3."
        )
        form.addRow("Chapter range", self.chapter_range)

        form.addRow(QLabel(""))   # spacer

        help_lbl = QLabel(
            "<b>Tip:</b> Filter expressions use Python syntax and can reference any metadata key "
            "that gallery-dl exposes for the extractor. Use <code>--verbose</code> on the command "
            "line first to inspect available keys."
        )
        help_lbl.setWordWrap(True)
        help_lbl.setStyleSheet("color: palette(mid); font-size:8pt;")
        help_lbl.setTextFormat(Qt.TextFormat.RichText)
        form.addRow(help_lbl)

        return w

    def _tab_behaviour(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        def _section(text):
            lbl = QLabel(text.upper())
            lbl.setStyleSheet("color: palette(mid); font-size:8pt; font-weight:bold; letter-spacing:1px; margin-top:6px;")
            layout.addWidget(lbl)

        _section("Files")
        self.skip_existing = QCheckBox("Skip files that already exist  (recommended)")
        self.skip_existing.setChecked(True)
        self.skip_existing.setToolTip(
            "gallery-dl --skip\n"
            "If a file with the same name already exists on disk, skip it\n"
            "instead of re-downloading. Highly recommended for large galleries."
        )
        layout.addWidget(self.skip_existing)

        _section("Metadata")
        self.write_metadata  = QCheckBox("Write item metadata alongside each file  (.json)")
        self.write_metadata.setToolTip(
            "gallery-dl --write-metadata\n"
            "Saves a .json sidecar next to each downloaded file containing\n"
            "all metadata gallery-dl collected (tags, IDs, dates, etc.)."
        )
        self.write_tags      = QCheckBox("Write tags to XMP/EXIF sidecar")
        self.write_tags.setToolTip(
            "gallery-dl --write-tags\n"
            "Embeds tags into the file's XMP/EXIF metadata where supported."
        )
        self.write_info_json = QCheckBox("Write gallery info to info.json")
        self.write_info_json.setToolTip(
            "gallery-dl --write-info-json\n"
            "Writes a single info.json file per gallery/album describing\n"
            "the whole collection (title, uploader, URL, item count, etc.)."
        )
        for cb in (self.write_metadata, self.write_tags, self.write_info_json):
            layout.addWidget(cb)

        _section("Behaviour")
        self.dry_run = QCheckBox("Simulate only — list what would be downloaded, do not write files  (dry run)")
        self.dry_run.setToolTip(
            "gallery-dl --simulate\n"
            "Runs the extractor and prints what would be downloaded\n"
            "without actually saving any files. Great for testing filters."
        )
        self.verbose = QCheckBox("Verbose log output  (shows every request gallery-dl makes)")
        self.verbose.setToolTip(
            "gallery-dl --verbose\n"
            "Prints detailed debug information including every HTTP request.\n"
            "Useful for diagnosing extraction problems or discovering metadata keys."
        )
        for cb in (self.dry_run, self.verbose):
            layout.addWidget(cb)

        layout.addStretch()
        return w

    def _tab_network(self) -> QWidget:
        w = QWidget()
        form = QFormLayout(w)
        form.setContentsMargins(16, 14, 16, 14)
        form.setVerticalSpacing(10)
        form.setHorizontalSpacing(14)

        self.retries = QSpinBox()
        self.retries.setRange(0, 20)
        self.retries.setValue(4)
        self.retries.setToolTip("Number of times to retry a failed request before giving up.")
        form.addRow("Retries", self.retries)

        self.timeout = QDoubleSpinBox()
        self.timeout.setRange(0, 300)
        self.timeout.setValue(30.0)
        self.timeout.setSuffix(" s")
        self.timeout.setToolTip("HTTP request timeout in seconds.")
        form.addRow("Timeout", self.timeout)

        self.rate_limit = QLineEdit()
        self.rate_limit.setPlaceholderText("e.g.  500k   or   2M   (bytes/sec)")
        self.rate_limit.setToolTip("Throttle download speed. Use k/M suffixes.")
        form.addRow("Rate limit", self.rate_limit)

        self.cookies_browser = QComboBox()
        self.cookies_browser.addItems(["None", "chrome", "firefox", "edge", "safari", "opera", "brave"])
        self.cookies_browser.setToolTip(
            "Extract cookies from your browser automatically.\n"
            "Useful for sites that require login (Instagram, Patreon, etc.)."
        )
        form.addRow("Cookies from browser", self.cookies_browser)

        self.cookies_file = QLineEdit()
        self.cookies_file.setPlaceholderText("Path to cookies.txt  (Netscape format)")
        self.cookies_file.setToolTip(
            "gallery-dl --cookies <file>\n"
            "Load cookies from a Netscape-format cookies.txt file.\n"
            "Export one using a browser extension like 'Get cookies.txt LOCALLY'.\n"
            "Use this instead of 'Cookies from browser' if auto-extract doesn't work."
        )
        btn_cookie_browse = QPushButton("Browse…")
        btn_cookie_browse.clicked.connect(self._browse_cookie_file)
        row = QHBoxLayout()
        row.addWidget(self.cookies_file)
        row.addWidget(btn_cookie_browse)
        form.addRow("Cookies file", row)

        self.proxy = QLineEdit()
        self.proxy.setPlaceholderText("http://user:pass@host:port")
        self.proxy.setToolTip(
            "gallery-dl --proxy <url>\n"
            "Route all requests through this proxy.\n"
            "Supports http://, https://, and socks5:// schemes.\n"
            "Example: socks5://127.0.0.1:1080"
        )
        form.addRow("Proxy", self.proxy)

        return w

    # ── Log area ─────────────────────────────────────────────────────────────

    def _build_log_area(self) -> QWidget:
        container = QWidget()
        vbox = QVBoxLayout(container)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(0)

        # Log toolbar
        toolbar = QWidget()
        toolbar.setObjectName("dialog_header")
        tbl = QHBoxLayout(toolbar)
        tbl.setContentsMargins(10, 4, 10, 4)
        tbl.setSpacing(8)

        log_title = QLabel("Log")
        log_title.setStyleSheet("color: palette(mid); font-size:9pt; font-weight:bold;")
        tbl.addWidget(log_title)

        # Level filter toggle buttons
        self._log_level_filters: set[str] = {"error", "warning", "info", "debug"}
        self._level_btns: dict[str, QPushButton] = {}

        for level, label in [("error", "Err"), ("warning", "Warn"), ("info", "Info"), ("debug", "Debug")]:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setChecked(True)
            btn.setFixedHeight(22)
            btn.toggled.connect(lambda checked, l=level: self._toggle_level_filter(l, checked))
            self._level_btns[level] = btn
            tbl.addWidget(btn)

        self._refresh_level_btn_styles()

        tbl.addStretch()

        self.log_search = QLineEdit()
        self.log_search.setPlaceholderText("Filter log…")
        self.log_search.setFixedWidth(140)
        self.log_search.setFixedHeight(22)
        self.log_search.textChanged.connect(self._filter_log)
        self.log_search.setStyleSheet("font-size:8pt;")
        tbl.addWidget(self.log_search)

        btn_copy_log = QPushButton("Copy")
        btn_copy_log.setFixedHeight(22)
        btn_copy_log.setStyleSheet("font-size:8pt; padding:0 8px;")
        btn_copy_log.setToolTip("Copy entire log to clipboard")
        btn_copy_log.clicked.connect(self._copy_log)
        tbl.addWidget(btn_copy_log)

        btn_clear_log = QPushButton("Clear")
        btn_clear_log.setFixedHeight(22)
        btn_clear_log.setStyleSheet("font-size:8pt; padding:0 8px;")
        btn_clear_log.clicked.connect(self._clear_log)
        tbl.addWidget(btn_clear_log)

        vbox.addWidget(toolbar)

        self.log_output = QPlainTextEdit()
        self.log_output.setObjectName("log_output")
        self.log_output.setReadOnly(True)
        self.log_output.setMaximumBlockCount(get_settings().get("log_max_lines", 3000))
        self.log_output.setPlaceholderText("Download log will appear here…")
        vbox.addWidget(self.log_output, stretch=1)

        # All raw log lines stored for filtering
        self._log_lines: list[tuple[str, str]] = []   # (level, html_text)

        return container

    # ── Signals / helpers ────────────────────────────────────────────────────

    def _connect_signals(self):
        self.url_input.textChanged.connect(self._on_url_changed)
        self._url_check_timer.timeout.connect(self._run_detection)

        self.btn_paste.clicked.connect(self._paste_clipboard)
        self.btn_download.clicked.connect(self._on_download)
        self.btn_queue.clicked.connect(self._on_queue)
        self.btn_stop.clicked.connect(self._on_stop)
        self.btn_multi.toggled.connect(self._toggle_multi_mode)

        self.btn_load_preset.clicked.connect(self._load_selected_preset)
        self.btn_save_preset.clicked.connect(self._save_preset)
        self.btn_delete_preset.clicked.connect(self._delete_preset)
        self.btn_reset.clicked.connect(self._reset_fields)

    # ── Clipboard & drag-drop ────────────────────────────────────────────────

    # ── Multi-URL mode ───────────────────────────────────────────────────────

    def _toggle_multi_mode(self, on: bool):
        self._single_bar.setVisible(not on)
        self._multi_bar.setVisible(on)
        self.btn_multi.setText("Single URL" if on else "Multi-URL")

    def _multi_paste(self):
        from PyQt6.QtWidgets import QApplication
        text = QApplication.clipboard().text().strip()
        if text:
            self.url_multi_input.setPlainText(text)

    @staticmethod
    def _parse_url_file(path: str) -> list[str]:
        """Delegate to core.utils.parse_url_file — tested independently of Qt."""
        from core.utils import parse_url_file
        return parse_url_file(path)

    def _import_urls_from_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Import URLs from file",
            "",
            "Text / CSV files (*.txt *.csv *.tsv);;All files (*)"
        )
        if not path:
            return
        self._load_url_file(path)

    def _load_url_file(self, path: str):
        """Parse a URL file and append its contents to the multi-URL input."""
        try:
            urls = self._parse_url_file(path)
        except OSError as e:
            QMessageBox.warning(self, "Import failed", str(e))
            return

        if not urls:
            QMessageBox.information(
                self, "No URLs found",
                "No valid http(s) URLs were found in that file.\n\n"
                "Make sure each URL is on its own line and starts with http:// or https://"
            )
            return

        if not self.btn_multi.isChecked():
            self.btn_multi.setChecked(True)

        current = self.url_multi_input.toPlainText().strip()
        new_block = "\n".join(urls)
        combined = (current + "\n" + new_block).strip() if current else new_block
        self.url_multi_input.setPlainText(combined)

        cursor = self.url_multi_input.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.url_multi_input.setTextCursor(cursor)

        self._append_log("info", f"Loaded {len(urls)} URL(s) from {path}")

    def _queue_multi(self):
        text = self.url_multi_input.toPlainText()
        urls = [l.strip() for l in text.splitlines() if l.strip().startswith("http")]
        if not urls:
            self._append_log("warning", "No valid URLs found (each must start with http).")
            return
        opts = self._build_options_obj()
        queued = []
        skipped = []
        for url in urls:
            if self._is_duplicate(url):
                skipped.append(url)
                continue
            self.manager.enqueue(url, opts)
            queued.append(url)
        self.url_multi_input.clear()
        if queued:
            self._append_log("info", f"Queued {len(queued)} URL(s).")
            self.queued.emit()
        if skipped:
            self._append_log("warning", f"Skipped {len(skipped)} duplicate(s).")

    # ── Deduplication ─────────────────────────────────────────────────────────

    def _is_duplicate(self, url: str) -> bool:
        """Return True if url is already queued or running."""
        from core.job import JobStatus
        for job in self.manager.jobs:
            if job.url == url and job.status in (JobStatus.QUEUED, JobStatus.RUNNING):
                return True
        return False

    def _paste_clipboard(self):
        from PyQt6.QtWidgets import QApplication
        text = QApplication.clipboard().text().strip()
        if text:
            self.url_input.setText(text)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasText() or event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        mime: QMimeData = event.mimeData()
        if mime.hasUrls():
            dropped = mime.urls()
            # Local .txt/.csv file dropped → load as URL list
            if len(dropped) == 1 and dropped[0].isLocalFile():
                local_path = dropped[0].toLocalFile()
                if local_path.lower().endswith((".txt", ".csv", ".tsv")):
                    self._load_url_file(local_path)
                    event.acceptProposedAction()
                    return
            # Otherwise use first URL as the gallery URL
            url = dropped[0].toString()
            self.url_input.setText(url)
            self._on_url_changed(url)
        elif mime.hasText():
            text = mime.text().strip()
            # Multiple URLs pasted/dropped → load into multi-URL input
            http_lines = [l.strip() for l in text.splitlines()
                          if l.strip().startswith(("http://", "https://"))]
            if len(http_lines) > 1:
                if not self.btn_multi.isChecked():
                    self.btn_multi.setChecked(True)
                current = self.url_multi_input.toPlainText().strip()
                combined = (current + "\n" + "\n".join(http_lines)).strip()
                self.url_multi_input.setPlainText(combined)
            else:
                self.url_input.setText(text)
                self._on_url_changed(text)
        event.acceptProposedAction()

    # ── URL detection ────────────────────────────────────────────────────────

    def _on_url_changed(self, text: str):
        self._url_check_timer.start()

    def _run_detection(self):
        self._update_site_banner(self.url_input.text().strip())

    def _update_site_banner(self, url: str):
        match = detect_site(url)
        if match:
            self.banner.setVisible(True)
            self.banner_site.setText(match.name)
            caps = match.capabilities
            if len(caps) > 90:
                caps = caps[:90] + "…"
            self.banner_caps.setText(caps)
            self.banner_cat.setText(f"  {match.category}")
            label, bg, fg = AUTH_LABELS.get(match.auth_type, AUTH_LABELS[None])
            self.banner_auth.setText(label)
            self.banner_auth.setStyleSheet(
                f"background:{bg}; color:{fg}; border-radius:4px;"
                "padding:2px 8px; font-size:8pt; font-weight:bold;"
            )
        else:
            self.banner.setVisible(False)

    # ── Presets ──────────────────────────────────────────────────────────────

    def _load_preset_list(self):
        self.preset_combo.clear()
        self.preset_combo.addItem("— select preset —")

        for group_label, names in preset_mgr.list_grouped():
            # Insert a non-selectable group header
            self.preset_combo.insertSeparator(self.preset_combo.count())
            header_idx = self.preset_combo.count()
            self.preset_combo.addItem(f"  {group_label}")
            # Make the header item non-selectable and visually distinct
            header_item = self.preset_combo.model().item(header_idx)
            from PyQt6.QtCore import Qt as _Qt
            from PyQt6.QtGui import QFont as _QFont
            if header_item:
                header_item.setFlags(
                    header_item.flags() & ~_Qt.ItemFlag.ItemIsEnabled & ~_Qt.ItemFlag.ItemIsSelectable
                )
                f = _QFont()
                f.setBold(True)
                f.setPointSize(max(7, f.pointSize() - 1))
                header_item.setFont(f)

            for name in names:
                self.preset_combo.addItem(f"    {name}", userData=name)

    def _load_selected_preset(self):
        name = self.preset_combo.currentData() or self.preset_combo.currentText().strip()
        if not name or name.startswith("—"):
            return
        opts = preset_mgr.load_preset(name)
        if opts:
            self._apply_options(opts)
            self._append_log("info", f"Preset loaded: {name}")
            get_settings().set("last_preset", name)

    def _save_preset(self):
        name, ok = QInputDialog.getText(self, "Save preset", "Preset name:")
        if not ok or not name.strip():
            return
        name = name.strip()
        if preset_mgr.is_builtin(name):
            QMessageBox.warning(
                self, "Reserved name",
                f'"{name}" is a built-in preset and cannot be overwritten.\n'
                "Please choose a different name."
            )
            return
        opts = self._build_options_obj()
        preset_mgr.save_preset(name, opts)
        self._load_preset_list()
        idx = self.preset_combo.findData(name)
        if idx < 0:
            idx = self.preset_combo.findText(f"    {name}")
        if idx >= 0:
            self.preset_combo.setCurrentIndex(idx)
        self._append_log("info", f"Preset saved: {name}")

    def _delete_preset(self):
        name = self.preset_combo.currentData() or self.preset_combo.currentText().strip()
        if not name or name.startswith("—"):
            return
        if preset_mgr.is_builtin(name):
            QMessageBox.information(self, "Built-in preset", "Built-in presets cannot be deleted.")
            return
        preset_mgr.delete_preset(name)
        self._load_preset_list()
        self._append_log("info", f"Preset deleted: {name}")

    def _reset_fields(self):
        self._apply_options(DownloadOptions())

    def _apply_options(self, opts: DownloadOptions):
        self.out_dir.setText(opts.output_dir or "")
        self.filename_pattern.setText(opts.filename_pattern or "")
        self.zip_check.setChecked(opts.zip_archive)
        self.mtime_check.setChecked(opts.set_mtime)
        self.filter_expr.setText(opts.item_filter or "")
        self.image_filter.setText(opts.image_filter or "")
        self.range_input.setText(opts.index_range or "")
        self.chapter_range.setText(opts.chapter_range or "")
        self.skip_existing.setChecked(opts.skip_existing)
        self.write_metadata.setChecked(opts.write_metadata)
        self.write_tags.setChecked(opts.write_tags)
        self.write_info_json.setChecked(opts.write_info_json)
        self.dry_run.setChecked(opts.dry_run)
        self.verbose.setChecked(opts.verbose)
        self.retries.setValue(opts.retries)
        self.timeout.setValue(opts.timeout)
        self.rate_limit.setText(opts.rate_limit or "")
        browser = opts.cookies_from_browser or "None"
        idx = self.cookies_browser.findText(browser)
        if idx >= 0:
            self.cookies_browser.setCurrentIndex(idx)
        self.cookies_file.setText(opts.cookies_file or "")
        self.proxy.setText(opts.proxy or "")

    # ── File dialogs ─────────────────────────────────────────────────────────

    def _browse_output_dir(self):
        path = QFileDialog.getExistingDirectory(self, "Select output directory")
        if path:
            self.out_dir.setText(path)

    def _browse_cookie_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select cookies file", filter="Text files (*.txt);;All files (*)"
        )
        if path:
            self.cookies_file.setText(path)

    def _pick_job_folder(self):
        """Let the user choose a one-off save folder for the next job."""
        start = self._job_output_dir or self.out_dir.text().strip() or ""
        path = QFileDialog.getExistingDirectory(
            self, "Save this job to…", start
        )
        if not path:
            return
        self._job_output_dir = path
        self._folder_label.setText(path)
        self._folder_label.setStyleSheet("font-size:8pt; font-weight:bold;")
        self._btn_folder_clear.setVisible(True)
        self._btn_folder_change.setText("Change…")

    def _clear_job_folder(self):
        """Reset the per-job folder override back to the global default."""
        self._job_output_dir = None
        default = self.out_dir.text().strip()
        self._folder_label.setText(
            f"Saving to  {default}" if default else "Saving to default folder"
        )
        self._folder_label.setStyleSheet("color: palette(mid); font-size:8pt;")
        self._btn_folder_clear.setVisible(False)
        self._btn_folder_change.setText("Save to\u2026")

    # ── Options → DownloadOptions ────────────────────────────────────────────

    def _build_options_obj(self) -> DownloadOptions:
        browser = self.cookies_browser.currentText()
        # Per-job folder override takes priority over the options panel value
        output_dir = self._job_output_dir or self.out_dir.text().strip() or None
        return DownloadOptions(
            output_dir=output_dir,
            filename_pattern=self.filename_pattern.text().strip() or None,
            zip_archive=self.zip_check.isChecked(),
            set_mtime=self.mtime_check.isChecked(),
            item_filter=self.filter_expr.text().strip() or None,
            image_filter=self.image_filter.text().strip() or None,
            index_range=self.range_input.text().strip() or None,
            chapter_range=self.chapter_range.text().strip() or None,
            skip_existing=self.skip_existing.isChecked(),
            write_metadata=self.write_metadata.isChecked(),
            write_tags=self.write_tags.isChecked(),
            write_info_json=self.write_info_json.isChecked(),
            dry_run=self.dry_run.isChecked(),
            verbose=self.verbose.isChecked(),
            retries=self.retries.value(),
            timeout=self.timeout.value(),
            rate_limit=self.rate_limit.text().strip() or None,
            cookies_from_browser=browser if browser != "None" else None,
            cookies_file=self.cookies_file.text().strip() or None,
            proxy=self.proxy.text().strip() or None,
        )

    # ── Download actions ─────────────────────────────────────────────────────

    # FIX #5: read defaults from app settings when the panel first loads
    def _apply_settings_defaults(self):
        s = get_settings()
        if s.get("default_output_dir"):
            self.out_dir.setText(s.get("default_output_dir"))
        if s.get("default_filename"):
            self.filename_pattern.setText(s.get("default_filename"))
        self.retries.setValue(s.get("default_retries", 4))
        self.timeout.setValue(s.get("default_timeout", 30.0))
        if s.get("default_rate_limit"):
            self.rate_limit.setText(s.get("default_rate_limit"))
        if s.get("default_proxy"):
            self.proxy.setText(s.get("default_proxy"))
        # Restore last used preset
        last = s.get("last_preset", "")
        if last:
            # Search by userData first (indented items), then fallback to text
            idx = self.preset_combo.findData(last)
            if idx < 0:
                idx = self.preset_combo.findText(last)
            if idx >= 0:
                self.preset_combo.setCurrentIndex(idx)
        s.changed.connect(self._on_setting_changed)

    def _on_setting_changed(self, key: str, value):
        if key == "default_output_dir" and value and not self.out_dir.text():
            self.out_dir.setText(value)
        elif key == "default_filename" and value and not self.filename_pattern.text():
            self.filename_pattern.setText(value)
        elif key == "default_retries":
            self.retries.setValue(int(value))
        elif key == "default_timeout":
            self.timeout.setValue(float(value))
        elif key == "default_rate_limit" and value and not self.rate_limit.text():
            self.rate_limit.setText(value)
        elif key == "default_proxy" and value and not self.proxy.text():
            self.proxy.setText(value)
        elif key == "log_max_lines":
            self.log_output.setMaximumBlockCount(int(value))
        elif key in ("theme_id", "font_size"):
            self._refresh_level_btn_styles()

    def _refresh_level_btn_styles(self):
        """Re-apply theme colours to the log level toggle buttons.

        Called once at construction and again whenever the theme or font size
        changes so the buttons always match the active theme.
        """
        from ui.themes import get_theme

        def _lighten(hex_color: str, amount: int = 28) -> str:
            c = hex_color.lstrip("#")
            r = min(255, int(c[0:2], 16) + amount)
            g = min(255, int(c[2:4], 16) + amount)
            b = min(255, int(c[4:6], 16) + amount)
            return f"#{r:02x}{g:02x}{b:02x}"

        theme = get_theme(get_settings().get("theme_id", "mocha"))
        level_colors = {
            "error":   (theme.danger,   theme.danger_hover),
            "warning": (theme.warning,  _lighten(theme.warning)),
            "info":    (theme.accent,   theme.accent_hover),
            "debug":   (theme.accent2,  _lighten(theme.accent2)),
        }
        for level, btn in self._level_btns.items():
            active_col, hover_col = level_colors[level]
            btn.setStyleSheet(f"""
                QPushButton {{
                    font-size: 8pt;
                    padding: 0 8px;
                    border: 1px solid {active_col};
                    border-radius: 3px;
                    color: {active_col};
                    background: transparent;
                }}
                QPushButton:checked {{
                    background: {active_col};
                    color: {theme.text_on_accent};
                }}
                QPushButton:hover {{
                    border-color: {hover_col};
                    color: {hover_col};
                }}
                QPushButton:checked:hover {{
                    background: {hover_col};
                    color: {theme.text_on_accent};
                }}
            """)

    # FIX #10: validate URL before starting
    def _validate_url(self, url: str) -> str | None:
        """Return an error message if the URL is invalid, else None."""
        if not url:
            return "Please enter a URL."
        if not url.startswith(("http://", "https://", "ftp://")):
            return (
                f"'{url[:60]}' doesn't look like a URL.\n"
                "It should start with http:// or https://"
            )
        return None

    def _validate_rate_limit(self, value: str) -> str | None:
        """Return an error message if the rate-limit string is invalid, else None.

        gallery-dl accepts:  <number>         (bytes/s)
                             <number>k or K   (kilobytes/s)
                             <number>m or M   (megabytes/s)
        Anything else will be silently rejected by gallery-dl at runtime.
        """
        import re as _re
        if not value:
            return None   # empty = no rate limit, always valid
        if not _re.fullmatch(r"\d+(\.\d+)?[kKmM]?", value):
            return (
                f"Invalid rate limit '{value}'. "
                "Use a number optionally followed by k or M  (e.g. 500k, 2M, 1048576)."
            )
        return None

    def _on_download(self):
        url = self.url_input.text().strip()
        err = self._validate_url(url)
        if err:
            self._append_log("error", err)
            self.url_input.setStyleSheet(
                "border: 1px solid palette(bright-text); border-radius: 6px; padding: 5px 9px;"
            )
            return
        self.url_input.setStyleSheet("")
        rate_err = self._validate_rate_limit(self.rate_limit.text().strip())
        if rate_err:
            self._append_log("error", rate_err)
            self.rate_limit.setStyleSheet(
                "border: 1px solid palette(bright-text); border-radius: 4px; padding: 2px 6px;"
            )
            return
        self.rate_limit.setStyleSheet("")
        if self._is_duplicate(url):
            resp = QMessageBox.question(
                self, "Duplicate URL",
                f"This URL is already queued or running:\n{url[:80]}\n\nStart another download anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if resp != QMessageBox.StandardButton.Yes:
                return
        opts = self._build_options_obj()
        job = self.manager.start(url, opts)
        job.log_line.connect(self._append_log)
        job.progress_updated.connect(self._on_progress_tick)
        # FIX #6: capture job in closure, not via manager._active
        job.finished.connect(lambda j=job: self._on_job_finished(j))
        self.btn_stop.setEnabled(True)
        self.btn_download.setEnabled(False)
        self._clear_job_folder()   # reset per-job folder ready for next job

    def _on_queue(self):
        url = self.url_input.text().strip()
        err = self._validate_url(url)
        if err:
            self._append_log("error", err)
            self.url_input.setStyleSheet(
                "border: 1px solid palette(bright-text); border-radius: 6px; padding: 5px 9px;"
            )
            return
        self.url_input.setStyleSheet("")
        if self._is_duplicate(url):
            resp = QMessageBox.question(
                self, "Duplicate URL",
                f"This URL is already in the queue:\n{url[:80]}\n\nAdd it again?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if resp != QMessageBox.StandardButton.Yes:
                return
        opts = self._build_options_obj()
        self.manager.enqueue(url, opts)
        self.url_input.clear()
        self.banner.setVisible(False)
        self.queued.emit()
        self._append_log("info", f"Queued: {url}")
        self._clear_job_folder()   # reset per-job folder ready for next job

    def _on_stop(self):
        if get_settings().get("confirm_before_stop", True):
            resp = QMessageBox.question(
                self, "Stop download",
                "Stop the active download?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if resp != QMessageBox.StandardButton.Yes:
                return
        self.manager.stop_active()
        self.btn_stop.setEnabled(False)
        self.btn_download.setEnabled(True)
        # record_job_cancelled() is emitted by the status_changed signal handler
        # in DownloadManager._make_job() when the job status transitions to
        # CANCELLED — no manual call needed here, and it would double-count.

    # FIX #6: job passed directly, no private manager access
    @pyqtSlot()
    def _on_job_finished(self, job=None):
        self.btn_stop.setEnabled(False)
        self.btn_download.setEnabled(True)
        # Stats (started/done/error/cancelled) are all recorded by the
        # status_changed signal handler in DownloadManager._make_job() —
        # no manual accounting needed here.
        # Notification sound
        if get_settings().get("notify_sound", False):
            try:
                from PyQt6.QtMultimedia import QSoundEffect
                from PyQt6.QtCore import QUrl
                import os
                sound_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                          "..", "..", "assets", "complete.wav")
                if os.path.exists(sound_path):
                    fx = QSoundEffect(self)
                    fx.setSource(QUrl.fromLocalFile(os.path.abspath(sound_path)))
                    fx.play()
                else:
                    # Fallback: system bell
                    from PyQt6.QtWidgets import QApplication
                    QApplication.beep()
            except Exception:
                from PyQt6.QtWidgets import QApplication
                QApplication.beep()

    @pyqtSlot(int, int)
    def _on_progress_tick(self, done: int, total: int):
        # Don't double-count via file_done signal — progress_tick is for the bar only
        pass

    # ── Log ──────────────────────────────────────────────────────────────────

    @pyqtSlot(str, str)
    def _append_log(self, level: str, line: str):
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        # Use CSS class names mapped to palette roles in QTextBrowser QSS
        LEVEL_CLASS = {
            "error":   "log-error",
            "warning": "log-warn",
            "info":    "log-info",
            "debug":   "log-debug",
        }
        cls = LEVEL_CLASS.get(level, "log-info")
        ts_html = f'<span class="log-ts">[{timestamp}]</span> '
        text_html = f'<span class="{cls}">{html.escape(line)}</span>'
        entry = ts_html + text_html
        self._log_lines.append((level, entry))

        if level not in self._log_level_filters:
            return
        filt = self.log_search.text().strip().lower()
        if not filt or filt in line.lower():
            self.log_output.appendHtml(entry)
            self.log_output.moveCursor(QTextCursor.MoveOperation.End)

    def _toggle_level_filter(self, level: str, checked: bool):
        if checked:
            self._log_level_filters.add(level)
        else:
            self._log_level_filters.discard(level)
        self._filter_log(self.log_search.text())

    def _filter_log(self, query: str = ""):
        query = query.strip().lower()
        self.log_output.clear()
        import re
        for level, html_line in self._log_lines:
            if level not in self._log_level_filters:
                continue
            plain = re.sub(r"<[^>]+>", "", html_line)
            if not query or query in plain.lower():
                self.log_output.appendHtml(html_line)
        self.log_output.moveCursor(QTextCursor.MoveOperation.End)

    def _copy_log(self):
        from PyQt6.QtWidgets import QApplication
        import re
        lines = [re.sub(r"<[^>]+>", "", h) for _, h in self._log_lines]
        QApplication.clipboard().setText("\n".join(lines))

    def _clear_log(self):
        self._log_lines.clear()
        self.log_output.clear()

    # ── Banner fields (needed by main_window to set URL from Sites panel) ───

    def set_url(self, url: str):
        self.url_input.setText(url)
