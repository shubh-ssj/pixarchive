from __future__ import annotations

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QListWidget, QListWidgetItem, QStackedWidget, QLabel,
    QApplication, QMenuBar, QMenu, QPushButton, QMessageBox
)
from PyQt6.QtCore import Qt, QSize, QEvent, QTimer
from PyQt6.QtGui import QKeySequence, QAction

from ui.panels.download_panel import DownloadPanel
from ui.panels.queue_panel import QueuePanel
from ui.panels.history_panel import HistoryPanel
from ui.panels.config_panel import ConfigPanel
from ui.panels.accounts_panel import AccountsPanel
from ui.panels.sites_panel import SitesPanel
from ui.panels.scheduler_panel import SchedulerPanel
from ui.status_bar import StatusBar
from ui.tip_bar import TipBar
from ui.tray import TrayManager
from core.download_manager import DownloadManager
from core.scheduler import Scheduler
from core.url_detector import detect_site
from core.app_settings import get_settings


NAV_ITEMS = [
    ("Download",   "⬇", "Ctrl+1"),
    ("Queue",      "≡",  "Ctrl+2"),
    ("History",    "◷", "Ctrl+3"),
    ("Scheduler",  "⏱", "Ctrl+4"),
    ("Sites",      "◈", "Ctrl+5"),
    ("Config",     "⚙", "Ctrl+6"),
    ("Accounts",   "☻", "Ctrl+7"),
]


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PixArchive")
        self.setMinimumSize(960, 640)
        self.resize(1200, 760)
        self._set_window_icon()

        self._settings_dialog = None
        self._help_dialog     = None
        self._about_dialog    = None

        # Debounce timer for minimize-to-tray — prevents rapid taskbar clicks
        # from queuing multiple hide() calls
        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self._hide_to_tray_if_minimized)

        self.download_manager = DownloadManager()
        self.scheduler = Scheduler(self)
        self._build_menu()
        self._build_ui()
        self._connect_signals()
        self._setup_tray()
        self._setup_drag_drop()
        self._setup_clipboard_watch()
        self._setup_update_check()

    # ── Window icon ──────────────────────────────────────────────────────────

    def _set_window_icon(self):
        import sys, os
        from PyQt6.QtGui import QIcon
        # PyInstaller bundle: assets are in _MEIPASS/assets/
        if getattr(sys, "frozen", False):
            base = sys._MEIPASS          # type: ignore[attr-defined]
        else:
            base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        ico = os.path.join(base, "assets", "icon.ico")
        if os.path.exists(ico):
            self.setWindowIcon(QIcon(ico))

    # ── Menu bar ─────────────────────────────────────────────────────────────

    def _build_menu(self):
        mb: QMenuBar = self.menuBar()

        # File
        file_menu: QMenu = mb.addMenu("File")

        act_download = QAction("New download…", self)
        act_download.setShortcut(QKeySequence("Ctrl+N"))
        act_download.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        act_download.triggered.connect(lambda: self.nav_list.setCurrentRow(0))
        file_menu.addAction(act_download)

        act_paste = QAction("Paste URL from clipboard", self)
        act_paste.setShortcut(QKeySequence("Ctrl+Shift+V"))
        act_paste.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        act_paste.triggered.connect(self._paste_to_url)
        file_menu.addAction(act_paste)

        file_menu.addSeparator()

        act_settings = QAction("Settings…", self)
        act_settings.setShortcut(QKeySequence("Ctrl+,"))
        act_settings.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        act_settings.triggered.connect(self.open_settings)
        file_menu.addAction(act_settings)

        file_menu.addSeparator()

        act_export = QAction("Export config bundle…", self)
        act_export.setShortcut(QKeySequence("Ctrl+Shift+E"))
        act_export.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        act_export.triggered.connect(self._export_bundle)
        file_menu.addAction(act_export)

        act_import = QAction("Import config bundle…", self)
        act_import.setShortcut(QKeySequence("Ctrl+Shift+I"))
        act_import.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        act_import.triggered.connect(self._import_bundle)
        file_menu.addAction(act_import)

        file_menu.addSeparator()

        act_quit = QAction("Quit", self)
        act_quit.setShortcut(QKeySequence("Ctrl+Q"))
        act_quit.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        act_quit.triggered.connect(QApplication.quit)
        file_menu.addAction(act_quit)

        # View
        view_menu: QMenu = mb.addMenu("View")
        for i, (label, icon, shortcut) in enumerate(NAV_ITEMS):
            act = QAction(f"{icon}  {label}", self)
            act.setShortcut(QKeySequence(shortcut))
            act.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
            act.triggered.connect(lambda checked=False, idx=i: self.nav_list.setCurrentRow(idx))
            view_menu.addAction(act)

        # Download
        dl_menu: QMenu = mb.addMenu("Download")

        act_start = QAction("Start all queued", self)
        act_start.triggered.connect(self.download_manager.start_queued)
        dl_menu.addAction(act_start)

        act_stop = QAction("Stop active download", self)
        act_stop.triggered.connect(self.download_manager.stop_active)
        dl_menu.addAction(act_stop)

        dl_menu.addSeparator()

        act_clear = QAction("Clear finished jobs", self)
        act_clear.triggered.connect(self.download_manager.clear_finished)
        dl_menu.addAction(act_clear)

        # Help
        help_menu: QMenu = mb.addMenu("Help")

        act_help = QAction("Help…", self)
        act_help.setShortcut(QKeySequence("F1"))
        act_help.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        act_help.triggered.connect(self.open_help)
        help_menu.addAction(act_help)

        help_menu.addSeparator()

        act_check_update = QAction("Check for gallery-dl update", self)
        act_check_update.triggered.connect(self._manual_update_check)
        help_menu.addAction(act_check_update)

        help_menu.addSeparator()

        act_gdl_docs = QAction("gallery-dl documentation", self)
        act_gdl_docs.triggered.connect(lambda: self._open_url("https://gdl-org.github.io/docs/"))
        help_menu.addAction(act_gdl_docs)

        act_gdl_gh = QAction("gallery-dl on GitHub", self)
        act_gdl_gh.triggered.connect(lambda: self._open_url("https://github.com/mikf/gallery-dl"))
        help_menu.addAction(act_gdl_gh)

        help_menu.addSeparator()

        act_about = QAction("About PixArchive…", self)
        act_about.triggered.connect(self.open_about)
        help_menu.addAction(act_about)

    # ── UI ───────────────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QWidget()
        outer = QVBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        self.setCentralWidget(root)

        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(0)

        row_layout.addWidget(self._build_sidebar())

        self.stack = QStackedWidget()
        self.download_panel  = DownloadPanel(self.download_manager)
        self.queue_panel     = QueuePanel(self.download_manager)
        self.history_panel   = HistoryPanel(self.download_manager)
        self.scheduler_panel = SchedulerPanel(self.scheduler)
        self.sites_panel     = SitesPanel()
        self.config_panel    = ConfigPanel()
        self.accounts_panel  = AccountsPanel()

        for panel in (
            self.download_panel, self.queue_panel, self.history_panel,
            self.scheduler_panel, self.sites_panel, self.config_panel, self.accounts_panel,
        ):
            self.stack.addWidget(panel)

        row_layout.addWidget(self.stack, stretch=1)

        # Feature tip bar — shown once per app version, above the content area
        if TipBar.should_show():
            self.tip_bar = TipBar()
            self.tip_bar.nav_requested.connect(self.nav_list.setCurrentRow)
            outer.addWidget(self.tip_bar)
        else:
            self.tip_bar = None

        outer.addWidget(row, stretch=1)
        outer.addWidget(StatusBar())

    def _build_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setFixedWidth(172)
        sidebar.setObjectName("sidebar")

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(8, 14, 8, 12)
        layout.setSpacing(0)

        title = QLabel("gallery-dl")
        title.setObjectName("sidebar_title")
        layout.addWidget(title)

        self.nav_list = QListWidget()
        self.nav_list.setObjectName("nav_list")
        self.nav_list.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        for label, icon, _ in NAV_ITEMS:
            item = QListWidgetItem(f"  {icon}  {label}")
            item.setSizeHint(QSize(0, 36))
            self.nav_list.addItem(item)
        self.nav_list.setCurrentRow(0)
        layout.addWidget(self.nav_list, stretch=1)

        btn_settings = QPushButton("  ⚙  Settings")
        btn_settings.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_settings.clicked.connect(self.open_settings)
        layout.addWidget(btn_settings)

        btn_help = QPushButton("  ?  Help")
        btn_help.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_help.clicked.connect(self.open_help)
        layout.addWidget(btn_help)

        btn_about = QPushButton("  ℹ  About")
        btn_about.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_about.clicked.connect(self.open_about)
        layout.addWidget(btn_about)

        version_lbl = QLabel("v1.4.0")
        version_lbl.setObjectName("sidebar_version")
        layout.addWidget(version_lbl)

        return sidebar

    # ── Signals ──────────────────────────────────────────────────────────────

    def _connect_signals(self):
        self.nav_list.currentRowChanged.connect(self.stack.setCurrentIndex)
        self.download_panel.queued.connect(lambda: self.nav_list.setCurrentRow(1))
        self.sites_panel.url_selected.connect(self._on_site_url_selected)
        self.scheduler.job_triggered.connect(
            lambda url, opts: self.download_manager.enqueue(url, opts)
        )

    def _export_bundle(self):
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        from core.config_bundle import export_bundle, suggested_filename
        path, _ = QFileDialog.getSaveFileName(
            self, "Export config bundle",
            suggested_filename(),
            "PixArchive bundle (*.zip);;All files (*)"
        )
        if not path:
            return
        try:
            included = export_bundle(path)
            if included:
                QMessageBox.information(
                    self, "Export complete",
                    f"Config bundle exported successfully.\n\nIncluded:\n" +
                    "\n".join(f"  • {f}" for f in included)
                )
            else:
                QMessageBox.warning(
                    self, "Nothing to export",
                    "No user config files found to export.\n\n"
                    "Try customising some presets or site overrides first."
                )
        except Exception as e:
            QMessageBox.critical(self, "Export failed", str(e))

    def _import_bundle(self):
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        from core.config_bundle import import_bundle
        from core import presets as preset_mgr

        path, _ = QFileDialog.getOpenFileName(
            self, "Import config bundle",
            "",
            "PixArchive bundle (*.zip);;All files (*)"
        )
        if not path:
            return

        resp = QMessageBox.question(
            self, "Import config bundle",
            "Import settings from this bundle?\n\n"
            "Existing settings will be merged (your local settings take "
            "priority for window geometry and session state). "
            "Presets and site overrides will be added alongside your current ones.\n\n"
            "The app will reload settings after import.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if resp != QMessageBox.StandardButton.Yes:
            return

        try:
            results = import_bundle(path, merge=True)
        except ValueError as e:
            QMessageBox.critical(self, "Invalid bundle", str(e))
            return
        except Exception as e:
            QMessageBox.critical(self, "Import failed", str(e))
            return

        # Reload live objects from disk
        from core.app_settings import get_settings
        get_settings().reload()
        preset_mgr._invalidate_cache()
        self.scheduler._jobs = []
        from core.scheduler import _load_jobs
        self.scheduler._jobs = _load_jobs()
        self.scheduler.jobs_changed.emit()

        # Refresh panels that cache preset/override lists
        self.download_panel._load_preset_list()

        lines = [f"  {name}: {status}" for name, status in results.items()]
        QMessageBox.information(
            self, "Import complete",
            "Bundle imported.\n\n" + "\n".join(lines) +
            "\n\nSome changes (theme, paths) take effect on next launch."
        )

    def _on_site_url_selected(self, url: str):
        self.download_panel.url_input.setText(url)
        self.nav_list.setCurrentRow(0)

    # ── Shortcuts ────────────────────────────────────────────────────────────
    # All shortcuts are registered on their QActions with ApplicationShortcut
    # context above — no separate QShortcut objects needed.

    def _paste_to_url(self):
        text = QApplication.clipboard().text().strip()
        if text:
            self.download_panel.url_input.setText(text)
            self.nav_list.setCurrentRow(0)

    # ── Tray ─────────────────────────────────────────────────────────────────

    def _setup_tray(self):
        self._tray_manager = TrayManager(self, self.download_manager)

    # ── Drag & drop onto the main window ─────────────────────────────────────

    def _setup_drag_drop(self):
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText() or event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        mime = event.mimeData()
        urls = []
        if mime.hasUrls():
            urls = [u.toString() for u in mime.urls() if u.toString().startswith("http")]
        elif mime.hasText():
            # Support dropping a text file or pasted multi-line text
            for line in mime.text().splitlines():
                line = line.strip()
                if line.startswith("http"):
                    urls.append(line)

        if not urls:
            event.ignore()
            return

        # First URL goes into the download bar; rest get queued immediately
        self.download_panel.url_input.setText(urls[0])
        self.nav_list.setCurrentRow(0)
        if len(urls) > 1:
            opts = self.download_panel._build_options_obj()
            for url in urls[1:]:
                self.download_manager.enqueue(url, opts)
            self.nav_list.setCurrentRow(1)
            self.download_panel._append_log("info", f"Drag-dropped {len(urls)-1} additional URL(s) added to queue.")
        event.acceptProposedAction()

    # ── Clipboard watch ───────────────────────────────────────────────────────

    def _setup_clipboard_watch(self):
        self._last_clipboard = ""

    def changeEvent(self, event: QEvent):
        super().changeEvent(event)
        if event.type() == QEvent.Type.WindowStateChange:
            # Minimize button → hide to tray (if enabled and tray is available).
            # Use a debounce timer so rapid taskbar clicks (minimize/restore/minimize…)
            # only queue one hide() call, and re-check isMinimized() at fire time so
            # a quick restore before the timer fires doesn't accidentally hide the window.
            s = get_settings()
            if (self.isMinimized()
                    and s.get("minimize_to_tray", True)
                    and self._tray_manager._tray is not None):
                self._hide_timer.start(50)   # coalesce bursts; check state on fire
        elif event.type() == QEvent.Type.ActivationChange and self.isActiveWindow():
            s = get_settings()
            if s.get("clipboard_watch", True):
                self._check_clipboard_for_url()

    def _hide_to_tray_if_minimized(self):
        """Called by the debounce timer — only hides if still minimized."""
        if self.isMinimized():
            self.hide()

    def _check_clipboard_for_url(self):
        # Only act on the Download panel
        if self.nav_list.currentRow() != 0:
            return
        text = QApplication.clipboard().text().strip()
        # Don't re-offer the same URL twice, and don't clobber user input
        if not text or text == self._last_clipboard:
            return
        if "\n" in text:  # multi-line — not a URL
            return
        if self.download_panel.url_input.text().strip():
            return
        if detect_site(text):
            self._last_clipboard = text
            self.download_panel.url_input.setText(text)

    # ── Update checker ────────────────────────────────────────────────────────

    def _setup_update_check(self):
        s = get_settings()
        if not s.get("check_updates", True):
            return
        # Delay the check 5s after startup so it doesn't slow the launch
        QTimer.singleShot(5000, self._run_update_check)

    def _run_update_check(self):
        from core.updater import UpdateChecker
        s = get_settings()
        self._updater = UpdateChecker(gdl_cmd=s.get("gallery_dl_path", "gallery-dl"), parent=self)
        self._updater.update_available.connect(self._on_update_available)
        self._updater.check()

    def _manual_update_check(self):
        from core.updater import UpdateChecker
        s = get_settings()
        self._manual_updater = UpdateChecker(gdl_cmd=s.get("gallery_dl_path", "gallery-dl"), parent=self)
        def _on_result(installed, latest):
            QMessageBox.information(
                self, "gallery-dl update available",
                f"Installed: {installed}\nLatest:    {latest}\n\n"
                f"Run:  pip install -U gallery-dl"
            )
        def _on_up_to_date(installed):
            QMessageBox.information(
                self, "gallery-dl is up to date",
                f"You have the latest version: {installed}"
            )
        def _on_fail(msg):
            QMessageBox.warning(self, "Update check failed", msg)
        self._manual_updater.update_available.connect(_on_result)
        self._manual_updater.up_to_date.connect(_on_up_to_date)
        self._manual_updater.check_failed.connect(_on_fail)
        self._manual_updater.check()

    def _on_update_available(self, installed: str, latest: str):
        """Passive notification — only shows tray balloon, not a modal dialog."""
        if self._tray_manager._tray:
            from PyQt6.QtWidgets import QSystemTrayIcon
            self._tray_manager._tray.showMessage(
                "gallery-dl update available",
                f"Installed: {installed}  →  Latest: {latest}\n"
                "Run: pip install -U gallery-dl",
                QSystemTrayIcon.MessageIcon.Information,
                6000,
            )

    # ── Dialog openers ───────────────────────────────────────────────────────

    def open_settings(self):
        from ui.dialogs.settings_dialog import SettingsDialog
        if self._settings_dialog is None:
            self._settings_dialog = SettingsDialog(self)
        else:
            self._settings_dialog._load_values()
        self._settings_dialog.exec()

    def open_help(self, page: str = ""):
        from ui.dialogs.help_dialog import HelpDialog
        if self._help_dialog is None:
            self._help_dialog = HelpDialog(self)
        if page:
            self._help_dialog.open_page(page)
        self._help_dialog.show()
        self._help_dialog.raise_()
        self._help_dialog.activateWindow()

    def open_about(self):
        from ui.dialogs.about_dialog import AboutDialog
        dlg = AboutDialog(self)
        dlg.exec()

    # ── Geometry & state persistence ─────────────────────────────────────────

    def _restore_state(self):
        s = get_settings()
        if s.get("remember_window_size", True):
            w = s.get("window_width",  1200)
            h = s.get("window_height", 760)
            x = s.get("window_x", -1)
            y = s.get("window_y", -1)
            self.resize(w, h)
            if x >= 0 and y >= 0:
                screen = QApplication.primaryScreen().availableGeometry()
                x = max(0, min(x, screen.width()  - 100))
                y = max(0, min(y, screen.height() - 100))
                self.move(x, y)
            if s.get("window_maximized", False):
                self.showMaximized()

        panel_idx = int(s.get("active_panel", 0))
        if 0 <= panel_idx < self.nav_list.count():
            self.nav_list.setCurrentRow(panel_idx)

    def _save_state(self):
        s = get_settings()
        if s.get("remember_window_size", True):
            maximized = self.isMaximized()
            geo = self.normalGeometry()   # always the restored (non-maximized) geometry
            s.set_many({
                "window_width":     geo.width(),
                "window_height":    geo.height(),
                "window_x":         geo.x(),
                "window_y":         geo.y(),
                "window_maximized": maximized,
                "active_panel":     self.nav_list.currentRow(),
            })

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _open_url(self, url: str):
        import webbrowser
        browser = get_settings().get("preferred_browser", "")
        if browser:
            try:
                webbrowser.get(browser).open(url)
                return
            except webbrowser.Error:
                pass   # browser name not recognised — fall back to system default
        webbrowser.open(url)

    def closeEvent(self, event):
        from core.job import JobStatus
        s = get_settings()
        active = [j for j in self.download_manager.jobs if j.status == JobStatus.RUNNING]
        if active and s.get("confirm_before_stop", True):
            resp = QMessageBox.question(
                self, "Quit with active downloads?",
                f"{len(active)} download(s) still running.\nStop them and quit?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if resp != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
        self._save_state()
        self.download_manager.stop_all()
        event.accept()
        QApplication.quit()
