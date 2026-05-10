<div align="center">
  <img src="assets/icon.png" alt="PixArchive" width="120" height="120"/>
  <br/><br/>
  <img src="https://img.shields.io/badge/PixArchive-1.6.0-FF6363?style=for-the-badge&logoColor=white" alt="PixArchive"/>
<br/><br/>
  <img src="https://img.shields.io/github/actions/workflow/status/shubh-ssj/pixarchive/tests.yml?style=flat-square&label=Tests&color=FF6363" alt="Tests"/>
  &nbsp;
  <img src="https://img.shields.io/badge/Python-3.11%2B-1A1A2E?style=flat-square&logo=python&logoColor=FF6363" alt="Python"/>
  &nbsp;
  <img src="https://img.shields.io/badge/PyQt6-6.4%2B-1A1A2E?style=flat-square&logo=qt&logoColor=FF6363" alt="PyQt6"/>
  &nbsp;
  <img src="https://img.shields.io/badge/License-MIT-1A1A2E?style=flat-square&logoColor=FF6363" alt="MIT License"/>
  &nbsp;
  <img src="https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-1A1A2E?style=flat-square&logoColor=FF6363" alt="Platform"/>
<br/><br/>
<strong>Archive image galleries from 200+ sites — Pixiv, Instagram, Twitter/X, DeviantArt, ArtStation, Flickr, Tumblr, Reddit, and more.</strong>
<br/><br/>
  <a href="#-installation">
    <img src="https://img.shields.io/badge/%E2%86%93%20Download-Windows-FF6363?style=for-the-badge" alt="Download for Windows"/>
  </a>
  &nbsp;
  <a href="#-installation">
    <img src="https://img.shields.io/badge/%E2%86%93%20Download-Linux-2A2A3E?style=for-the-badge" alt="Download for Linux"/>
  </a>
  &nbsp;
  <a href="#-installation">
    <img src="https://img.shields.io/badge/Run%20from-Source-2A2A3E?style=for-the-badge" alt="Run from Source"/>
  </a>
</div>

What is PixArchive?
PixArchive is a desktop utility for downloading and archiving image galleries at scale. It wraps gallery-dl — the gold-standard download engine — inside a clean, modern UI that handles everything from smart URL detection to per-site authentication, scheduling, and history.
Designed for speed. Built for collectors.

Features
<table>
<tr>
<td width="50%" valign="top">
⬇️ Download Panel

Smart URL detection — paste a URL and an instant banner shows the site, supported content types, and auth requirements
Clipboard watcher — switch to PixArchive with a URL on your clipboard and it pastes automatically
Drag & drop — drop URLs or a .txt/.csv file of URLs directly onto the window
Batch URL import — load hundreds of URLs from a text file; CSV-aware, deduplicates automatically
Per-job folder override — change the save folder for one job without touching global settings
22 built-in presets across three groups: Site-specific, Media type, and Workflow

</td>
<td width="50%" valign="top">
📋 Queue & History

Live job cards with progress bars, image/video counts, skipped files, and ETA
Rolling 5-second average download speed in the status bar
Per-job log viewer with level filters and search
Right-click menu: view log, copy URL, open folder, retry, cancel
SQLite-backed history with search, date filter, pagination, and CSV/JSON export

</td>
</tr>
<tr>
<td width="50%" valign="top">
🕐 Scheduler

Schedule any URL: once, hourly, daily, weekly, or custom interval
Missed jobs drift-skip to the next future slot if the app was closed
Full add/edit/delete UI with a calendar date picker

</td>
<td width="50%" valign="top">
🌐 Sites Panel

200+ supported sites in a searchable, filterable card grid
Auth-type badges: OAuth / Cookies / Credentials / Public
Click any card to pre-fill the download URL

</td>
</tr>
<tr>
<td width="50%" valign="top">
⚙️ Config & Accounts

Form editor for common gallery-dl settings + raw JSON editor
Per-site overrides — different output folder, filename pattern, cookies, retries, or proxy per site
Per-site credential management
Config validator with helpful error messages
Config bundle export/import — back up everything as a single .zip via <kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>E</kbd>

</td>
<td width="50%" valign="top">
✨ Everything Else

7 themes: Catppuccin Mocha/Latte/Frappé/Macchiato, Tokyo Night, Nord, Synthwave '84
System tray with rich, batched desktop notifications
Background update checker — notified once per version, never nags
gallery-dl version check on startup
First-run wizard that detects and installs gallery-dl automatically
Auto-migrates settings from ~/.gallery-dl-gui/ on first launch

</td>
</tr>
</table>

⬇️ Installation
Windows
PackageDescriptionpixarchive-setup.exeInstaller — recommended, adds to Start Menupixarchive-portable.zipPortable — extract anywhere, run pixarchive.exe
→ Download from the Releases page. No Python required.
Linux
Download pixarchive.tar.gz from Releases and run ./pixarchive, or use the .AppImage for a fully self-contained single file.
From source — all platforms
Requirements: Python 3.11+ and pip
bashgit clone https://github.com/shubh-ssj/pixarchive.git
cd pixarchive
pip install -r requirements.txt
python main.py
On first launch, PixArchive checks whether gallery-dl is installed and offers to install it for you.

🏗️ Building from source
See BUILD.md for full instructions. Quick start:
bashpip install pyinstaller PyQt6
python download_gallery_dl.py   # downloads gallery-dl binary for bundling

# Windows
build.bat

# Linux / macOS
bash build.sh

⌨️ Keyboard Shortcuts
<div align="center">
ShortcutAction<kbd>Ctrl</kbd> + <kbd>1</kbd>Download panel<kbd>Ctrl</kbd> + <kbd>2</kbd>Queue<kbd>Ctrl</kbd> + <kbd>3</kbd>History<kbd>Ctrl</kbd> + <kbd>4</kbd>Scheduler<kbd>Ctrl</kbd> + <kbd>5</kbd>Sites<kbd>Ctrl</kbd> + <kbd>6</kbd>Config<kbd>Ctrl</kbd> + <kbd>7</kbd>Accounts<kbd>Ctrl</kbd> + <kbd>N</kbd>Go to Download panel<kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>V</kbd>Paste clipboard URL<kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>E</kbd>Export config bundle<kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>I</kbd>Import config bundle<kbd>Ctrl</kbd> + <kbd>,</kbd>Open Settings<kbd>Ctrl</kbd> + <kbd>Q</kbd>Quit<kbd>F1</kbd>Open Help
</div>

📁 App Data Locations
WhatPathSettings~/.pixarchive/settings.jsonPresets~/.pixarchive/presets.jsonPer-site overrides~/.pixarchive/site_overrides.jsonScheduled jobs~/.pixarchive/schedule.jsonHistory~/.pixarchive/history.dbAccounts~/.pixarchive/accounts.jsongallery-dl config (Windows)%APPDATA%\gallery-dl\config.jsongallery-dl config (Linux/macOS)~/.config/gallery-dl/config.json

Upgrading from the old gallery-dl GUI? PixArchive automatically migrates your settings from ~/.gallery-dl-gui/ on first launch — no manual steps needed.


🗂️ Project Structure
<details>
<summary>Expand to view</summary>
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
</details>

🧪 Running Tests
bashpip install pytest
python -m pytest tests/ -v
Tests mock PyQt6 and run without a display — CI runs them on every push.

License
MIT © 2026 SSJ
PixArchive uses gallery-dl (MIT) by Mike Fährmann and PyQt6 (GPL v3) by Riverbank Computing.
