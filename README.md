<div align="center">
  <img src="https://raw.githubusercontent.com/shubh-ssj/pixarchive/main/assets/pixarchive_banner_wrapped.svg" width="100%" alt="PixArchive Banner"/>
  
  <br/><br/>
  
  <img src="https://raw.githubusercontent.com/shubh-ssj/pixarchive/main/assets/icon.png" width="128" height="128" alt="PixArchive Logo"/>
  
  <h1 style="margin: 12px 0 8px; font-size: 42px; font-weight: 700; background: linear-gradient(90deg, #FF6363, #FF8A8A); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
    PixArchive
  </h1>
  
  <p style="font-size: 20px; color: #E4E4E4; max-width: 720px; margin: 0 auto;">
    Archive image galleries from 200+ sites — beautifully and at scale.
  </p>

  <br/>

  <img src="https://img.shields.io/badge/PixArchive-1.6.0-FF6363?style=for-the-badge&logoColor=white" alt="Version"/>
  <img src="https://img.shields.io/github/actions/workflow/status/shubh-ssj/pixarchive/tests.yml?style=for-the-badge&label=Tests&color=FF6363" alt="Tests"/>
  <img src="https://img.shields.io/badge/Python-3.11%2B-1A1A2E?style=for-the-badge&logo=python&logoColor=FF6363" alt="Python"/>
  <img src="https://img.shields.io/badge/PyQt6-6.4%2B-1A1A2E?style=for-the-badge&logo=qt&logoColor=FF6363" alt="PyQt6"/>
  <img src="https://img.shields.io/badge/License-MIT-1A1A2E?style=for-the-badge&logoColor=FF6363" alt="MIT"/>

  <br/><br/>

  <a href="#-installation">
    <img src="https://img.shields.io/badge/%E2%86%93_Download_for_Windows-FF6363?style=for-the-badge&logo=windows&logoColor=white" height="46" alt="Download Windows"/>
  </a>
  &nbsp;&nbsp;
  <a href="#-installation">
    <img src="https://img.shields.io/badge/%E2%86%93_Download_for_Linux-2A2A3E?style=for-the-badge&logo=linux&logoColor=white" height="46" alt="Download Linux"/>
  </a>
  &nbsp;&nbsp;
  <a href="https://github.com/shubh-ssj/pixarchive/releases">
    <img src="https://img.shields.io/badge/Run_from_Source-2A2A3E?style=for-the-badge&logo=github&logoColor=white" height="46" alt="Run from Source"/>
  </a>
</div>

---

## What is PixArchive?

**PixArchive** is a fast, modern desktop application for downloading and archiving image galleries from 200+ websites. It wraps the powerful [`gallery-dl`](https://github.com/mikf/gallery-dl) engine in a clean, intuitive UI designed for collectors and power users.

**Speed. Beauty. Reliability.**

---

## Features

<div style="background: #2A2A3E; padding: 28px; border-radius: 16px; margin: 24px 0;">

<table>
<tr>
<td width="50%" valign="top">

### ⬇️ Download Panel
- Smart URL detection with rich previews
- Clipboard watcher + Drag & Drop
- Batch import from `.txt` / `.csv`
- 22 powerful presets
- Per-job folder overrides

</td>
<td width="50%" valign="top">

### 📋 Queue & History
- Live progress with ETAs and speed tracking
- Rich right-click context menu
- SQLite-backed history with search & export
- Detailed per-job logs

</td>
</tr>
<tr>
<td width="50%" valign="top">

### 🕐 Scheduler
- Once, hourly, daily, weekly, or custom intervals
- Smart handling for missed jobs

</td>
<td width="50%" valign="top">

### 🌐 Sites Panel
- 200+ supported sites in a beautiful card grid
- Authentication requirement badges
- One-click URL prefill

</td>
</tr>
</table>

</div>

### ✨ Highlights
- 7 stunning themes (Catppuccin, Tokyo Night, Nord, Synthwave, etc.)
- Per-site configuration overrides
- Config bundle export/import (`Ctrl+Shift+E`)
- System tray with rich notifications
- Automatic gallery-dl management
- First-run wizard

---

## ⬇️ Installation

### Windows (Recommended)
Download `pixarchive-setup.exe` (installer) or `pixarchive-portable.zip` from the **[Releases page](https://github.com/shubh-ssj/pixarchive/releases)**.

### Linux
Download the `.AppImage` or `.tar.gz` from Releases.

### From Source
```bash
git clone https://github.com/shubh-ssj/pixarchive.git
cd pixarchive
pip install -r requirements.txt
python main.py
