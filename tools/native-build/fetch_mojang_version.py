#!/usr/bin/env python3
"""
fetch_mojang_version.py

Automated fetcher for vanilla Minecraft Java Edition bytecode and libraries.
Queries Mojang's official Piston Meta version manifest to download the exact
client.jar and runtime dependencies for any requested Minecraft release.
"""

import os
import sys
import json
import urllib.request
from pathlib import Path

VERSION_MANIFEST_URL = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"

def fetch_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "MCDroidPort-Compiler/1.0"})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def download_file(url: str, dest_path: Path):
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    if dest_path.exists():
        return
    req = urllib.request.Request(url, headers={"User-Agent": "MCDroidPort-Compiler/1.0"})
    with urllib.request.urlopen(req) as resp, open(dest_path, "wb") as f:
        f.write(resp.read())

def fetch_minecraft(version_id: str, output_dir: Path):
    print(f"Querying Mojang version manifest for: {version_id}...")
    manifest = fetch_json(VERSION_MANIFEST_URL)

    target_entry = None
    if version_id.lower() in ("latest", "release"):
        version_id = manifest.get("latest", {}).get("release", "1.21.2")

    for v in manifest.get("versions", []):
        if v.get("id") == version_id:
            target_entry = v
            break

    if not target_entry:
        print(f"Error: Minecraft version '{version_id}' not found in Mojang manifest.")
        sys.exit(1)

    print(f"Fetching version details for {version_id} from {target_entry['url']}...")
    v_data = fetch_json(target_entry["url"])

    # 1. Download client.jar (minecraft.jar)
    client_dl = v_data.get("downloads", {}).get("client", {})
    client_url = client_dl.get("url")
    if not client_url:
        print("Error: No client download URL in version metadata.")
        sys.exit(1)

    client_jar_path = output_dir / "minecraft.jar"
    print(f"Downloading client.jar -> {client_jar_path}...")
    download_file(client_url, client_jar_path)

    # 2. Download libraries
    libs_dir = output_dir / "libraries"
    libraries = v_data.get("libraries", [])
    print(f"Downloading {len(libraries)} dependency libraries...")

    downloaded = 0
    for lib in libraries:
        artifact = lib.get("downloads", {}).get("artifact")
        if not artifact:
            continue
        lib_url = artifact.get("url")
        lib_path = artifact.get("path")
        if lib_url and lib_path:
            # Skip desktop Linux natives
            if "natives-linux" in lib_path or "natives-windows" in lib_path or "natives-macos" in lib_path:
                continue
            dest = libs_dir / lib_path
            download_file(lib_url, dest)
            downloaded += 1

    print(f"Successfully downloaded {downloaded} libraries and client.jar for Minecraft {version_id}.")

if __name__ == "__main__":
    ver = sys.argv[1] if len(sys.argv) > 1 else "1.21.2"
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("build_input")
    fetch_minecraft(ver, out)
