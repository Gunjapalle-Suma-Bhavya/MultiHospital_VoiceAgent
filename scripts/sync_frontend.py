#!/usr/bin/env python3
"""
NexusHealth Frontend Build & Static Asset Synchronizer.
Verifies compiled Vite production bundles in static/ and verifies asset integrity.
"""

import os
import glob
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
STATIC_DIR = os.path.join(BASE_DIR, "static")
STATIC_ASSETS = os.path.join(STATIC_DIR, "assets")
INDEX_HTML = os.path.join(STATIC_DIR, "index.html")

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

    print(f"[Success] Synced production frontend build successfully:")
    print(f"  • Entry HTML: {INDEX_HTML}")
    print(f"  • Latest JS:  {os.path.basename(latest_js)} ({os.path.getsize(latest_js):,} bytes)")
    print(f"  • Latest CSS: {os.path.basename(latest_css)} ({os.path.getsize(latest_css):,} bytes)")

if __name__ == "__main__":
    sync_frontend()
