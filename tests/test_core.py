"""
Unit tests for critical PixArchive core logic.
All tests import from core.utils or mock Qt so they run without a display.
Run with:  python -m pytest tests/
"""
from __future__ import annotations

import json
import os
import sys
import zipfile
from datetime import datetime, timedelta
from unittest.mock import MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock PyQt6 before any project imports that need it
qt_mock = MagicMock()
for mod in ["PyQt6", "PyQt6.QtWidgets", "PyQt6.QtCore", "PyQt6.QtGui"]:
    sys.modules.setdefault(mod, qt_mock)
qt_mock.QObject    = object
qt_mock.QTimer     = MagicMock
qt_mock.pyqtSignal = lambda *a, **kw: MagicMock()


# ── parse_url_file ─────────────────────────────────────────────────────────────

from core.utils import parse_url_file

def test_parse_url_file_basic(tmp_path):
    f = tmp_path / "urls.txt"
    f.write_text("https://example.com/a\nhttps://example.com/b\n")
    assert parse_url_file(str(f)) == ["https://example.com/a", "https://example.com/b"]

def test_parse_url_file_strips_comments(tmp_path):
    f = tmp_path / "urls.txt"
    f.write_text("# header\nhttps://example.com/a\n# comment\nhttps://example.com/b\n")
    assert parse_url_file(str(f)) == ["https://example.com/a", "https://example.com/b"]

def test_parse_url_file_deduplicates(tmp_path):
    f = tmp_path / "urls.txt"
    f.write_text("https://example.com/a\nhttps://example.com/a\nhttps://example.com/b\n")
    assert parse_url_file(str(f)) == ["https://example.com/a", "https://example.com/b"]

def test_parse_url_file_skips_non_http(tmp_path):
    f = tmp_path / "urls.txt"
    f.write_text("ftp://example.com\nhttps://good.com/\nnot-a-url\n")
    assert parse_url_file(str(f)) == ["https://good.com/"]

def test_parse_url_file_csv_first_column(tmp_path):
    f = tmp_path / "urls.csv"
    f.write_text("https://example.com/a,label1\nhttps://example.com/b,label2\n")
    assert parse_url_file(str(f)) == ["https://example.com/a", "https://example.com/b"]

def test_parse_url_file_empty(tmp_path):
    f = tmp_path / "urls.txt"
    f.write_text("# just comments\n\n\n")
    assert parse_url_file(str(f)) == []

def test_parse_url_file_preserves_order(tmp_path):
    f = tmp_path / "urls.txt"
    urls = [f"https://example.com/{i}" for i in range(10)]
    f.write_text("\n".join(urls))
    assert parse_url_file(str(f)) == urls

def test_parse_url_file_missing_file():
    import pytest
    with pytest.raises(OSError):
        parse_url_file("/nonexistent/path/urls.txt")


# ── parse_version ──────────────────────────────────────────────────────────────

from core.utils import parse_version, GDL_MIN_VERSION, version_str

def test_parse_version_basic():
    assert parse_version("1.6.0")  == (1, 6, 0)
    assert parse_version("v1.6.0") == (1, 6, 0)

def test_parse_version_empty():
    assert parse_version("") == (0,)
    assert parse_version("not-a-version") == (0,)

def test_parse_version_numeric_comparison():
    assert parse_version("1.10.0") > parse_version("1.6.0")
    assert parse_version("2.0.0")  > parse_version("1.99.99")
    assert parse_version("1.6.1")  > parse_version("1.6.0")
    assert parse_version("1.6.0") == parse_version("1.6.0")

def test_parse_version_with_prefix():
    assert parse_version("gallery-dl 1.26.3") == (1, 26, 3)

def test_gdl_min_version_comparison():
    assert parse_version("1.26.0") <  GDL_MIN_VERSION
    assert parse_version("1.27.0") >= GDL_MIN_VERSION
    assert parse_version("1.32.1") >= GDL_MIN_VERSION

def test_version_str():
    assert version_str((1, 26, 0)) == "1.26.0"
    assert version_str((2, 0, 1))  == "2.0.1"


# ── scheduler helpers ──────────────────────────────────────────────────────────

from core.utils import scheduler_job_is_due, scheduler_job_advance

def test_scheduler_is_due_past():
    past = (datetime.now() - timedelta(minutes=5)).isoformat()
    assert scheduler_job_is_due(past, enabled=True) is True

def test_scheduler_is_due_future():
    future = (datetime.now() + timedelta(minutes=5)).isoformat()
    assert scheduler_job_is_due(future, enabled=True) is False

def test_scheduler_is_due_disabled():
    past = (datetime.now() - timedelta(minutes=5)).isoformat()
    assert scheduler_job_is_due(past, enabled=False) is False

def test_scheduler_advance_oneshot():
    past = (datetime.now() - timedelta(minutes=5)).isoformat()
    _, new_enabled = scheduler_job_advance(past, repeat_minutes=None, enabled=True)
    assert new_enabled is False

def test_scheduler_advance_repeating():
    past = (datetime.now() - timedelta(minutes=5)).isoformat()
    new_run, new_enabled = scheduler_job_advance(past, repeat_minutes=60, enabled=True)
    assert new_enabled is True
    assert datetime.fromisoformat(new_run) > datetime.now()

def test_scheduler_advance_drift_skip():
    very_old = (datetime.now() - timedelta(hours=25)).isoformat()
    new_run, new_enabled = scheduler_job_advance(very_old, repeat_minutes=60, enabled=True)
    assert new_enabled is True
    assert datetime.fromisoformat(new_run) > datetime.now()

def test_scheduler_advance_no_double_fire():
    for hours_ago in [1, 6, 24, 168]:
        past = (datetime.now() - timedelta(hours=hours_ago)).isoformat()
        new_run, _ = scheduler_job_advance(past, repeat_minutes=60, enabled=True)
        assert datetime.fromisoformat(new_run) > datetime.now(), \
            f"next_run in past after {hours_ago}h drift"


# ── config_bundle ──────────────────────────────────────────────────────────────

def _make_bundle_mocks(tmp_path):
    """Set up sys.modules mocks so config_bundle can be imported without Qt."""
    mock_settings = MagicMock()
    mock_settings.SETTINGS_PATH  = str(tmp_path / "settings.json")
    mock_settings.DEFAULTS       = {"theme_id": "dark"}
    sys.modules["core.app_settings"] = mock_settings

    mock_presets = MagicMock()
    mock_presets.PRESETS_PATH    = str(tmp_path / "presets.json")
    mock_presets.BUILTIN_PRESETS = {}
    sys.modules["core.presets"]  = mock_presets

    mock_overrides = MagicMock()
    mock_overrides.OVERRIDES_PATH = str(tmp_path / "overrides.json")
    sys.modules["core.site_overrides"] = mock_overrides

    mock_scheduler = MagicMock()
    mock_scheduler.SCHEDULE_PATH = str(tmp_path / "schedule.json")
    sys.modules["core.scheduler"] = mock_scheduler

    sys.modules.pop("core.config_bundle", None)


def test_export_bundle_creates_zip(tmp_path):
    _make_bundle_mocks(tmp_path)
    (tmp_path / "settings.json").write_text(json.dumps({"theme_id": "dark"}))
    from core import config_bundle
    dest = str(tmp_path / "bundle.zip")
    included = config_bundle.export_bundle(dest)
    assert os.path.exists(dest)
    assert "settings.json" in included
    with zipfile.ZipFile(dest) as zf:
        assert "manifest.json" in zf.namelist()
        manifest = json.loads(zf.read("manifest.json"))
        assert manifest["marker"] == "pixarchive_bundle_v1"

def test_import_bundle_invalid_file(tmp_path):
    _make_bundle_mocks(tmp_path)
    import pytest
    from core import config_bundle
    bad = tmp_path / "bad.zip"
    with zipfile.ZipFile(str(bad), "w") as zf:
        zf.writestr("random.txt", "not a bundle")
    with pytest.raises(ValueError, match="manifest"):
        config_bundle.import_bundle(str(bad))

def test_import_bundle_wrong_marker(tmp_path):
    _make_bundle_mocks(tmp_path)
    import pytest
    from core import config_bundle
    bad = tmp_path / "bad.zip"
    with zipfile.ZipFile(str(bad), "w") as zf:
        zf.writestr("manifest.json", json.dumps({"marker": "wrong"}))
    with pytest.raises(ValueError, match="marker"):
        config_bundle.import_bundle(str(bad))


# ── options ────────────────────────────────────────────────────────────────────

from core.options import DownloadOptions

def test_options_default_retries_not_emitted():
    assert "--retries" not in DownloadOptions().to_argv()
    assert "--timeout"  not in DownloadOptions().to_argv()

def test_options_non_default_retries_emitted():
    argv = DownloadOptions(retries=10).to_argv()
    assert "--retries" in argv and "10" in argv

def test_options_single_source_of_truth():
    from dataclasses import fields as dc_fields
    default = next(f.default for f in dc_fields(DownloadOptions) if f.name == "retries")
    assert "--retries" not in DownloadOptions(retries=default).to_argv()


# ── presets ────────────────────────────────────────────────────────────────────

def test_preset_cache_thread_safety():
    import threading
    from core import presets as preset_mgr
    preset_mgr._invalidate_cache()
    results, errors = [], []
    def worker():
        try:
            results.append(len(preset_mgr.list_grouped()))
        except Exception as e:
            errors.append(e)
    threads = [threading.Thread(target=worker) for _ in range(20)]
    for t in threads: t.start()
    for t in threads: t.join()
    assert not errors
    assert len(set(results)) == 1

def test_list_grouped_covers_all_builtins():
    from core import presets as preset_mgr
    preset_mgr._invalidate_cache()
    all_grouped = [n for _, names in preset_mgr.list_grouped() for n in names]
    for name in preset_mgr.BUILTIN_PRESETS:
        assert name in all_grouped, f"'{name}' missing from list_grouped()"

def test_list_grouped_no_duplicates():
    from core import presets as preset_mgr
    preset_mgr._invalidate_cache()
    all_names = [n for _, names in preset_mgr.list_grouped() for n in names]
    assert len(all_names) == len(set(all_names))
