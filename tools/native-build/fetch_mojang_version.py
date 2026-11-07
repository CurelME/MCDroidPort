#!/usr/bin/env python3
"""
fetch_mojang_version.py

Automated fetcher for vanilla Minecraft Java Edition bytecode and libraries.
Queries Mojang's official Piston Meta version manifest to download the exact
client.jar and runtime dependencies for any requested Minecraft release.
Includes rule-based OS filtering and concurrent multi-threaded downloads.
"""

import os
import sys
import json
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

VERSION_MANIFEST_URL = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"

def fetch_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "MCDroidPort-Compiler/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))

def download_file_with_retry(url: str, dest_path: Path, expected_size: int = -1, max_retries: int = 3):
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    if dest_path.exists() and (expected_size <= 0 or dest_path.stat().st_size == expected_size):
        return True

    for attempt in range(1, max_retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "MCDroidPort-Compiler/1.0"})
            with urllib.request.urlopen(req, timeout=25) as resp:
                data = resp.read()
                if expected_size > 0 and len(data) != expected_size:
                    raise IOError(f"Size mismatch: expected {expected_size}, got {len(data)}")
                with open(dest_path, "wb") as f:
                    f.write(data)
            return True
        except Exception as e:
            if attempt == max_retries:
                print(f"Failed to download {dest_path.name} from {url}: {e}")
                return False
            time.sleep(1)
    return False

def is_library_allowed(rules: list) -> bool:
    if not rules:
        return True
    allowed = False
    for r in rules:
        action = r.get("action") == "allow"
        os_info = r.get("os", {})
        os_name = os_info.get("name")
        if os_name is None or os_name == "linux":
            allowed = action
    return allowed

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
    java_ver = v_data.get("javaVersion", {}).get("majorVersion", 25 if str(version_id).startswith("26") else 21)
    print(f"Detected target Java runtime major version: {java_ver}")

    gh_output = os.environ.get("GITHUB_OUTPUT")
    if gh_output:
        try:
            with open(gh_output, "a", encoding="utf-8") as f:
                f.write(f"java_version={java_ver}\n")
        except Exception as e:
            print(f"Failed to write GITHUB_OUTPUT: {e}")

    gh_env = os.environ.get("GITHUB_ENV")
    if gh_env:
        try:
            with open(gh_env, "a", encoding="utf-8") as f:
                f.write(f"JAVA_VERSION={java_ver}\n")
        except Exception as e:
            print(f"Failed to write GITHUB_ENV: {e}")

    # 1. Download client.jar (minecraft.jar)
    client_dl = v_data.get("downloads", {}).get("client", {})
    client_url = client_dl.get("url")
    client_size = client_dl.get("size", -1)
    if not client_url:
        print("Error: No client download URL in version metadata.")
        sys.exit(1)

    client_jar_path = output_dir / "minecraft.jar"
    print(f"Downloading client.jar -> {client_jar_path} ({client_size} bytes)...")
    if not download_file_with_retry(client_url, client_jar_path, client_size):
        print("Failed to download client.jar!")
        sys.exit(1)

    # 2. Download libraries
    libs_dir = output_dir / "libraries"
    libraries = v_data.get("libraries", [])
    print(f"Parsing {len(libraries)} candidate dependency libraries from Mojang metadata...")

    tasks = []
    for lib in libraries:
        # Check rule blocks (filter out non-Linux/OS-incompatible dependencies)
        if not is_library_allowed(lib.get("rules", [])):
            continue

        artifact = lib.get("downloads", {}).get("artifact")
        if not artifact:
            continue
        lib_url = artifact.get("url")
        lib_path = artifact.get("path")
        lib_size = artifact.get("size", -1)

        if lib_url and lib_path:
            # Skip desktop natives (native AOT provides mobile implementations)
            if "natives-linux" in lib_path or "natives-windows" in lib_path or "natives-macos" in lib_path:
                continue
            dest = libs_dir / lib_path
            tasks.append((lib_url, dest, lib_size))

    print(f"Downloading {len(tasks)} verified Java dependency libraries concurrently...")
    downloaded = 0
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(download_file_with_retry, url, dest, size): dest for url, dest, size in tasks}
        for future in as_completed(futures):
            dest = futures[future]
            if future.result():
                downloaded += 1

    print(f"Successfully downloaded {downloaded}/{len(tasks)} libraries and client.jar for Minecraft {version_id}.")

if __name__ == "__main__":
    ver = sys.argv[1] if len(sys.argv) > 1 else "1.21.2"
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("build_input")
    fetch_minecraft(ver, out)
