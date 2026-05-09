"""
Config bundle: export and import PixArchive settings as a single .zip file.

Bundle contents:
  settings.json       — app settings
  presets.json        — user presets (built-ins are excluded; they ship with the app)
  site_overrides.json — per-site download overrides
  schedule.json       — scheduled jobs

history.db is intentionally excluded — it's a local log, not portable config.
"""
from __future__ import annotations

import json
import os
import zipfile
from datetime import datetime
from typing import Optional

from core.app_settings import SETTINGS_PATH, DEFAULTS
from core.presets import PRESETS_PATH, BUILTIN_PRESETS
from core.site_overrides import OVERRIDES_PATH
from core.scheduler import SCHEDULE_PATH

# Files to include in the bundle, keyed by the name they'll have inside the zip
_BUNDLE_FILES: dict[str, str] = {
    "settings.json":       SETTINGS_PATH,
    "presets.json":        PRESETS_PATH,
    "site_overrides.json": OVERRIDES_PATH,
    "schedule.json":       SCHEDULE_PATH,
}

_BUNDLE_MARKER = "pixarchive_bundle_v1"


def export_bundle(dest_path: str) -> list[str]:
    """Write a .zip bundle to dest_path.

    Returns a list of which files were included (some may not exist yet).
    Raises on I/O errors.
    """
    included: list[str] = []

    with zipfile.ZipFile(dest_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        # Write a manifest so we can detect this is a real PixArchive bundle
        manifest = {
            "marker":    _BUNDLE_MARKER,
            "exported":  datetime.now().isoformat(timespec="seconds"),
            "contents":  [],
        }

        for bundle_name, fs_path in _BUNDLE_FILES.items():
            if not os.path.exists(fs_path):
                continue

            # For presets.json: strip built-in presets — only export user presets
            if bundle_name == "presets.json":
                try:
                    with open(fs_path, encoding="utf-8") as f:
                        all_presets = json.load(f)
                    user_presets = {k: v for k, v in all_presets.items()
                                    if k not in BUILTIN_PRESETS}
                    if not user_presets:
                        continue   # nothing user-defined to export
                    zf.writestr(bundle_name, json.dumps(user_presets, indent=2))
                except Exception:
                    continue
            else:
                zf.write(fs_path, arcname=bundle_name)

            included.append(bundle_name)
            manifest["contents"].append(bundle_name)

        zf.writestr("manifest.json", json.dumps(manifest, indent=2))

    return included


def import_bundle(src_path: str, merge: bool = True) -> dict[str, str]:
    """Import a bundle from src_path.

    Args:
        src_path:  path to the .zip bundle
        merge:     if True, merge into existing config (user presets merged,
                   settings merged key-by-key). If False, overwrite entirely.

    Returns a dict {bundle_name: "imported" | "skipped" | "error: …"}.
    Raises ValueError if the file is not a valid PixArchive bundle.
    Raises on I/O errors opening the zip.
    """
    results: dict[str, str] = {}

    with zipfile.ZipFile(src_path, "r") as zf:
        names = zf.namelist()

        # Validate bundle marker
        if "manifest.json" not in names:
            raise ValueError("Not a valid PixArchive bundle (missing manifest.json).")
        manifest = json.loads(zf.read("manifest.json"))
        if manifest.get("marker") != _BUNDLE_MARKER:
            raise ValueError("Not a valid PixArchive bundle (wrong marker).")

        for bundle_name, fs_path in _BUNDLE_FILES.items():
            if bundle_name not in names:
                results[bundle_name] = "skipped (not in bundle)"
                continue

            try:
                raw = zf.read(bundle_name).decode("utf-8")
                incoming = json.loads(raw)
            except Exception as e:
                results[bundle_name] = f"error: {e}"
                continue

            try:
                os.makedirs(os.path.dirname(fs_path), exist_ok=True)

                if not merge:
                    # Overwrite entirely
                    with open(fs_path, "w", encoding="utf-8") as f:
                        json.dump(incoming, f, indent=2)

                elif bundle_name == "settings.json":
                    # Merge: only import keys present in DEFAULTS, don't
                    # clobber window geometry or session state
                    _SKIP_ON_IMPORT = {
                        "window_width", "window_height", "window_x", "window_y",
                        "window_maximized", "active_panel", "last_preset",
                    }
                    existing: dict = {}
                    if os.path.exists(fs_path):
                        try:
                            with open(fs_path, encoding="utf-8") as f:
                                existing = json.load(f)
                        except Exception:
                            pass
                    for k, v in incoming.items():
                        if k in DEFAULTS and k not in _SKIP_ON_IMPORT:
                            existing[k] = v
                    with open(fs_path, "w", encoding="utf-8") as f:
                        json.dump(existing, f, indent=2)

                elif bundle_name == "presets.json":
                    # Merge: add/replace user presets, never touch built-ins
                    existing = {}
                    if os.path.exists(fs_path):
                        try:
                            with open(fs_path, encoding="utf-8") as f:
                                existing = json.load(f)
                        except Exception:
                            pass
                    # incoming only contains user presets (built-ins stripped on export)
                    existing.update(incoming)
                    with open(fs_path, "w", encoding="utf-8") as f:
                        json.dump(existing, f, indent=2)

                elif bundle_name == "site_overrides.json":
                    # Merge: add/replace entries
                    existing = {}
                    if os.path.exists(fs_path):
                        try:
                            with open(fs_path, encoding="utf-8") as f:
                                existing = json.load(f)
                        except Exception:
                            pass
                    existing.update(incoming)
                    with open(fs_path, "w", encoding="utf-8") as f:
                        json.dump(existing, f, indent=2)

                elif bundle_name == "schedule.json":
                    # Merge by job ID: add jobs that don't already exist
                    existing_jobs: list = []
                    if os.path.exists(fs_path):
                        try:
                            with open(fs_path, encoding="utf-8") as f:
                                existing_jobs = json.load(f)
                        except Exception:
                            pass
                    existing_ids = {j.get("id") for j in existing_jobs}
                    for job in incoming:
                        if job.get("id") not in existing_ids:
                            existing_jobs.append(job)
                    with open(fs_path, "w", encoding="utf-8") as f:
                        json.dump(existing_jobs, f, indent=2)

                results[bundle_name] = "imported"

            except Exception as e:
                results[bundle_name] = f"error: {e}"

    return results


def suggested_filename() -> str:
    """Return a timestamped default export filename."""
    ts = datetime.now().strftime("%Y%m%d-%H%M")
    return f"pixarchive-config-{ts}.zip"
