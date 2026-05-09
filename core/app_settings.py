"""
Application settings — persisted to ~/.pixarchive/settings.json.

Every call to set() immediately writes to disk so that no state is ever
lost between sessions, regardless of how the app exits.
"""
from __future__ import annotations
import json
import os
from typing import Any

from PyQt6.QtCore import QObject, pyqtSignal

SETTINGS_PATH = os.path.join(os.path.expanduser("~"), ".pixarchive", "settings.json")

_OLD_DIR = os.path.join(os.path.expanduser("~"), ".gallery-dl-gui")
_NEW_DIR = os.path.join(os.path.expanduser("~"), ".pixarchive")

def _migrate_config():
    """One-time migration: move ~/.gallery-dl-gui/ → ~/.pixarchive/ if needed."""
    if os.path.isdir(_OLD_DIR) and not os.path.isdir(_NEW_DIR):
        import shutil
        try:
            shutil.copytree(_OLD_DIR, _NEW_DIR)
        except Exception:
            pass   # non-fatal — fresh config will be created

DEFAULTS: dict[str, Any] = {
    # Appearance
    "theme_id":             "catppuccin-mocha",
    "theme_accent":         "#89b4fa",      # legacy, kept for compat
    "font_size":            10,             # pt

    # Layout / UI
    "sidebar_width":        172,
    "show_site_banner":     True,
    "compact_queue_cards":  False,
    "log_max_lines":        3000,

    # Window geometry — saved on close, restored on open
    "remember_window_size": True,
    "window_width":         1200,
    "window_height":        760,
    "window_x":             -1,     # -1 = let the OS decide
    "window_y":             -1,
    "window_maximized":     False,

    # Active panel — saved on close, restored on open
    "active_panel":         0,      # index into NAV_ITEMS

    # Downloads
    "default_output_dir":   "",
    "default_filename":     "",
    "auto_start_queue":     False,
    "confirm_before_stop":  True,
    "max_concurrent":       1,

    # Network
    "default_retries":      4,
    "default_timeout":      30.0,
    "default_rate_limit":   "",
    "default_proxy":        "",

    # Notifications
    "notify_on_complete":   True,
    "notify_on_error":      True,
    "notify_sound":         False,
    "minimize_to_tray":     True,
    "start_minimized":      False,

    # Clipboard & drag-drop
    "clipboard_watch":      True,
    "drag_drop_enabled":    True,

    # Advanced
    "gallery_dl_path":      "gallery-dl",
    "preferred_browser":    "",              # "" = system default
    "last_preset":          "",          # name of last loaded preset
    "check_updates":        True,
    "log_level":            "info",
    "tips_seen_version":       "",  # last version where tips were shown
    "update_notified_version": "",  # last version that triggered an update banner
    "notify_always":           False,  # notify even when window is visible
}


class AppSettings(QObject):
    """
    Singleton settings store.

    - set(key, value)  writes to disk immediately so nothing is ever lost.
    - changed signal fires after every set() for live listeners.
    - save_failed signal fires if a disk write fails (read-only FS, full disk, etc).
    - save() is still public for explicit bulk-flush use, but set() now
      handles persistence automatically.
    """
    changed    = pyqtSignal(str, object)   # (key, new_value)
    save_failed = pyqtSignal(str)           # (error_message,)

    def __init__(self):
        super().__init__()
        _migrate_config()
        self._data: dict[str, Any] = dict(DEFAULTS)
        self._load()

    # ── Disk I/O ─────────────────────────────────────────────────────────────

    def _load(self):
        if not os.path.exists(SETTINGS_PATH):
            return
        try:
            with open(SETTINGS_PATH, encoding="utf-8") as f:
                saved = json.load(f)
            # Only accept keys present in DEFAULTS (forward-compatible)
            for k, v in saved.items():
                if k in DEFAULTS:
                    self._data[k] = v
        except Exception as exc:
            import sys
            print(f"[PixArchive] Warning: could not load settings ({exc}); using defaults.", file=sys.stderr)

    def reload(self):
        """Re-read settings from disk and emit changed for every key that differs."""
        old_data = dict(self._data)
        self._data = dict(DEFAULTS)
        self._load()
        for k, v in self._data.items():
            if v != old_data.get(k):
                self.changed.emit(k, v)

    def save(self):
        """Write all settings to disk. Emits save_failed if write is impossible."""
        os.makedirs(os.path.dirname(SETTINGS_PATH), exist_ok=True)
        try:
            with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2)
        except Exception as exc:
            self.save_failed.emit(str(exc))

    # ── Public API ────────────────────────────────────────────────────────────

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, DEFAULTS.get(key, default))

    def set(self, key: str, value: Any):
        """Set a value, persist it to disk immediately, then notify listeners."""
        self._data[key] = value
        self.save()                     # ← writes every time, nothing is lost
        self.changed.emit(key, value)

    def set_many(self, updates: dict[str, Any]):
        """
        Set multiple values in one shot and write to disk once.
        Use this for bulk updates (e.g. saving the whole settings dialog)
        to avoid N individual disk writes.
        """
        for k, v in updates.items():
            self._data[k] = v
        self.save()
        for k, v in updates.items():
            self.changed.emit(k, v)

    def reset_all(self):
        """Restore every setting to its default and persist."""
        self._data = dict(DEFAULTS)
        self.save()


# Global singleton
_settings = AppSettings()

def get_settings() -> AppSettings:
    return _settings


def resolve_gdl_cmd() -> str:
    """
    Return the path to the gallery-dl executable to use.

    Priority:
      1. User-configured path in settings (if set and non-default)
      2. Bundled binary shipped inside the PyInstaller bundle (bin/gallery-dl[.exe])
      3. 'gallery-dl' on system PATH (default fallback)
    """
    import os, sys

    configured = _settings.get("gallery_dl_path", "gallery-dl")

    # If the user has explicitly set a custom path, honour it
    if configured and configured != "gallery-dl":
        return configured

    # Look for a bundled binary next to the executable (PyInstaller bundle)
    if getattr(sys, "frozen", False):
        # Running inside a PyInstaller bundle
        base = sys._MEIPASS          # type: ignore[attr-defined]
    else:
        # Running from source — check ./bin/ relative to this file
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    bin_name = "gallery-dl.exe" if sys.platform == "win32" else "gallery-dl"
    bundled  = os.path.join(base, "bin", bin_name)

    if os.path.isfile(bundled):
        return bundled

    # Fall back to system PATH
    return "gallery-dl"
