"""
Per-site download option overrides.

Stored in ~/.pixarchive/site_overrides.json as a dict keyed by the
site name returned by url_detector.detect_site() (e.g. "pixiv", "Twitter/X").

Each entry is a partial DownloadOptions dict — only the keys that should
override the job's options are present; missing keys leave the job value alone.
"""
from __future__ import annotations

import json
import os
from dataclasses import fields as dc_fields
from typing import Optional

from core.options import DownloadOptions

OVERRIDES_PATH = os.path.join(
    os.path.expanduser("~"), ".pixarchive", "site_overrides.json"
)

# Which DownloadOptions fields are meaningful to override per-site.
# (zip_archive and dry_run are intentionally excluded — those are job-level.)
OVERRIDABLE_FIELDS: list[str] = [
    "output_dir",
    "filename_pattern",
    "skip_existing",
    "set_mtime",
    "write_metadata",
    "write_tags",
    "write_info_json",
    "item_filter",
    "image_filter",
    "retries",
    "timeout",
    "rate_limit",
    "cookies_from_browser",
    "cookies_file",
    "proxy",
]

_VALID_OPTS = {f.name for f in dc_fields(DownloadOptions)}


def _load() -> dict[str, dict]:
    if not os.path.exists(OVERRIDES_PATH):
        return {}
    try:
        with open(OVERRIDES_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save(data: dict[str, dict]):
    os.makedirs(os.path.dirname(OVERRIDES_PATH), exist_ok=True)
    with open(OVERRIDES_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def list_overrides() -> dict[str, dict]:
    """Return all site overrides as {site_name: {field: value}}."""
    return _load()


def get_override(site_name: str) -> dict:
    """Return the override dict for a specific site, or {}."""
    return _load().get(site_name, {})


def set_override(site_name: str, overrides: dict):
    """Save (or replace) the override dict for a site.

    Only recognised DownloadOptions fields are kept.
    """
    clean = {k: v for k, v in overrides.items() if k in _VALID_OPTS}
    data = _load()
    if clean:
        data[site_name] = clean
    else:
        data.pop(site_name, None)
    _save(data)


def delete_override(site_name: str):
    data = _load()
    if site_name in data:
        del data[site_name]
        _save(data)


def apply_to_options(site_name: Optional[str], opts: DownloadOptions) -> DownloadOptions:
    """Return a new DownloadOptions with site overrides merged in.

    Job-level values take precedence for fields the user explicitly set
    in the download panel. The override only wins for fields that are still
    at their DownloadOptions default — this way a user who changes retries
    in the panel isn't silently overridden.

    Exception: output_dir, filename_pattern, cookies_* and proxy are always
    applied from the override if present, since those are the whole point of
    per-site config.
    """
    if not site_name:
        return opts

    override = get_override(site_name)
    if not override:
        return opts

    # Build the set of per-field defaults for comparison
    defaults = {f.name: f.default for f in dc_fields(DownloadOptions)}

    # Fields that always win from override (structural/auth settings)
    always_override = {
        "output_dir", "filename_pattern",
        "cookies_from_browser", "cookies_file", "proxy",
    }

    kwargs = {}
    for f in dc_fields(DownloadOptions):
        name = f.name
        job_val = getattr(opts, name)
        if name in override:
            ov_val = override[name]
            if name in always_override:
                # Always apply structural overrides
                kwargs[name] = ov_val
            elif job_val == defaults.get(name):
                # Job value is still default → let the site override win
                kwargs[name] = ov_val
            else:
                # User explicitly changed this field → respect their choice
                kwargs[name] = job_val
        else:
            kwargs[name] = job_val

    return DownloadOptions(**kwargs)
