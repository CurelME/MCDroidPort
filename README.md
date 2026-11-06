# MCDroidPort

Compiler for Minecraft Java Edition, compiling game bytecode into native Android ARM64 shared libraries (`libminecraft.so`).

## Usage

Trigger the build workflow under the Actions tab by specifying any target Minecraft version (such as `1.21.2`). The workflow compiles the native engine, compresses the binary into `libminecraft.so.gz`, and publishes the release payload automatically to the `engine-binaries` branch.

## Local Compilation

### Requirements
- Python 3.10+
- Oracle GraalVM for JDK 21+ with `native-image` installed
- Android NDK r27c (`ANDROID_NDK_HOME`)

### Steps

1. Fetch game files for target Minecraft version:
```bash
python tools/native-build/fetch_mojang_version.py 1.21.2 build_input
```

2. Compile native engine:
```bash
python tools/native-build/build_native_image.py --build
```
