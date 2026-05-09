#!/usr/bin/env python3
"""
Downloads the latest standalone gallery-dl binary for the current platform
into ./bin/ so that build.bat / build.sh can bundle it into the executable.

Run this ONCE before building:
    python download_gallery_dl.py

The binary is fetched from the official GitHub releases page:
    https://github.com/mikf/gallery-dl/releases/latest
"""
import json
import os
import stat
import sys
import urllib.request

API_URL  = "https://api.github.com/repos/mikf/gallery-dl/releases/latest"
BIN_DIR  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bin")

# Asset name → platform match
ASSET_MAP = {
    "win32":  "gallery-dl.exe",
    "darwin": "gallery-dl",          # macOS universal binary
    "linux":  "gallery-dl",
}


def _progress(count, block_size, total):
    if total <= 0:
        print(f"\r  {count * block_size // 1024} KB downloaded...", end="", flush=True)
    else:
        pct = min(100, count * block_size * 100 // total)
        bar = "█" * (pct // 5) + "░" * (20 - pct // 5)
        mb_done  = count * block_size / 1_048_576
        mb_total = total / 1_048_576
        print(f"\r  [{bar}] {pct:3d}%  {mb_done:.1f}/{mb_total:.1f} MB", end="", flush=True)


def main():
    platform = sys.platform

    if platform not in ASSET_MAP:
        print(f"[ERROR] Unsupported platform: {platform}")
        sys.exit(1)

    asset_name = ASSET_MAP[platform]
    out_name   = "gallery-dl.exe" if platform == "win32" else "gallery-dl"
    out_path   = os.path.join(BIN_DIR, out_name)

    print(f"gallery-dl binary downloader")
    print(f"Platform : {platform}")
    print(f"Asset    : {asset_name}")
    print(f"Output   : {out_path}")
    print()

    # ── Fetch latest release info ─────────────────────────────────────────────
    print("Fetching latest release info from GitHub...")
    req = urllib.request.Request(
        API_URL,
        headers={
            "Accept":     "application/vnd.github+json",
            "User-Agent": "pixarchive-builder/0.1",
        }
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        release = json.loads(resp.read())

    tag     = release.get("tag_name", "unknown")
    assets  = release.get("assets", [])

    print(f"Latest release: {tag}")

    # ── Find the right asset ──────────────────────────────────────────────────
    download_url = None
    for asset in assets:
        name = asset.get("name", "")
        # Match exactly — gallery-dl.exe or gallery-dl (no extension)
        if name == asset_name:
            download_url = asset["browser_download_url"]
            size_mb = asset.get("size", 0) / 1_048_576
            print(f"Found asset : {name}  ({size_mb:.1f} MB)")
            break

    if not download_url:
        # Fallback: try the generic binary name
        for asset in assets:
            if asset_name in asset.get("name", ""):
                download_url = asset["browser_download_url"]
                print(f"Found asset (fallback): {asset['name']}")
                break

    if not download_url:
        print(f"\n[ERROR] Could not find '{asset_name}' in release {tag}.")
        print("Available assets:")
        for a in assets:
            print(f"  - {a['name']}")
        sys.exit(1)

    # ── Download ──────────────────────────────────────────────────────────────
    os.makedirs(BIN_DIR, exist_ok=True)
    print(f"\nDownloading...")
    urllib.request.urlretrieve(download_url, out_path, reporthook=_progress)
    print()  # newline after progress bar

    # ── Make executable (Unix) ────────────────────────────────────────────────
    if platform != "win32":
        os.chmod(out_path, os.stat(out_path).st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
        print(f"Made executable: chmod +x {out_path}")

    # ── Verify ────────────────────────────────────────────────────────────────
    import subprocess
    try:
        r = subprocess.run([out_path, "--version"], capture_output=True, text=True, timeout=5)
        version = (r.stdout or r.stderr).strip()
        print(f"Verified: {version}")
    except Exception as e:
        print(f"[WARN] Could not verify binary: {e}")

    print()
    print(f"Done! Binary saved to: {out_path}")
    print("You can now run build.bat (Windows) or build.sh (Linux/macOS).")


if __name__ == "__main__":
    main()
