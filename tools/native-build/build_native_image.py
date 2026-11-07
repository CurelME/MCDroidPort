#!/usr/bin/env python3
"""
build_native_image.py

MCDroidPort GraalVM Native Image AOT Build Orchestrator
-------------------------------------------------------
Automates compiling Minecraft Java Edition (minecraft.jar + dependencies)
into a standalone ARM64 Linux/Android shared library (libminecraft.so)
powered by SubstrateVM.

Eliminates:
  - OpenJDK HotSpot runtime (libjvm.so)
  - 150MB APK asset overhead
  - All JIT compiler threads (C1 and C2)
  - Bytecode interpretation pauses

Usage:
  python build_native_image.py --check-tools
  python build_native_image.py --generate-config
  python build_native_image.py --build
  python build_native_image.py --clean-jvm
"""

import os
import sys
import argparse
import subprocess
import shutil
import glob
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
APP_DIR = REPO_ROOT / "app"
ASSETS_DIR = APP_DIR / "src" / "main" / "assets"
JNILIBS_DIR = APP_DIR / "src" / "main" / "jniLibs" / "arm64-v8a"
CONFIG_DIR = REPO_ROOT / "tools" / "native-build" / "config"
SRC_DIR = REPO_ROOT / "tools" / "native-build" / "src"

def find_ndk_clang() -> tuple[Path, Path]:
    """Locate Android NDK LLVM cross compiler for aarch64."""
    candidates = []
    if "ANDROID_NDK_HOME" in os.environ:
        candidates.append(Path(os.environ["ANDROID_NDK_HOME"]))
    if "ANDROID_NDK_ROOT" in os.environ:
        candidates.append(Path(os.environ["ANDROID_NDK_ROOT"]))

    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        ndk_root = Path(local_app_data) / "Android" / "Sdk" / "ndk"
        if ndk_root.exists():
            candidates.extend(sorted(ndk_root.iterdir(), reverse=True))

    for ndk in candidates:
        if not ndk.is_dir():
            continue
        bin_dir = ndk / "toolchains" / "llvm" / "prebuilt" / "windows-x86_64" / "bin"
        if not bin_dir.exists():
            continue
        clang_cmd = bin_dir / "aarch64-linux-android30-clang.cmd"
        clang_exe = bin_dir / "aarch64-linux-android30-clang.exe"
        if clang_cmd.exists():
            return ndk, clang_cmd
        if clang_exe.exists():
            return ndk, clang_exe

    return Path(), Path()

def find_native_image() -> Path | None:
    """Locate GraalVM native-image tool."""
    if "GRAALVM_HOME" in os.environ:
        p = Path(os.environ["GRAALVM_HOME"]) / "bin" / ("native-image.cmd" if sys.platform == "win32" else "native-image")
        if p.exists():
            return p

    if "JAVA_HOME" in os.environ:
        p = Path(os.environ["JAVA_HOME"]) / "bin" / ("native-image.cmd" if sys.platform == "win32" else "native-image")
        if p.exists():
            return p

    which = shutil.which("native-image")
    if which:
        return Path(which)

    return None

def check_tools(args):
    print("==================================================")
    print("MCDroidPort Native Image Toolchain Verification")
    print("==================================================")

    ndk_dir, clang = find_ndk_clang()
    if clang and clang.exists():
        print(f"[OK] Android NDK detected : {ndk_dir}")
        print(f"     Clang cross compiler: {clang}")
    else:
        print("[FAIL] Android NDK aarch64 cross compiler not found.")

    ni = find_native_image()
    if ni and ni.exists():
        print(f"[OK] GraalVM native-image : {ni}")
    else:
        print("[WARN] GraalVM native-image executable not detected on PATH or GRAALVM_HOME.")
        print("       Install Oracle GraalVM for JDK 21/24/25 or set GRAALVM_HOME.")

    mc_jar = ASSETS_DIR / "minecraft.jar"
    if mc_jar.exists():
        print(f"[OK] Game bytecode        : {mc_jar} ({mc_jar.stat().st_size / (1024*1024):.1f} MB)")
    else:
        print(f"[FAIL] minecraft.jar missing at {mc_jar}")

    print("==================================================")

def generate_config(args):
    """Run tracing agent on desktop to collect reachability metadata."""
    print("Executing Native Image Tracing Agent against minecraft.jar...")
    mc_jar = ASSETS_DIR / "minecraft.jar"
    if not mc_jar.exists():
        print(f"Error: {mc_jar} not found")
        sys.exit(1)

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    agent_flag = f"-agentlib:native-image-agent=config-merge-dir={CONFIG_DIR}"
    
    cmd = [
        "java",
        agent_flag,
        "-cp", str(mc_jar),
        "net.minecraft.client.main.Main",
        "--help"
    ]
    print("Running:", " ".join(cmd))
    subprocess.run(cmd, check=False)
    print(f"Metadata generated and merged into {CONFIG_DIR}")

def build_native_library(args):
    """Compile libminecraft.so via GraalVM native-image."""
    ni = find_native_image()
    if not ni.exists():
        print("Error: GraalVM native-image compiler not found. Please install GraalVM or set GRAALVM_HOME.")
        sys.exit(1)

    ndk_dir, clang = find_ndk_clang()
    if not clang.exists():
        print("Error: Android NDK aarch64 Clang cross compiler not found.")
        sys.exit(1)

    mc_jar = ASSETS_DIR / "minecraft.jar"
    libs_dir = ASSETS_DIR / "libraries"
    
    all_jars = [str(mc_jar)]
    if libs_dir.exists():
        for root, _, files in os.walk(libs_dir):
            for f in files:
                if f.endswith(".jar") and "natives-linux" not in f:
                    all_jars.append(os.path.join(root, f))

    classpath = os.pathsep.join(all_jars)
    JNILIBS_DIR.mkdir(parents=True, exist_ok=True)
    output_so = JNILIBS_DIR / "libminecraft.so"

    cmd = [
        str(ni),
        "--shared",
        "-H:+UnlockExperimentalVMOptions",
        "-Dsvm.platform=org.graalvm.nativeimage.Platform$ANDROID_AARCH64",
        "--libc=bionic",
        "-H:+UseCAPCache",
        f"-H:CAPCacheDir={CONFIG_DIR / 'cap'}",
        "-H:Name=libminecraft",
        "--gc=serial",
        "-O3",
        "--no-fallback",
        f"-H:CCompilerPath={clang}",
        f"-H:ConfigurationFileDirectories={CONFIG_DIR}",
        f"-H:NativeLinkerOption=-L{JNILIBS_DIR}",
        "-H:NativeLinkerOption=-lsubstrate_shim",
        "-H:NativeLinkerOption=-lmcdroid",
        "-H:NativeLinkerOption=-Wl,-rpath,$ORIGIN",
        "-cp", classpath,
        "com.mcdroidport.nativeimage.MinecraftNativeMain",
        "-o", str(JNILIBS_DIR / "libminecraft")
    ]

    print("==================================================")
    print(f"Building {output_so} via GraalVM Native Image...")
    print("==================================================")
    print("Command:", " ".join(cmd))
    
    res = subprocess.run(cmd)
    if res.returncode == 0:
        print(f"\n[SUCCESS] libminecraft.so compiled successfully -> {output_so}")
    else:
        print(f"\n[FAILED] native-image exited with code {res.returncode}")
        sys.exit(res.returncode)

def clean_jvm(args):
    """Permanently delete the 150MB OpenJDK tree from assets to minimize APK size."""
    jvm_assets = ASSETS_DIR / "jvm"
    if jvm_assets.exists():
        print(f"Removing {jvm_assets}...")
        shutil.rmtree(jvm_assets)
        print("Removed assets/jvm (150MB space saved).")
    else:
        print("assets/jvm already clean.")

def main():
    parser = argparse.ArgumentParser(description="MCDroidPort GraalVM Native Image AOT Build Orchestrator")
    parser.add_argument("--check-tools", action="store_true", help="Verify toolchains")
    parser.add_argument("--generate-config", action="store_true", help="Run tracing agent")
    parser.add_argument("--build", action="store_true", help="Compile libminecraft.so")
    parser.add_argument("--clean-jvm", action="store_true", help="Remove assets/jvm")

    args = parser.parse_args()
    if args.check_tools:
        check_tools(args)
    elif args.generate_config:
        generate_config(args)
    elif args.build:
        build_native_library(args)
    elif args.clean_jvm:
        clean_jvm(args)
    else:
        check_tools(args)

if __name__ == "__main__":
    main()
