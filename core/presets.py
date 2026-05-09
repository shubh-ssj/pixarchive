"""
Preset system: save/load named DownloadOptions profiles to disk.
Stored as JSON in ~/.pixarchive/presets.json
"""
from __future__ import annotations
import json
import os
import threading
from dataclasses import asdict, fields
from typing import Optional

from core.options import DownloadOptions


PRESETS_PATH = os.path.join(os.path.expanduser("~"), ".pixarchive", "presets.json")

BUILTIN_PRESETS: dict[str, dict] = {
    # ── Site-specific ──────────────────────────────────────────────────────────
    "Pixiv – high-res originals": {
        "filename_pattern": "{user[id]}/{id}_p{num}.{extension}",
        "skip_existing": True,
        "write_metadata": True,
        "retries": 6,
        "timeout": 45.0,
    },
    "Reddit – images only": {
        "item_filter": 'extension in ("jpg","jpeg","png","gif","webp")',
        "skip_existing": True,
        "retries": 4,
    },
    "Twitter/X – media archive": {
        "filename_pattern": "{author[name]}/{tweet_id}_{num}.{extension}",
        "skip_existing": True,
        "write_metadata": True,
        "set_mtime": True,
        "retries": 6,
        "timeout": 45.0,
    },
    "Instagram – posts & reels": {
        "filename_pattern": "{username}/{shortcode}_{num}.{extension}",
        "skip_existing": True,
        "write_metadata": True,
        "set_mtime": True,
        "retries": 5,
        "timeout": 45.0,
    },
    "DeviantArt – full gallery": {
        "filename_pattern": "{username}/{index}_{title}.{extension}",
        "skip_existing": True,
        "write_metadata": True,
        "write_tags": True,
        "set_mtime": True,
        "retries": 5,
    },
    "ArtStation – portfolio": {
        "filename_pattern": "{username}/{id}_{title}.{extension}",
        "skip_existing": True,
        "write_metadata": True,
        "set_mtime": True,
        "retries": 5,
        "timeout": 45.0,
    },
    "Tumblr – blog archive": {
        "filename_pattern": "{blog[name]}/{id}_{num}.{extension}",
        "skip_existing": True,
        "write_metadata": True,
        "write_info_json": True,
        "set_mtime": True,
        "retries": 5,
    },
    "Flickr – photostream": {
        "filename_pattern": "{user[path_alias]}/{id}_{title}.{extension}",
        "skip_existing": True,
        "write_metadata": True,
        "set_mtime": True,
        "retries": 4,
        "timeout": 40.0,
    },
    "Naver Webtoon": {
        "filename_pattern": "{title}/{episode_id}_{episode}/{num:>03}.{extension}",
        "zip_archive": False,
        "skip_existing": True,
        "write_info_json": True,
        "set_mtime": True,
        "retries": 6,
        "timeout": 45.0,
    },
    "Naver Webtoon – zipped episodes": {
        "filename_pattern": "{title}/{episode_id}_{episode}/{num:>03}.{extension}",
        "zip_archive": True,
        "skip_existing": True,
        "write_info_json": True,
        "set_mtime": True,
        "retries": 6,
        "timeout": 45.0,
    },

    # ── Workflow ───────────────────────────────────────────────────────────────
    "Dry run / preview": {
        "dry_run": True,
        "verbose": True,
    },
    "Archive + metadata": {
        "write_metadata": True,
        "write_info_json": True,
        "set_mtime": True,
        "skip_existing": True,
    },
    "Full offline archive": {
        "write_metadata": True,
        "write_tags": True,
        "write_info_json": True,
        "set_mtime": True,
        "skip_existing": True,
        "retries": 6,
        "timeout": 60.0,
    },
    "Images only – no videos": {
        "item_filter": 'extension in ("jpg","jpeg","png","gif","webp","tiff","bmp","avif","jxl","heic","heif")',
        "skip_existing": True,
    },
    "Videos only": {
        "item_filter": 'extension in ("mp4","webm","mov","avi","mkv","m4v","flv","ts","wmv","3gp")',
        "skip_existing": True,
    },
    "Videos + thumbnails": {
        "item_filter": 'extension in ("mp4","webm","mov","avi","mkv","m4v","flv","ts","wmv","3gp","jpg","jpeg","png","webp")',
        "skip_existing": True,
        "write_metadata": True,
        "set_mtime": True,
    },
    "Mixed media – images & videos": {
        "skip_existing": True,
        "write_metadata": True,
        "set_mtime": True,
        "retries": 5,
        "timeout": 45.0,
    },
    "Latest 50 items": {
        "index_range": "1-50",
        "skip_existing": True,
    },
    "Slow connection / metered": {
        "rate_limit": "200k",
        "retries": 8,
        "timeout": 60.0,
        "skip_existing": True,
    },
    "Resume interrupted": {
        "skip_existing": True,
        "retries": 10,
        "timeout": 60.0,
    },
    "Quick grab – no extras": {
        "skip_existing": False,
        "write_metadata": False,
        "write_info_json": False,
        "retries": 2,
        "timeout": 15.0,
    },
}


# Canonical group order for built-in presets.
# Any preset name not listed here falls into "Workflow" automatically.
BUILTIN_GROUPS: dict[str, list[str]] = {
    "Site-specific": [
        "Pixiv – high-res originals",
        "Twitter/X – media archive",
        "Instagram – posts & reels",
        "DeviantArt – full gallery",
        "ArtStation – portfolio",
        "Tumblr – blog archive",
        "Flickr – photostream",
        "Reddit – images only",
        "Naver Webtoon",
        "Naver Webtoon – zipped episodes",
    ],
    "Media type": [
        "Images only – no videos",
        "Videos only",
        "Videos + thumbnails",
        "Mixed media – images & videos",
    ],
    "Workflow": [
        "Archive + metadata",
        "Full offline archive",
        "Latest 50 items",
        "Slow connection / metered",
        "Resume interrupted",
        "Quick grab – no extras",
        "Dry run / preview",
    ],
}


_cache: dict[str, dict] | None = None
_cache_lock = threading.Lock()


def _load_all() -> dict[str, dict]:
    global _cache
    with _cache_lock:
        if _cache is not None:
            return _cache
        data: dict[str, dict] = {}
        data.update(BUILTIN_PRESETS)
        if os.path.exists(PRESETS_PATH):
            try:
                with open(PRESETS_PATH, encoding="utf-8") as f:
                    user = json.load(f)
                data.update(user)
            except Exception:
                pass
        _cache = data
        return _cache


def _invalidate_cache():
    global _cache
    with _cache_lock:
        _cache = None


def _save_user(name: str, opts_dict: dict):
    os.makedirs(os.path.dirname(PRESETS_PATH), exist_ok=True)
    existing: dict = {}
    if os.path.exists(PRESETS_PATH):
        try:
            with open(PRESETS_PATH, encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            pass
    existing[name] = opts_dict
    with open(PRESETS_PATH, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2)
    _invalidate_cache()


def _delete_user(name: str):
    if name in BUILTIN_PRESETS:
        return  # can't delete builtins
    if not os.path.exists(PRESETS_PATH):
        return
    try:
        with open(PRESETS_PATH, encoding="utf-8") as f:
            existing = json.load(f)
        existing.pop(name, None)
        with open(PRESETS_PATH, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2)
        _invalidate_cache()
    except Exception:
        pass


def list_presets() -> list[str]:
    return list(_load_all().keys())


def list_grouped() -> list[tuple[str | None, list[str]]]:
    """Return presets as [(group_label, [name, ...]), ...].

    Built-ins come first in their declared group order.
    User presets are collected into a final "My presets" group.
    group_label is None for a plain separator row (unused currently).
    """
    all_names = set(_load_all().keys())
    user_names = all_names - set(BUILTIN_PRESETS.keys())

    groups: list[tuple[str | None, list[str]]] = []
    seen: set[str] = set()

    for group_label, members in BUILTIN_GROUPS.items():
        present = [n for n in members if n in all_names]
        if present:
            groups.append((group_label, present))
            seen.update(present)

    # Any built-ins not in BUILTIN_GROUPS (shouldn't happen, but safe fallback)
    orphan_builtins = [n for n in BUILTIN_PRESETS if n not in seen]
    if orphan_builtins:
        groups.append(("Other", orphan_builtins))

    if user_names:
        groups.append(("My presets", sorted(user_names)))

    return groups


def load_preset(name: str) -> Optional[DownloadOptions]:
    all_p = _load_all()
    if name not in all_p:
        return None
    d = all_p[name]
    # Only pass keys that DownloadOptions accepts
    valid = {f.name for f in fields(DownloadOptions)}
    filtered = {k: v for k, v in d.items() if k in valid}
    return DownloadOptions(**filtered)


def save_preset(name: str, opts: DownloadOptions):
    _save_user(name, asdict(opts))


def delete_preset(name: str):
    _delete_user(name)


def is_builtin(name: str) -> bool:
    return name in BUILTIN_PRESETS
