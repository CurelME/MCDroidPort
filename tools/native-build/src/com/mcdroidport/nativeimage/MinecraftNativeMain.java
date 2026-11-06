package com.mcdroidport.nativeimage;

import org.graalvm.nativeimage.IsolateThread;
import org.graalvm.nativeimage.c.function.CEntryPoint;
import org.graalvm.nativeimage.c.type.CCharPointer;
import org.graalvm.nativeimage.c.type.CCharPointerPointer;
import org.graalvm.nativeimage.c.type.CTypeConversion;

/**
 * MinecraftNativeMain
 *
 * SubstrateVM entrypoint wrapper for Ahead-of-Time compiled Minecraft Java Edition.
 * Exposes both:
 * 1. Standard Java main(String[]) entrypoint for GraalVM image builder analysis.
 * 2. C ABI symbol `minecraft_main` callable directly from NativeMinecraftLoader via dlopen/dlsym.
 */
public class MinecraftNativeMain {

    public static void main(String[] args) {
        try {
            net.minecraft.client.main.Main.main(args);
        } catch (Throwable t) {
            System.err.println("[MCDroidPort/Native] Fatal error in Minecraft execution: " + t.getMessage());
            t.printStackTrace(System.err);
        }
    }

    @CEntryPoint(name = "minecraft_main")
    public static int nativeEntryPoint(IsolateThread thread, int argc, CCharPointerPointer argv) {
        try {
            int argCount = Math.max(0, argc - 1);
            String[] javaArgs = new String[argCount];
            if (argv.isNonNull()) {
                for (int i = 1; i < argc; i++) {
                    CCharPointer argPtr = argv.read(i);
                    if (argPtr.isNonNull()) {
                        javaArgs[i - 1] = CTypeConversion.toJavaString(argPtr);
                    } else {
                        javaArgs[i - 1] = "";
                    }
                }
            }

            main(javaArgs);
            return 0;
        } catch (Throwable t) {
            System.err.println("[MCDroidPort/Native] Fatal error in native Minecraft execution: " + t.getMessage());
            t.printStackTrace(System.err);
            return 1;
        }
    }
}
