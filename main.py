import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFontDatabase
from PyQt6.QtCore import Qt

from core.app_settings import get_settings, resolve_gdl_cmd
from ui.themes import apply_theme, DEFAULT_THEME_ID
from ui.main_window import MainWindow


def main():
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("PixArchive")
    app.setApplicationVersion("1.6.0")
    app.setQuitOnLastWindowClosed(False)

    s = get_settings()

    theme_id  = s.get("theme_id",  DEFAULT_THEME_ID)
    font_size = s.get("font_size", 10)
    apply_theme(app, theme_id, font_size)

    font = QFontDatabase.systemFont(QFontDatabase.SystemFont.GeneralFont)
    font.setPointSize(font_size)
    app.setFont(font)

    window = MainWindow()

    mgr = window.download_manager
    mgr.set_max_concurrent(s.get("max_concurrent", 1))
    mgr.set_gdl_cmd(resolve_gdl_cmd())
    mgr.set_auto_start(s.get("auto_start_queue", False))

    def _on_setting_changed(key: str, value):
        if key in ("theme_id", "font_size"):
            apply_theme(app, s.get("theme_id", DEFAULT_THEME_ID), s.get("font_size", 10))
            if key == "font_size":
                f = QFontDatabase.systemFont(QFontDatabase.SystemFont.GeneralFont)
                f.setPointSize(int(value))
                app.setFont(f)
        elif key == "max_concurrent":
            mgr.set_max_concurrent(int(value))
        elif key == "gallery_dl_path":
            mgr.set_gdl_cmd(resolve_gdl_cmd())
        elif key == "auto_start_queue":
            mgr.set_auto_start(bool(value))

    s.changed.connect(_on_setting_changed)

    # ── Show window before first-run check so it's visible and responsive ──────
    start_min = s.get("start_minimized", False) and window._tray_manager._tray is not None
    if not start_min:
        window.show()
        window._restore_state()

    # ── First-run check ──────────────────────────────────────────────────────
    # Done after show() so the parent window is visible when the wizard appears
    # and so the app is never frozen/blank during the subprocess check.
    from ui.dialogs.first_run import FirstRunDialog
    FirstRunDialog.check_and_show(window)
    mgr.set_gdl_cmd(resolve_gdl_cmd())

    # ── Update check (background, non-blocking) ──────────────────────────────
    try:
        from core.updater import UpdateChecker, UpdateBanner
        _checker = UpdateChecker(app.applicationVersion(), parent=window)

        def _on_update_available(latest: str, url: str):
            try:
                banner = UpdateBanner(app.applicationVersion(), latest, url, parent=None)
                outer = window.centralWidget().layout()
                outer.insertWidget(outer.count() - 1, banner)
            except Exception:
                pass

        _checker.update_available.connect(_on_update_available)
        _checker.start()
    except Exception:
        pass   # update check is best-effort — never crash the app

    # ── gallery-dl version check (background, non-blocking) ───────────────────
    try:
        from ui.dialogs.first_run import GdlVersionChecker, GdlOutdatedBanner

        _gdl_checker = GdlVersionChecker(parent=window)

        def _on_gdl_outdated(version: str):
            try:
                banner = GdlOutdatedBanner(version)
                outer = window.centralWidget().layout()
                outer.insertWidget(outer.count() - 1, banner)
            except Exception:
                pass

        _gdl_checker.outdated.connect(_on_gdl_outdated)
        _gdl_checker.start()
    except Exception:
        pass   # version check is best-effort — never crash the app

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
