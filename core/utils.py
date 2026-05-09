"""
Pure-Python utility functions extracted from Qt-dependent modules so they
can be imported and tested without a display or PyQt6 installation.
"""
from __future__ import annotations
import re
from datetime import datetime, timedelta
from typing import Optional


# ── URL file parsing (from download_panel) ────────────────────────────────────

def parse_url_file(path: str) -> list[str]:
    """Read a text/CSV file and return a deduplicated list of http(s) URLs.

    Rules:
      - Lines starting with # (after stripping) are treated as comments
      - Empty lines are skipped
      - Only lines that start with http:// or https:// are kept
      - CSV: only the first column is inspected
      - Duplicates are removed, order is preserved
    """
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except Exception as e:
        raise OSError(f"Could not read file: {e}")

    seen: set[str] = set()
    urls: list[str] = []
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "," in line:
            line = line.split(",")[0].strip()
        if line.startswith(("http://", "https://")):
            if line not in seen:
                seen.add(line)
                urls.append(line)
    return urls


# ── Version parsing (from updater and first_run) ──────────────────────────────

def parse_version(v: str) -> tuple[int, ...]:
    """Parse a version string like '1.6.0' or 'v1.6.0' into a comparable tuple."""
    v = v.lstrip("v").strip()
    parts = re.findall(r"\d+", v)
    return tuple(int(p) for p in parts) if parts else (0,)


def version_str(t: tuple[int, ...]) -> str:
    return ".".join(str(x) for x in t)


# ── gallery-dl version constants ──────────────────────────────────────────────

GDL_MIN_VERSION = (1, 26, 0)


# ── Scheduler job helpers (pure logic, no Qt) ─────────────────────────────────

def scheduler_job_is_due(next_run_iso: str, enabled: bool) -> bool:
    if not enabled:
        return False
    return datetime.now() >= datetime.fromisoformat(next_run_iso)


def scheduler_job_advance(
    next_run_iso: str,
    repeat_minutes: Optional[int],
    enabled: bool,
) -> tuple[str, bool]:
    """Return (new_next_run_iso, new_enabled) after advancing a scheduled job."""
    if repeat_minutes:
        nxt = datetime.fromisoformat(next_run_iso) + timedelta(minutes=repeat_minutes)
        now = datetime.now()
        while nxt <= now:
            nxt += timedelta(minutes=repeat_minutes)
        return nxt.isoformat(timespec="seconds"), True
    else:
        return next_run_iso, False
