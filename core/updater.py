"""
Update checker — fetches the latest release from GitHub and notifies the user
if a newer version is available.

Runs in a QThread so it never blocks the UI. The result is emitted via a signal
and shown as a dismissible banner in the main window.

GitHub API endpoint:
  https://api.github.com/repos/{owner}/{repo}/releases/latest

The banner is shown only once per discovered version so it doesn't nag.
"""
from __future__ import annotations

import json
import urllib.request
from typing import Optional

from PyQt6.QtCore import QObject, QThread, pyqtSignal
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton

from core.app_settings import get_settings

# TODO: set these to the real GitHub org/repo before shipping
# e.g. GITHUB_OWNER = "mikf", GITHUB_REPO = "pixarchive"
GITHUB_OWNER = "shubh-ssj"
GITHUB_REPO  = "pixarchive"
API_URL      = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"

_TIMEOUT = 8   # seconds


def _parse_version(v: str) -> tuple[int, ...]:
    """Delegate to core.utils.parse_version — tested independently of Qt."""
    from core.utils import parse_version
    return parse_version(v)


class _AppFetchWorker(QObject):
    finished = pyqtSignal(str, str)   # (latest_version, release_url)
    failed   = pyqtSignal(str)        # (error_message,)

    def run(self):
        try:
            req = urllib.request.Request(
                API_URL,
                headers={
                    "Accept":     "application/vnd.github+json",
                    "User-Agent": "PixArchive-UpdateChecker/1.0",
                }
            )
            with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            tag      = data.get("tag_name", "")
            html_url = data.get("html_url", "")
            if tag:
                self.finished.emit(tag, html_url)
            else:
                self.failed.emit("No tag in response")
        except Exception as e:
            self.failed.emit(str(e))


class AppUpdateChecker(QObject):
    """
    Run a background update check. Connect update_available to show a banner.

        checker = UpdateChecker("1.6.0", parent=window)
        checker.update_available.connect(window.show_update_banner)
        checker.start()
    """
    update_available = pyqtSignal(str, str)   # (latest_version, release_url)

    def __init__(self, current_version: str, parent=None):
        super().__init__(parent)
        self._current = current_version
        self._thread  = QThread(self)
        self._worker  = _AppFetchWorker()
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_result)
        self._worker.failed.connect(self._on_fail)
        self._worker.finished.connect(self._thread.quit)
        self._worker.failed.connect(self._thread.quit)
        self._thread.finished.connect(self._worker.deleteLater)

    def start(self):
        if not get_settings().get("check_updates", True):
            return
        self._thread.start()

    def _on_result(self, latest: str, url: str):
        if _parse_version(latest) > _parse_version(self._current):
            seen = get_settings().get("update_notified_version", "")
            if _parse_version(latest) > _parse_version(seen):
                self.update_available.emit(latest, url)

    def _on_fail(self, _err: str):
        pass   # silently ignore network errors and 404s — update check is best-effort
        # (a 404 will occur until GITHUB_OWNER/GITHUB_REPO are set to the real repo)


class UpdateBanner(QWidget):
    """Slim dismissible banner shown when a new version is available."""

    def __init__(self, current: str, latest: str, url: str, parent=None):
        super().__init__(parent)
        self.setObjectName("update_banner")
        self.setStyleSheet(
            "#update_banner { background: palette(highlight); }"
            "#update_banner QLabel { color: palette(highlighted-text); font-size:8.5pt; }"
            "#update_banner QPushButton { color: palette(highlighted-text); font-size:8pt; "
            "background: transparent; border: 1px solid palette(highlighted-text); "
            "border-radius: 3px; padding: 1px 8px; }"
        )
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 5, 10, 5)
        layout.setSpacing(10)

        lbl = QLabel(f"\U0001f389  PixArchive {latest} is available  (you have {current})")
        layout.addWidget(lbl, stretch=1)

        if url:
            btn_dl = QPushButton("View release")
            btn_dl.clicked.connect(lambda: self._open_url(url))
            layout.addWidget(btn_dl)

        btn_skip = QPushButton("Skip this version")
        btn_skip.clicked.connect(lambda: self._skip(latest))
        layout.addWidget(btn_skip)

        btn_x = QPushButton("\u2715")
        btn_x.setFixedWidth(24)
        btn_x.clicked.connect(self._dismiss)
        layout.addWidget(btn_x)

    def _open_url(self, url: str):
        from PyQt6.QtGui import QDesktopServices
        from PyQt6.QtCore import QUrl
        QDesktopServices.openUrl(QUrl(url))

    def _skip(self, version: str):
        get_settings().set("update_notified_version", version)
        self.setVisible(False)

    def _dismiss(self):
        self.setVisible(False)


# ── gallery-dl update checker (original — used by main_window.py) ─────────────
# Checks whether the installed gallery-dl is up to date by comparing
# the running version against the latest Codeberg release.

class _GdlFetchWorker(QObject):
    done   = pyqtSignal(str)   # latest version tag
    failed = pyqtSignal(str)   # error message

    def run(self):
        try:
            req = urllib.request.Request(
                "https://codeberg.org/api/v1/repos/mikf/gallery-dl/releases?limit=1",
                headers={"Accept": "application/json", "User-Agent": "PixArchive/1.0"}
            )
            with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
                releases = json.loads(resp.read())
            tag = releases[0].get("tag_name", "") if releases else ""
            if tag:
                self.done.emit(tag)
            else:
                self.failed.emit("No release found")
        except Exception as e:
            self.failed.emit(str(e))


class UpdateChecker(QObject):
    """
    Checks whether the installed gallery-dl is up to date.
    Used by main_window.py for both automatic and manual update checks.

    Signals:
        update_available(installed, latest) — newer version exists
        up_to_date(installed)               — already on latest
        check_failed(message)               — network or parse error
    """
    update_available = pyqtSignal(str, str)   # (installed_version, latest_version)
    up_to_date       = pyqtSignal(str)         # (installed_version,)
    check_failed     = pyqtSignal(str)         # (error_message,)

    def __init__(self, gdl_cmd: str = "gallery-dl", parent=None):
        super().__init__(parent)
        self._gdl_cmd = gdl_cmd
        self._thread  = QThread(self)
        self._worker  = _GdlFetchWorker()
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.done.connect(self._on_latest)
        self._worker.failed.connect(self._on_fail)
        self._worker.done.connect(self._thread.quit)
        self._worker.failed.connect(self._thread.quit)
        self._thread.finished.connect(self._worker.deleteLater)

    def check(self):
        """Start the background check."""
        self._thread.start()

    def _on_latest(self, latest_tag: str):
        # Get the installed version by running gallery-dl --version
        try:
            import subprocess, sys
            _extra = {"creationflags": subprocess.CREATE_NO_WINDOW} if sys.platform == "win32" else {}
            r = subprocess.run(
                [self._gdl_cmd, "--version"],
                capture_output=True, text=True, timeout=5,
                **_extra,
            )
            installed = (r.stdout or r.stderr).strip()
        except Exception:
            installed = "unknown"

        installed_v = _parse_version(installed)
        latest_v    = _parse_version(latest_tag)

        if latest_v > installed_v:
            self.update_available.emit(installed, latest_tag)
        else:
            self.up_to_date.emit(installed)

    def _on_fail(self, err: str):
        self.check_failed.emit(err)
