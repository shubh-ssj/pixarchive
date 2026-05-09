# Building PixArchive

This document explains how to produce a standalone executable and installer
that users can run without installing Python.

## Quick start

```bash
# Install build dependencies (gallery-dl NOT needed — it gets bundled automatically)
pip install pyinstaller PyQt6

# Windows
build.bat

# Linux / macOS
bash build.sh
```

The build scripts automatically:
1. Download the latest standalone gallery-dl binary for your platform (via `download_gallery_dl.py`)
2. Bundle it inside the executable — users get a **fully self-contained app with zero dependencies**

> If you want to download the gallery-dl binary separately first:
> ```bash
> python download_gallery_dl.py
> ```

---

## Windows

### Prerequisites

| Tool | Where to get it |
|------|----------------|
| Python 3.11+ | https://python.org/downloads — tick "Add to PATH" |
| PyInstaller | `pip install pyinstaller` |
| Inno Setup 6 *(optional, for .exe installer)* | https://jrsoftware.org/isdl.php |
| UPX *(optional, smaller binary)* | https://github.com/upx/upx/releases — put `upx.exe` on PATH |

### Steps

```bat
pip install pyinstaller PyQt6 gallery-dl
build.bat
```

**Outputs:**

| File | Description |
|------|-------------|
| `dist\pixarchive\` | Portable folder — zip and distribute |
| `dist\pixarchive-portable.zip` | Portable ZIP (created automatically) |
| `installer\pixarchive-setup.exe` | Windows installer (requires Inno Setup) |

### What the installer does

- Installs to `%ProgramFiles%\PixArchive` (or per-user if no admin rights)
- Creates Start Menu shortcut
- Optional: desktop shortcut, startup entry, add to PATH
- Includes a proper uninstaller
- Bundles gallery-dl as a standalone binary — **no Python, no pip, no dependencies required**
- Falls back to a system-installed gallery-dl if the bundled one is superseded

---

## Linux

### Prerequisites

```bash
pip install pyinstaller PyQt6 gallery-dl

# For AppImage (optional)
# Download appimagetool from https://github.com/AppImage/AppImageKit/releases
# and put it on your PATH
```

### Steps

```bash
bash build.sh
```

**Outputs:**

| File | Description |
|------|-------------|
| `dist/pixarchive/` | Portable folder |
| `dist/pixarchive.tar.gz` | Portable tarball |
| `dist/pixarchive.AppImage` | Self-contained AppImage (if appimagetool found) |

### Running the AppImage

```bash
chmod +x pixarchive.AppImage
./pixarchive.AppImage
```

---

## macOS

### Prerequisites

```bash
pip install pyinstaller PyQt6 gallery-dl
brew install create-dmg   # optional, for .dmg
```

### Steps

```bash
bash build.sh
```

**Outputs:**

| File | Description |
|------|-------------|
| `dist/pixarchive/` | Portable folder |
| `dist/pixarchive.tar.gz` | Portable tarball |
| `dist/pixarchive.dmg` | macOS disk image (if create-dmg found) |

> **Note on code signing:** For distribution outside your own machine on macOS,
> you will need to sign and notarize the app with an Apple Developer account.
> Without signing, Gatekeeper will block it for other users.
> For personal use, right-click → Open to bypass the warning.

---

## Customising the build

### Adding an app icon

1. Create `assets/icon.ico` (Windows, 256×256 recommended)
2. Create `assets/icon.icns` (macOS)
3. Create `assets/icon.png` (Linux AppImage, 512×512)
4. In `pixarchive.spec`, uncomment the `icon=` line and update the path

### Adding a notification sound

1. Place a `complete.wav` file in `assets/`
2. In `pixarchive.spec`, uncomment the `('assets', 'assets')` line in `datas`

### Reducing binary size

- Install UPX and ensure it's on PATH — PyInstaller will use it automatically
- The `excludes` list in the spec already strips unused libraries
- Expected sizes: ~60–90 MB portable folder, ~25–35 MB installer

### One-file mode

For a single `.exe` instead of a folder, change the spec:

```python
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,    # add this
    a.zipfiles,    # add this
    a.datas,       # add this
    ...
    onefile=True,  # add this
)
```

And remove the `COLLECT()` call. Note: one-file mode is slower to start because
it extracts to a temp folder on every launch.

---

## Troubleshooting

**`ModuleNotFoundError` at runtime**  
Add the missing module to `hiddenimports` in the `.spec` file and rebuild.

**App opens then immediately closes**  
Run from a terminal to see the error:
```bat
dist\pixarchive\pixarchive.exe
```

**PyQt6 plugins missing (blank window / no styles)**  
The spec already collects Qt plugins. If issues persist, add to `datas`:
```python
collect_data_files('PyQt6', includes=['Qt/plugins/**/*'])
```

**Windows Defender flags the exe**  
This is a false positive common with PyInstaller. Code-signing the exe with a
certificate resolves it for distribution. For personal use, add an exclusion in
Windows Security.
