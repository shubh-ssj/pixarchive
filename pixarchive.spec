# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for PixArchive
# Build with:  pyinstaller pixarchive.spec

import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect all PyQt6 plugins needed for the app to run on a bare machine
qt_plugins = collect_data_files('PyQt6', includes=['Qt/plugins/platforms/*',
                                                    'Qt/plugins/styles/*',
                                                    'Qt/plugins/imageformats/*'])

# ── Detect bundled gallery-dl binary ─────────────────────────────────────────
import os, sys

# When building, look for a pre-downloaded gallery-dl binary in ./bin/
# Windows: bin/gallery-dl.exe
# Linux:   bin/gallery-dl
# macOS:   bin/gallery-dl
_bin_dir = os.path.join(os.path.dirname(os.path.abspath(SPEC)), 'bin')
_gdl_win  = os.path.join(_bin_dir, 'gallery-dl.exe')
_gdl_unix = os.path.join(_bin_dir, 'gallery-dl')

_bundled_binaries = []
if sys.platform == 'win32' and os.path.exists(_gdl_win):
    _bundled_binaries.append((_gdl_win, 'bin'))
    print(f'[spec] Bundling gallery-dl binary: {_gdl_win}')
elif os.path.exists(_gdl_unix):
    _bundled_binaries.append((_gdl_unix, 'bin'))
    print(f'[spec] Bundling gallery-dl binary: {_gdl_unix}')
else:
    print('[spec] WARNING: No gallery-dl binary found in ./bin/ — '
          'run download_gallery_dl.py first, or users will need it installed.')

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=_bundled_binaries,
    datas=[
        ('README.md',        '.'),
        ('requirements.txt', '.'),
        ('assets',           'assets'),
    ] + qt_plugins,
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'PyQt6.QtMultimedia',
        'PyQt6.sip',
        'sqlite3',
        'json',
        'csv',
        'urllib.request',
        'webbrowser',
        'subprocess',
        're',
        'dataclasses',
        'shutil',
        'os',
        'sys',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Things we definitely don't use — shrinks the bundle
        'tkinter', 'matplotlib', 'numpy', 'scipy', 'PIL',
        'IPython', 'jupyter', 'notebook', 'pandas',
        'PyQt5', 'PySide2', 'PySide6',
        'wx', 'gi',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='pixarchive',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,                   # compress with UPX if available
    console=False,              # no console window (windowed app)
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='pixarchive',      # output folder name inside dist/
)
