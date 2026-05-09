<div align="center">
  <img src="assets/icon_full.png" alt="PixArchive" height="120"/>
  <br/>
  <strong>PixArchive</strong>
  <br/>
  An image downloader utility for archiving galleries and collections from 200+ websites.
  <br/><br/>

  ![Tests](https://github.com/shubh-ssj/pixarchive/actions/workflows/tests.yml/badge.svg)
  ![Python](https://img.shields.io/badge/Python-3.11%2B-blue?style=flat-square)
  ![PyQt6](https://img.shields.io/badge/PyQt6-6.4%2B-green?style=flat-square)
  ![License](https://img.shields.io/badge/License-MIT-purple?style=flat-square)
  ![Version](https://img.shields.io/badge/Version-1.6.0-orange?style=flat-square)
</div>

---

<!-- Screenshots go here — see SCREENSHOTS section at the bottom of this file -->

## What is PixArchive?

PixArchive is a desktop utility for downloading and archiving image galleries from sites like Pixiv, Instagram, Twitter/X, DeviantArt, ArtStation, Flickr, Tumblr, Reddit, Naver Webtoon, and 200+ more. It uses [gallery-dl](https://github.com/mikf/gallery-dl) as its download engine and wraps it in a clean, modern UI that handles everything from URL detection to per-site authentication.

## Features

### Download panel
- **Smart URL detection** — paste a URL and a banner instantly shows the site name, supported content types, and whether authentication is needed
- **Clipboard watcher** — switch to PixArchive with a URL on your clipboard and it pastes automatically
- **Drag & drop** — drop URLs or a `.txt`/`.csv` file of URLs directly onto the window
- **Batch URL import** — load hundreds of URLs from a text file in one click; CSV-aware, deduplicates automatically
- **Per-job folder override** — change the save folder for a single job without touching your global settings
- **22 built-in presets** in three groups (Site-specific, Media type, Workflow) — covering Pixiv, Twitter/X, Instagram, DeviantArt, ArtStation, Tumblr, Flickr, Naver Webtoon, and common workflows
- **Full options** — output directory, filename patterns, filters, rate limiting, retries, proxy, cookie extraction from your browser, and more

### Queue & history
- Live job cards with progress bars, image/video split counts, skipped file counts, and ETA
- Live download speed in the status bar (rolling 5-second average)
- Per-job log viewer with level filters and search
- Right-click menu: view log, copy URL, open output folder, retry, cancel
- SQLite-backed history with search, date filter, pagination, and CSV/JSON export

### Scheduler
- Schedule any URL to download at a specific time — once, hourly, daily, weekly, or custom interval
- Missed jobs drift-skip to the next future slot if the app was closed
- Full add/edit/delete UI with a calendar date picker

### Sites panel
- 200+ supported sites in a searchable, filterable card grid
- Auth type badges (OAuth / Cookies / Credentials / Public)
- Click any card to pre-fill the download URL

### Config & accounts
- Form editor for common gallery-dl settings + raw JSON editor
- **Per-site overrides** — set a different output folder, filename pattern, cookies, retries, or proxy for specific sites — applied automatically to every matching job
- Per-site credential management
- Config validator with helpful error messages
- **Config bundle export/import** — back up and restore all your presets, overrides, and scheduled jobs as a single `.zip` file (File → Export/Import config bundle)

### Everything else
- 7 themes: Catppuccin Mocha/Latte/Frappé/Macchiato, Tokyo Night, Nord, Synthwave '84
- System tray with batched, rich desktop notifications (shows image/video counts per job)
- Background update checker — notified once per new version, never nags
- gallery-dl version check on startup — warns if your version is outdated
- Keyboard shortcuts for everything
- First-run wizard that detects and installs gallery-dl automatically
- Settings migration from `~/.gallery-dl-gui/` for users upgrading from the old GUI

## Installation

### From source (all platforms)

**Requirements:** Python 3.11+ and pip

```bash
git clone https://github.com/shubh-ssj/pixarchive.git
cd pixarchive
pip install -r requirements.txt
python main.py
```

On first launch, PixArchive will check whether gallery-dl is installed and offer to install it for you if not.

### Windows — installer

Download `pixarchive-setup.exe` from the [Releases](https://github.com/shubh-ssj/pixarchive/releases) page. No Python required.

### Windows — portable

Download `pixarchive-portable.zip`, extract anywhere, run `pixarchive.exe`. No install needed.

### Linux

Download `pixarchive.tar.gz` from [Releases](https://github.com/shubh-ssj/pixarchive/releases), extract, and run `./pixarchive`. Or use the `.AppImage` for a fully self-contained single file.

### macOS

Download `pixarchive.tar.gz` or `pixarchive.dmg` from [Releases](https://github.com/shubh-ssj/pixarchive/releases).

> **macOS note:** If Gatekeeper blocks the app, right-click → Open to bypass the warning. For mass distribution, code signing is required.

## Building from source

See [BUILD.md](BUILD.md) for full instructions. The short version:

```bash
pip install pyinstaller PyQt6
python download_gallery_dl.py   # downloads the gallery-dl binary to bundle

# Windows
build.bat

# Linux / macOS
bash build.sh
```

## Keyboard shortcuts

| Shortcut | Action |
|---|---|
| `Ctrl+1` | Download panel |
| `Ctrl+2` | Queue |
| `Ctrl+3` | History |
| `Ctrl+4` | Scheduler |
| `Ctrl+5` | Sites |
| `Ctrl+6` | Config |
| `Ctrl+7` | Accounts |
| `Ctrl+N` | Go to Download panel |
| `Ctrl+Shift+V` | Paste clipboard URL |
| `Ctrl+Shift+E` | Export config bundle |
| `Ctrl+Shift+I` | Import config bundle |
| `Ctrl+,` | Open Settings |
| `Ctrl+Q` | Quit |
| `F1` | Open Help |

## App data locations

| What | Path |
|---|---|
| Settings | `~/.pixarchive/settings.json` |
| Presets | `~/.pixarchive/presets.json` |
| Per-site overrides | `~/.pixarchive/site_overrides.json` |
| Scheduled jobs | `~/.pixarchive/schedule.json` |
| History | `~/.pixarchive/history.db` |
| Accounts | `~/.pixarchive/accounts.json` |
| gallery-dl config | `%APPDATA%\gallery-dl\config.json` (Windows) · `~/.config/gallery-dl/config.json` (Linux/macOS) |

## Project structure

```
pixarchive/
├── main.py
├── requirements.txt
├── download_gallery_dl.py   # downloads gallery-dl binary for bundling
├── pixarchive.spec          # PyInstaller build spec
├── build.bat                # Windows build script
├── build.sh                 # Linux / macOS build script
├── assets/
│   ├── icon.png             # App icon (no text, tight crop)
│   ├── icon_full.png        # Full logo with wordmark
│   └── icon.ico             # Multi-size ICO for Windows
├── core/
│   ├── app_settings.py      # Persistent settings
│   ├── config_bundle.py     # Export / import settings bundle
│   ├── download_manager.py
│   ├── job.py               # Download job + subprocess management
│   ├── options.py           # DownloadOptions dataclass + CLI builder
│   ├── presets.py           # Named option presets
│   ├── scheduler.py         # Scheduled download jobs
│   ├── site_overrides.py    # Per-site download option overrides
│   ├── sites.py             # 200+ site definitions
│   ├── stats.py             # Session statistics + speed tracking
│   ├── updater.py           # Background update checker
│   ├── url_detector.py      # URL → site regex detection
│   └── utils.py             # Pure-Python helpers (testable without Qt)
├── installer/
│   └── pixarchive.iss       # Inno Setup installer script
├── tests/
│   └── test_core.py         # Unit tests (run with pytest)
└── ui/
    ├── main_window.py
    ├── themes.py
    ├── tip_bar.py           # Feature discovery banner
    ├── tray.py              # System tray + notifications
    ├── status_bar.py
    ├── panels/
    │   ├── download_panel.py
    │   ├── queue_panel.py
    │   ├── history_panel.py
    │   ├── scheduler_panel.py
    │   ├── site_overrides_widget.py
    │   ├── sites_panel.py
    │   ├── config_panel.py
    │   └── accounts_panel.py
    └── dialogs/
        ├── first_run.py
        ├── settings_dialog.py
        ├── help_dialog.py
        ├── about_dialog.py
        └── job_log_dialog.py
```

## Running tests

```bash
pip install pytest
python -m pytest tests/ -v
```

Tests mock PyQt6 and run without a display — CI runs them on every push.

## License

MIT — Copyright © 2026 SSJ · [github.com/shubh-ssj](https://github.com/shubh-ssj)

PixArchive uses [gallery-dl](https://github.com/mikf/gallery-dl) (MIT) by Mike Fährmann and [PyQt6](https://riverbankcomputing.com/software/pyqt/) (GPL v3) by Riverbank Computing.
