"""
First-run / setup wizard.
Shown automatically when gallery-dl is not detected on PATH.
Checks installation, lets the user point to a custom path, and
writes the result to settings so the app is ready to go.
"""
from __future__ import annotations
import subprocess
import sys
import os

# Oldest gallery-dl version we consider fully supported.
# Bump this when a site-breaking gallery-dl release is known.
from core.utils import GDL_MIN_VERSION as _GDL_MIN_VERSION, parse_version as _parse_version, version_str as _version_str

CODEBERG_RELEASES_URL = "https://codeberg.org/gallery-dl/gallery-dl/releases"

# In-memory cache of the last confirmed-working gallery-dl command.
# Set on wizard success or after a download completes without error.
# Cleared by invalidate_gdl_cmd() when a download failure suggests
# gallery-dl is broken or missing, so the next check re-runs the wizard.
_confirmed_cmd: str | None = None


def get_confirmed_cmd() -> str | None:
    """Return the cached gallery-dl command, or None if not yet confirmed."""
    return _confirmed_cmd


def confirm_gdl_cmd(cmd: str) -> None:
    """
    Call this after a successful download to cache the working command.
    Subsequent check_and_show() calls will skip all checks and return True
    immediately until invalidate_gdl_cmd() is called.
    """
    global _confirmed_cmd
    _confirmed_cmd = cmd


def invalidate_gdl_cmd() -> None:
    """
    Call this when a download fails in a way that suggests gallery-dl is
    missing or broken. The next check_and_show() will re-run the wizard.
    """
    global _confirmed_cmd
    _confirmed_cmd = None


def _parse_gdl_version(v: str) -> tuple[int, ...]:
    """Delegate to core.utils.parse_version — tested independently of Qt."""
    return _parse_version(v)


def _pip_available() -> bool:
    """Return True if pip is usable in the current Python environment."""
    try:
        import importlib.util
        return importlib.util.find_spec("pip") is not None
    except Exception:
        return False

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QFileDialog, QWidget, QStackedWidget, QProgressBar,
    QPlainTextEdit
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject
from PyQt6.QtGui import QFont


# ── Background worker ─────────────────────────────────────────────────────────

class _CheckWorker(QObject):
    done = pyqtSignal(bool, str, str)   # (found, version, path_used)

    def __init__(self, cmd: str):
        super().__init__()
        self._cmd = cmd

    def run(self):
        try:
            _extra = {"creationflags": subprocess.CREATE_NO_WINDOW} if sys.platform == "win32" else {}
            r = subprocess.run(
                [self._cmd, "--version"],
                capture_output=True, text=True, timeout=8,
                **_extra,
            )
            raw = (r.stdout or r.stderr).strip()
            if raw:
                self.done.emit(True, raw, self._cmd)
            else:
                self.done.emit(False, "", self._cmd)
        except FileNotFoundError:
            self.done.emit(False, "", self._cmd)
        except Exception as e:
            self.done.emit(False, str(e), self._cmd)


class _InstallWorker(QObject):
    output  = pyqtSignal(str)
    done    = pyqtSignal(bool, str)   # (success, message)

    def run(self):
        try:
            _extra = {"creationflags": subprocess.CREATE_NO_WINDOW} if sys.platform == "win32" else {}
            proc = subprocess.Popen(
                [sys.executable, "-m", "pip", "install", "--upgrade", "gallery-dl"],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding="utf-8", errors="replace",
                **_extra,
            )
            for line in proc.stdout:
                self.output.emit(line.rstrip())
            proc.wait()
            if proc.returncode == 0:
                self.done.emit(True, "Installation successful.")
            else:
                self.done.emit(False, f"pip exited with code {proc.returncode}")
        except Exception as e:
            self.done.emit(False, str(e))


# ── Startup gallery-dl version checker ───────────────────────────────────────

class GdlVersionChecker(QObject):
    """
    Background checker run on every startup. Emits outdated(version_str) if
    gallery-dl is present but older than _GDL_MIN_VERSION.
    """
    outdated = pyqtSignal(str)   # version string found
    ok       = pyqtSignal(str)   # version string found and acceptable

    def __init__(self, parent=None):
        super().__init__(parent)
        from PyQt6.QtCore import QThread
        from core.app_settings import resolve_gdl_cmd
        self._thread = QThread(self)
        self._worker = _CheckWorker(resolve_gdl_cmd())
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.done.connect(self._on_result)
        self._worker.done.connect(self._thread.quit)
        self._thread.finished.connect(self._worker.deleteLater)

    def start(self):
        self._thread.start()

    def _on_result(self, found: bool, version: str, _cmd: str):
        if not found:
            return
        parsed = _parse_gdl_version(version)
        if parsed != (0,) and parsed < _GDL_MIN_VERSION:
            self.outdated.emit(version)
        else:
            self.ok.emit(version)


class GdlOutdatedBanner(QWidget):
    """Warning banner shown in the main window when gallery-dl is outdated."""

    def __init__(self, version: str, parent=None):
        super().__init__(parent)
        self.setObjectName("gdl_warn_banner")
        self.setStyleSheet(
            "#gdl_warn_banner { background: #f38ba8; }"
            "#gdl_warn_banner QLabel { color: #1e1e2e; font-size:8.5pt; }"
            "#gdl_warn_banner QPushButton { color: #1e1e2e; font-size:8pt; "
            "background: transparent; border: 1px solid #1e1e2e; "
            "border-radius: 3px; padding: 1px 8px; }"
        )
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 5, 10, 5)
        layout.setSpacing(10)

        lbl = QLabel(
            f"⚠  gallery-dl {version} is outdated (minimum recommended: "
            f"{_version_str(_GDL_MIN_VERSION)}) — some sites may fail."
        )
        layout.addWidget(lbl, stretch=1)

        btn_upgrade = QPushButton("How to upgrade")
        btn_upgrade.clicked.connect(self._show_upgrade_info)
        layout.addWidget(btn_upgrade)

        btn_x = QPushButton("✕")
        btn_x.setFixedWidth(24)
        btn_x.clicked.connect(lambda: self.setVisible(False))
        layout.addWidget(btn_x)

    def _show_upgrade_info(self):
        from PyQt6.QtWidgets import QMessageBox
        if _pip_available():
            msg = (
                "Run the following command in a terminal to upgrade gallery-dl:\n\n"
                "    pip install --upgrade gallery-dl\n\n"
                "Then restart PixArchive."
            )
        else:
            msg = (
                "Download the latest release from:\n\n"
                f"    {CODEBERG_RELEASES_URL}\n\n"
                "Replace your existing gallery-dl executable with the new one,\n"
                "then restart PixArchive."
            )
        QMessageBox.information(self, "Upgrade gallery-dl", msg)


# ── Dialog ────────────────────────────────────────────────────────────────────

class FirstRunDialog(QDialog):
    """
    Multi-page wizard:
      Page 0 — Welcome / checking
      Page 1 — Not found: offer install or locate
      Page 2 — Installing (live pip output)
      Page 3 — Done (success or failure)
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Welcome to PixArchive — Setup")
        self.setMinimumWidth(560)
        self.setMinimumHeight(380)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        self._found_cmd: str = "gallery-dl"
        self._check_ok: bool = False   # True only after a real successful check
        self._build_ui()
        self._start_check("gallery-dl")

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header
        header = QWidget()
        header.setObjectName("dialog_header")
        header.setFixedHeight(70)
        hl = QHBoxLayout(header)
        hl.setContentsMargins(24, 0, 24, 0)
        hl.setSpacing(14)

        # Full logo (with text) in the header
        if getattr(sys, "frozen", False):
            _base = sys._MEIPASS  # type: ignore[attr-defined]
        else:
            _base = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        _full_logo = os.path.join(_base, "assets", "icon_full.png")
        if os.path.exists(_full_logo):
            from PyQt6.QtGui import QPixmap
            logo_lbl = QLabel()
            px = QPixmap(_full_logo).scaledToHeight(
                48, Qt.TransformationMode.SmoothTransformation)
            logo_lbl.setPixmap(px)
            hl.addWidget(logo_lbl)
        else:
            title = QLabel("PixArchive — First Run Setup")
            title.setStyleSheet("font-size:13pt; font-weight:bold;")
            hl.addWidget(title)

        hl.addStretch()

        root.addWidget(header)

        # Pages
        self.stack = QStackedWidget()
        root.addWidget(self.stack, stretch=1)

        self.stack.addWidget(self._page_checking())   # 0
        self.stack.addWidget(self._page_not_found())  # 1
        self.stack.addWidget(self._page_installing()) # 2
        self.stack.addWidget(self._page_done())       # 3

        # Footer
        footer = QWidget()
        footer.setObjectName("dialog_footer")
        fl = QHBoxLayout(footer)
        fl.setContentsMargins(16, 10, 16, 10)
        fl.setSpacing(8)

        self.btn_skip = QPushButton("Skip for now")
        self.btn_skip.setStyleSheet("color: palette(mid);")
        self.btn_skip.clicked.connect(self._on_skip)
        fl.addWidget(self.btn_skip)

        fl.addStretch()

        self.btn_primary = QPushButton("Continue")
        self.btn_primary.setObjectName("btn_download")
        self.btn_primary.setFixedWidth(120)
        self.btn_primary.setEnabled(False)
        self.btn_primary.clicked.connect(self._on_primary)
        fl.addWidget(self.btn_primary)

        root.addWidget(footer)

    def _page_checking(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(24, 24, 24, 24)
        v.setSpacing(16)
        v.addStretch()

        self.check_spinner = QProgressBar()
        self.check_spinner.setRange(0, 0)   # indeterminate
        self.check_spinner.setFixedHeight(6)
        self.check_spinner.setTextVisible(False)
        v.addWidget(self.check_spinner)

        self.check_label = QLabel("Checking for gallery-dl…")
        self.check_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.check_label.setStyleSheet("color: palette(mid); font-size:10pt;")
        v.addWidget(self.check_label)

        v.addStretch()
        return w

    def _page_not_found(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(24, 20, 24, 20)
        v.setSpacing(14)

        icon_lbl = QLabel("⚠")
        icon_lbl.setStyleSheet("font-size:28pt; color: palette(bright-text);")
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        v.addWidget(icon_lbl)

        headline = QLabel("gallery-dl was not found on your PATH")
        headline.setStyleSheet("font-size:11pt; font-weight:bold;")
        headline.setAlignment(Qt.AlignmentFlag.AlignCenter)
        v.addWidget(headline)

        _has_pip = _pip_available()

        desc = QLabel(
            "PixArchive uses gallery-dl as its download engine.\n"
            + (
                "You can install it automatically with pip, or locate it manually\n"
                "if you already have it installed somewhere else."
                if _has_pip else
                "Download the latest release from Codeberg and place the executable\n"
                "somewhere on your PATH, or locate it manually below."
            )
        )
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setStyleSheet("color: palette(mid); font-size:9pt;")
        v.addWidget(desc)

        v.addSpacing(8)

        # pip install button — shown only when pip is available
        self.btn_install = QPushButton("  ⬇  Install gallery-dl via pip")
        self.btn_install.setObjectName("btn_download")
        self.btn_install.setFixedHeight(38)
        self.btn_install.clicked.connect(self._start_install)
        self.btn_install.setVisible(_has_pip)

        # Codeberg button — shown when pip is not available
        self.btn_codeberg = QPushButton("  🌐  Open gallery-dl releases page")
        self.btn_codeberg.setObjectName("btn_download")
        self.btn_codeberg.setFixedHeight(38)
        self.btn_codeberg.clicked.connect(self._open_codeberg)
        self.btn_codeberg.setVisible(not _has_pip)
        v.addWidget(self.btn_install)
        v.addWidget(self.btn_codeberg)

        # Locate manually
        locate_row = QHBoxLayout()
        self.custom_path = QLineEdit()
        self.custom_path.setPlaceholderText("Or paste path to gallery-dl executable…")
        self.custom_path.setFixedHeight(34)
        locate_row.addWidget(self.custom_path, stretch=1)

        btn_browse = QPushButton("Browse…")
        btn_browse.setFixedHeight(34)
        btn_browse.clicked.connect(self._browse_executable)
        locate_row.addWidget(btn_browse)

        btn_verify = QPushButton("Verify")
        btn_verify.setFixedHeight(34)
        btn_verify.clicked.connect(lambda: self._start_check(self.custom_path.text().strip()))
        locate_row.addWidget(btn_verify)

        v.addLayout(locate_row)
        v.addStretch()
        return w

    def _page_installing(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(24, 16, 24, 16)
        v.setSpacing(10)

        lbl = QLabel("Installing gallery-dl…")
        lbl.setStyleSheet("font-size:10pt; font-weight:bold;")
        v.addWidget(lbl)

        self.install_bar = QProgressBar()
        self.install_bar.setRange(0, 0)
        self.install_bar.setFixedHeight(6)
        self.install_bar.setTextVisible(False)
        v.addWidget(self.install_bar)

        self.install_log = QPlainTextEdit()
        self.install_log.setReadOnly(True)
        self.install_log.setObjectName("log_output")
        self.install_log.setFont(QFont("Consolas", 8))
        v.addWidget(self.install_log, stretch=1)
        return w

    def _page_done(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(24, 24, 24, 24)
        v.setSpacing(16)
        v.addStretch()

        self.done_icon = QLabel("✓")
        self.done_icon.setStyleSheet("font-size:32pt; color: palette(highlight);")
        self.done_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        v.addWidget(self.done_icon)

        self.done_headline = QLabel("gallery-dl is ready!")
        self.done_headline.setStyleSheet("font-size:12pt; font-weight:bold;")
        self.done_headline.setAlignment(Qt.AlignmentFlag.AlignCenter)
        v.addWidget(self.done_headline)

        self.done_detail = QLabel("")
        self.done_detail.setStyleSheet("color: palette(mid); font-size:9pt;")
        self.done_detail.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.done_detail.setWordWrap(True)
        v.addWidget(self.done_detail)

        v.addStretch()
        return w

    # ── Logic ─────────────────────────────────────────────────────────────────

    def _start_check(self, cmd: str):
        if not cmd:
            return
        self.stack.setCurrentIndex(0)
        self.check_label.setText(f"Checking for gallery-dl at: {cmd}")
        self.btn_primary.setEnabled(False)

        self._check_worker = _CheckWorker(cmd)
        self._check_thread = QThread()
        self._check_worker.moveToThread(self._check_thread)
        self._check_thread.started.connect(self._check_worker.run)
        self._check_worker.done.connect(self._on_check_done)
        self._check_worker.done.connect(self._check_thread.quit)
        self._check_thread.finished.connect(self._check_worker.deleteLater)
        self._check_thread.finished.connect(self._check_thread.deleteLater)
        self._check_thread.start()

    def _on_check_done(self, found: bool, version: str, cmd: str):
        if found:
            self._found_cmd = cmd
            self._check_ok = True
            parsed = _parse_gdl_version(version)
            outdated = parsed < _GDL_MIN_VERSION and parsed != (0,)

            if outdated:
                _upgrade_hint = (
                    "Run:  pip install --upgrade gallery-dl  to update."
                    if _pip_available() else
                    f"Download the latest release from:\n{CODEBERG_RELEASES_URL}"
                )
                self.done_icon.setText("⚠")
                self.done_icon.setStyleSheet("font-size:32pt; color: palette(bright-text);")
                self.done_headline.setText("gallery-dl found, but it's outdated")
                self.done_detail.setText(
                    f"Found: {cmd}\nVersion: {version}  "                    f"(minimum recommended: {_version_str(_GDL_MIN_VERSION)})\n\n"
                    f"Older versions may fail on sites that have updated their APIs.\n"
                    f"{_upgrade_hint}"
                )
            else:
                self.done_icon.setText("✓")
                self.done_icon.setStyleSheet("font-size:32pt; color: palette(highlight);")
                self.done_headline.setText("gallery-dl is ready!")
                self.done_detail.setText(
                    f"Found: {cmd}\nVersion: {version}\n\n"
                    "You're all set. Click Continue to start using the app."
                )
            self.stack.setCurrentIndex(3)
            self.btn_primary.setEnabled(True)
            self.btn_primary.setText("Continue")
            self.btn_skip.setVisible(False)
        else:
            self.stack.setCurrentIndex(1)
            self.btn_skip.setVisible(True)
            self.btn_primary.setEnabled(False)

    def _browse_executable(self):
        path, _ = QFileDialog.getOpenFileName(self, "Locate gallery-dl executable")
        if path:
            self.custom_path.setText(path)

    def _open_codeberg(self):
        if sys.platform == "win32":
            # os.startfile uses ShellExecute — no subprocess, no CMD flash.
            # webbrowser.open() falls back to subprocess.Popen (no
            # CREATE_NO_WINDOW) if os.startfile raises OSError, which
            # would produce a CMD window briefly.
            os.startfile(CODEBERG_RELEASES_URL)  # type: ignore[attr-defined]
        else:
            import webbrowser
            webbrowser.open(CODEBERG_RELEASES_URL)

    def _start_install(self):
        self.stack.setCurrentIndex(2)
        self.install_log.clear()
        self.btn_primary.setEnabled(False)
        self.btn_skip.setVisible(False)

        self._inst_worker = _InstallWorker()
        self._inst_thread = QThread()
        self._inst_worker.moveToThread(self._inst_thread)
        self._inst_thread.started.connect(self._inst_worker.run)
        self._inst_worker.output.connect(lambda t: self.install_log.appendPlainText(t))
        self._inst_worker.done.connect(self._on_install_done)
        self._inst_worker.done.connect(self._inst_thread.quit)
        self._inst_thread.finished.connect(self._inst_worker.deleteLater)
        self._inst_thread.finished.connect(self._inst_thread.deleteLater)
        self._inst_thread.start()

    def _on_install_done(self, success: bool, message: str):
        self.install_bar.setRange(0, 1)
        self.install_bar.setValue(1)
        if success:
            # Verify the install actually worked
            self._start_check("gallery-dl")
        else:
            self.done_icon.setText("✗")
            self.done_icon.setStyleSheet("font-size:32pt; color: palette(bright-text);")
            self.done_headline.setText("Installation failed")
            if _pip_available():
                _fail_hint = "Try running:  pip install gallery-dl\nin a terminal, then restart the app."
            else:
                _fail_hint = f"Download gallery-dl manually from:\n{CODEBERG_RELEASES_URL}\nThen restart the app."
            self.done_detail.setText(f"{message}\n\n{_fail_hint}")
            self.stack.setCurrentIndex(3)
            self.btn_primary.setEnabled(True)
            self.btn_primary.setText("Close")
            self.btn_skip.setVisible(False)

    def _on_primary(self):
        if self._check_ok:
            from core.app_settings import get_settings
            get_settings().set("gallery_dl_path", self._found_cmd)
            confirm_gdl_cmd(self._found_cmd)
            self.accept()
        else:
            # Reached via the "Close" button after a failed install —
            # no working gallery-dl was ever confirmed, so reject.
            self.reject()

    def _on_skip(self):
        self.reject()

    # ── Public helper ─────────────────────────────────────────────────────────

    @staticmethod
    def check_and_show(parent=None) -> bool:
        """
        Return True if gallery-dl is available, showing the setup wizard if not.

        Call order:
          1. In-memory cache hit  → instant True, no I/O.
          2. PATH / file check    → cheap filesystem check, no subprocess.
          3. Wizard               → only when the binary is genuinely missing.

        Call invalidate_gdl_cmd() from your download code whenever gallery-dl
        fails so that the next call here re-runs the wizard.
        """
        import shutil
        from core.app_settings import resolve_gdl_cmd

        # 1. Already confirmed this session — trust it.
        if _confirmed_cmd is not None:
            return True

        cmd = resolve_gdl_cmd()

        # 2. Lightweight existence check — no subprocess.
        found = (
            shutil.which(cmd) is not None   # plain name: search PATH
            if cmd == "gallery-dl" else
            os.path.isfile(cmd)             # custom path: just stat the file
        )
        if found:
            confirm_gdl_cmd(cmd)
            return True

        # 3. Binary not found — show wizard.
        dlg = FirstRunDialog(parent)
        return dlg.exec() == QDialog.DialogCode.Accepted
