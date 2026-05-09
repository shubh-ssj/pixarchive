@echo off
REM ─────────────────────────────────────────────────────────────────────────────
REM  PixArchive — Windows build script
REM  Run this from the project root directory.
REM
REM  Requirements:
REM    pip install pyinstaller gallery-dl PyQt6
REM
REM  Output:
REM    dist\pixarchive\          ← portable folder (zip and ship)
REM    installer\pixarchive-setup.exe  ← Inno Setup installer (if ISCC found)
REM ─────────────────────────────────────────────────────────────────────────────

setlocal enabledelayedexpansion

echo.
echo  PixArchive — Build Script
echo  ══════════════════════════════
echo.

REM ── Check Python ─────────────────────────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Install Python 3.11+ and add it to PATH.
    exit /b 1
)
echo [OK] Python found

REM ── Check / install PyInstaller ──────────────────────────────────────────────
pyinstaller --version >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing PyInstaller...
    pip install pyinstaller
    if errorlevel 1 (
        echo [ERROR] Failed to install PyInstaller.
        exit /b 1
    )
)
echo [OK] PyInstaller found

REM ── Download gallery-dl binary ───────────────────────────────────────────────
echo [INFO] Downloading gallery-dl standalone binary...
python download_gallery_dl.py
if errorlevel 1 (
    echo [ERROR] Failed to download gallery-dl binary.
    echo         Check your internet connection and try again.
    exit /b 1
)

REM ── Clean previous build ─────────────────────────────────────────────────────
echo [INFO] Cleaning previous build...
if exist build  rmdir /s /q build
if exist dist   rmdir /s /q dist

REM ── Run PyInstaller ──────────────────────────────────────────────────────────
echo [INFO] Building executable...
pyinstaller pixarchive.spec --noconfirm

if errorlevel 1 (
    echo [ERROR] PyInstaller build failed.
    exit /b 1
)
echo [OK] Build complete — dist\pixarchive\

REM ── Create portable ZIP ──────────────────────────────────────────────────────
echo [INFO] Creating portable ZIP...
if exist dist\pixarchive (
    powershell -Command "Compress-Archive -Path 'dist\pixarchive\*' -DestinationPath 'dist\pixarchive-portable.zip' -Force"
    echo [OK] Portable ZIP: dist\pixarchive-portable.zip
)

REM ── Build Inno Setup installer (optional) ────────────────────────────────────
set ISCC="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not exist %ISCC% set ISCC="C:\Program Files\Inno Setup 6\ISCC.exe"

if exist %ISCC% (
    echo [INFO] Building installer with Inno Setup...
    if not exist installer mkdir installer
    %ISCC% installer\pixarchive.iss
    if errorlevel 1 (
        echo [WARN] Inno Setup build failed — portable ZIP is still available.
    ) else (
        echo [OK] Installer: installer\pixarchive-setup.exe
    )
) else (
    echo [INFO] Inno Setup not found — skipping installer build.
    echo        Download from: https://jrsoftware.org/isdl.php
)

echo.
echo  Build complete!
echo  ──────────────────────────────────────────────────────
echo   Portable:  dist\pixarchive-portable.zip
if exist installer\pixarchive-setup.exe (
    echo   Installer: installer\pixarchive-setup.exe
)
echo.
endlocal
