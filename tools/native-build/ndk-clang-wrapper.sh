#!/usr/bin/env bash

if [ -n "$ANDROID_NDK_HOME" ] && [ -x "$ANDROID_NDK_HOME/toolchains/llvm/prebuilt/linux-x86_64/bin/aarch64-linux-android30-clang" ]; then
  REAL_CLANG="$ANDROID_NDK_HOME/toolchains/llvm/prebuilt/linux-x86_64/bin/aarch64-linux-android30-clang"
elif [ -n "$ANDROID_NDK_ROOT" ] && [ -x "$ANDROID_NDK_ROOT/toolchains/llvm/prebuilt/linux-x86_64/bin/aarch64-linux-android30-clang" ]; then
  REAL_CLANG="$ANDROID_NDK_ROOT/toolchains/llvm/prebuilt/linux-x86_64/bin/aarch64-linux-android30-clang"
elif [ -n "$NDK_BIN" ] && [ -x "$NDK_BIN/aarch64-linux-android30-clang" ]; then
  REAL_CLANG="$NDK_BIN/aarch64-linux-android30-clang"
else
  REAL_CLANG="$(which aarch64-linux-android30-clang 2>/dev/null)"
fi

if [ -z "$REAL_CLANG" ] || [ ! -x "$REAL_CLANG" ]; then
  echo "Error: aarch64-linux-android30-clang not found in PATH or ANDROID_NDK_HOME ($ANDROID_NDK_HOME)!" >&2
  exit 1
fi

args=()
has_shared=false
is_libminecraft=false
for arg in "$@"; do
  if [ "$arg" = "-fuse-ld=gold" ]; then
    args+=("-fuse-ld=lld")
  elif [ "$arg" = "-shared" ]; then
    has_shared=true
    args+=("$arg")
  else
    args+=("$arg")
  fi
  case "$arg" in
    *libminecraft*)
      is_libminecraft=true
      ;;
  esac
done

# If linking libminecraft shared library, append the JDK 21 Bionic bridge object
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BRIDGE_OBJ="$REPO_ROOT/build_native/jdk21_bionic_bridge.o"
if [ "$has_shared" = true ] && [ "$is_libminecraft" = true ] && [ -f "$BRIDGE_OBJ" ]; then
  args+=("$BRIDGE_OBJ")
fi

out=$("$REAL_CLANG" "${args[@]}" 2>&1)
status=$?

if [ $status -ne 0 ]; then
  echo "[ndk-clang-wrapper] COMMAND FAILED with exit code $status!" >&2
  echo "[ndk-clang-wrapper] Compiler output:" >&2
  echo "$out" >&2
  exit $status
fi

if [ -n "$out" ]; then
  echo "$out"
fi

exit 0
