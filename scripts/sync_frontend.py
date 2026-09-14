#!/usr/bin/env python3
"""
NexusHealth Frontend Build & Static Asset Synchronizer.
Verifies compiled Vite production bundles in static/ and syncs to public/ for Vercel edge deployment.
"""

import os
import glob
import shutil
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
STATIC_DIR = os.path.join(BASE_DIR, "static")
STATIC_ASSETS = os.path.join(STATIC_DIR, "assets")
INDEX_HTML = os.path.join(STATIC_DIR, "index.html")

PUBLIC_DIR = os.path.join(BASE_DIR, "public")
PUBLIC_STATIC = os.path.join(PUBLIC_DIR, "static")
PUBLIC_ASSETS = os.path.join(PUBLIC_DIR, "assets")

def sync_frontend():
    print("[Sync] Checking compiled frontend static assets...")
    if not os.path.exists(INDEX_HTML):
        print(f"[Error] {INDEX_HTML} not found!", file=sys.stderr)
        sys.exit(1)

    js_files = glob.glob(os.path.join(STATIC_ASSETS, "index-*.js"))
    css_files = glob.glob(os.path.join(STATIC_ASSETS, "index-*.css"))

    if not js_files or not css_files:
        print(f"[Warning] No compiled asset files found in {STATIC_ASSETS}!", file=sys.stderr)
        sys.exit(1)

    latest_js = max(js_files, key=os.path.getmtime)
    latest_css = max(css_files, key=os.path.getmtime)

    # Sync to public/ directory for Vercel edge CDN
    os.makedirs(PUBLIC_STATIC, exist_ok=True)
    os.makedirs(PUBLIC_ASSETS, exist_ok=True)
    
    shutil.copy2(INDEX_HTML, os.path.join(PUBLIC_DIR, "index.html"))
    shutil.copytree(STATIC_ASSETS, os.path.join(PUBLIC_STATIC, "assets"), dirs_exist_ok=True)
    shutil.copytree(STATIC_ASSETS, PUBLIC_ASSETS, dirs_exist_ok=True)

    print(f"[Success] Synced production frontend build to static/ and public/:")
    print(f"  • Entry HTML: {INDEX_HTML}")
    print(f"  • Latest JS:  {os.path.basename(latest_js)} ({os.path.getsize(latest_js):,} bytes)")
    print(f"  • Latest CSS: {os.path.basename(latest_css)} ({os.path.getsize(latest_css):,} bytes)")

if __name__ == "__main__":
    sync_frontend()
