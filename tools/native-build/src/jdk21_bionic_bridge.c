/**
 * jdk21_bionic_bridge.c
 *
 * Bridge forwarding layer resolving JDK 21 native I/O, networking, and filesystem
 * methods against Gluon Substrate static libraries and Bionic POSIX syscalls.
 * Guarantees zero undefined Java symbols when building standalone AOT libminecraft.so.
 */

#include <stdint.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <sys/uio.h>
#include <sys/mman.h>

#define EXPORT __attribute__((visibility("default")))

// Forward declarations of Gluon JDK 18 base symbols
extern int64_t Java_java_io_RandomAccessFile_length(void *env, void *this, int64_t fd);
extern int32_t Java_java_io_RandomAccessFile_readBytes(void *env, void *this, void *bytes, int32_t off, int32_t len);
extern void    Java_java_io_RandomAccessFile_writeBytes(void *env, void *this, void *bytes, int32_t off, int32_t len);
extern int32_t Java_java_io_UnixFileSystem_checkAccess(void *env, void *this, void *file, int32_t access);
extern int32_t Java_java_io_UnixFileSystem_createDirectory(void *env, void *this, void *file);
extern int32_t Java_java_io_UnixFileSystem_createFileExclusively(void *env, void *this, void *path);
extern int64_t Java_java_io_UnixFileSystem_getLastModifiedTime(void *env, void *this, void *file);
extern int64_t Java_java_io_UnixFileSystem_getLength(void *env, void *this, void *file);
extern void*   Java_java_io_UnixFileSystem_list(void *env, void *this, void *file);
extern int32_t Java_java_io_UnixFileSystem_setLastModifiedTime(void *env, void *this, void *file, int64_t time);
extern int32_t Java_java_io_UnixFileSystem_setPermission(void *env, void *this, void *file, int32_t access, int32_t enable, int32_t owneronly);

// JDK 21 RandomAccessFile & UnixFileSystem aliases
EXPORT int64_t Java_java_io_RandomAccessFile_length0(void *env, void *this, int64_t fd) {
    return Java_java_io_RandomAccessFile_length(env, this, fd);
}
EXPORT int32_t Java_java_io_RandomAccessFile_readBytes0(void *env, void *this, void *bytes, int32_t off, int32_t len) {
    return Java_java_io_RandomAccessFile_readBytes(env, this, bytes, off, len);
}
EXPORT void Java_java_io_RandomAccessFile_writeBytes0(void *env, void *this, void *bytes, int32_t off, int32_t len) {
    Java_java_io_RandomAccessFile_writeBytes(env, this, bytes, off, len);
}
EXPORT int32_t Java_java_io_UnixFileSystem_checkAccess0(void *env, void *this, void *file, int32_t access) {
    return Java_java_io_UnixFileSystem_checkAccess(env, this, file, access);
}
EXPORT int32_t Java_java_io_UnixFileSystem_createDirectory0(void *env, void *this, void *file) {
    return Java_java_io_UnixFileSystem_createDirectory(env, this, file);
}
EXPORT int32_t Java_java_io_UnixFileSystem_createFileExclusively0(void *env, void *this, void *path) {
    return Java_java_io_UnixFileSystem_createFileExclusively(env, this, path);
}
EXPORT int64_t Java_java_io_UnixFileSystem_getLastModifiedTime0(void *env, void *this, void *file) {
    return Java_java_io_UnixFileSystem_getLastModifiedTime(env, this, file);
}
EXPORT int64_t Java_java_io_UnixFileSystem_getLength0(void *env, void *this, void *file) {
    return Java_java_io_UnixFileSystem_getLength(env, this, file);
}
EXPORT void* Java_java_io_UnixFileSystem_list0(void *env, void *this, void *file) {
    return Java_java_io_UnixFileSystem_list(env, this, file);
}
EXPORT int32_t Java_java_io_UnixFileSystem_setLastModifiedTime0(void *env, void *this, void *file, int64_t time) {
    return Java_java_io_UnixFileSystem_setLastModifiedTime(env, this, file, time);
}
EXPORT int32_t Java_java_io_UnixFileSystem_setPermission0(void *env, void *this, void *file, int32_t access, int32_t enable, int32_t owneronly) {
    return Java_java_io_UnixFileSystem_setPermission(env, this, file, access, enable, owneronly);
}

// FileDispatcherImpl direct POSIX implementations
extern int32_t Java_sun_nio_ch_FileDispatcherImpl_read0(void *env, void *clazz, void *fd, int64_t address, int32_t len);
extern int32_t Java_sun_nio_ch_FileDispatcherImpl_write0(void *env, void *clazz, void *fd, int64_t address, int32_t len);
extern void    Java_sun_nio_ch_FileDispatcherImpl_closeIntFD(void *env, void *clazz, int32_t fd);
extern int64_t Java_sun_nio_ch_FileDispatcherImpl_size0(void *env, void *clazz, void *fd);
extern int64_t Java_sun_nio_ch_FileDispatcherImpl_seek0(void *env, void *clazz, void *fd, int64_t offset);
extern int32_t Java_sun_nio_ch_FileDispatcherImpl_truncate0(void *env, void *clazz, void *fd, int64_t size);
extern int32_t Java_sun_nio_ch_FileDispatcherImpl_force0(void *env, void *clazz, void *fd, int32_t md);
extern int32_t Java_sun_nio_ch_FileDispatcherImpl_pread0(void *env, void *clazz, void *fd, int64_t address, int32_t len, int64_t position);
extern int32_t Java_sun_nio_ch_FileDispatcherImpl_pwrite0(void *env, void *clazz, void *fd, int64_t address, int32_t len, int64_t position);
extern int32_t Java_sun_nio_ch_FileDispatcherImpl_lock0(void *env, void *clazz, void *fd, int32_t blocking, int64_t position, int64_t size, int32_t shared);
extern void    Java_sun_nio_ch_FileDispatcherImpl_release0(void *env, void *clazz, void *fd, int64_t position, int64_t size);

EXPORT int64_t Java_sun_nio_ch_FileDispatcherImpl_map0(void *env, void *clazz, void *fd, int32_t prot, int64_t position, int64_t length, int32_t isSync) {
    int native_prot = 0;
    int flags = MAP_SHARED;
    if (prot == 0) native_prot = PROT_READ;
    else if (prot == 1) native_prot = PROT_READ | PROT_WRITE;
    else if (prot == 2) { native_prot = PROT_READ | PROT_WRITE; flags = MAP_PRIVATE; }
    void *res = mmap(NULL, (size_t)length, native_prot, flags, *(int*)fd, (off_t)position);
    if (res == MAP_FAILED) return -1;
    return (int64_t)(uintptr_t)res;
}

EXPORT int32_t Java_sun_nio_ch_FileDispatcherImpl_unmap0(void *env, void *clazz, int64_t address, int64_t length) {
    return munmap((void*)(uintptr_t)address, (size_t)length);
}

// UnixFileDispatcherImpl delegates directly to FileDispatcherImpl
EXPORT int32_t Java_sun_nio_ch_UnixFileDispatcherImpl_read0(void *env, void *clazz, void *fd, int64_t address, int32_t len) {
    return Java_sun_nio_ch_FileDispatcherImpl_read0(env, clazz, fd, address, len);
}
EXPORT int32_t Java_sun_nio_ch_UnixFileDispatcherImpl_write0(void *env, void *clazz, void *fd, int64_t address, int32_t len) {
    return Java_sun_nio_ch_FileDispatcherImpl_write0(env, clazz, fd, address, len);
}
EXPORT void Java_sun_nio_ch_UnixFileDispatcherImpl_closeIntFD(void *env, void *clazz, int32_t fd) {
    Java_sun_nio_ch_FileDispatcherImpl_closeIntFD(env, clazz, fd);
}
EXPORT int64_t Java_sun_nio_ch_UnixFileDispatcherImpl_size0(void *env, void *clazz, void *fd) {
    return Java_sun_nio_ch_FileDispatcherImpl_size0(env, clazz, fd);
}
EXPORT int64_t Java_sun_nio_ch_UnixFileDispatcherImpl_seek0(void *env, void *clazz, void *fd, int64_t offset) {
    return Java_sun_nio_ch_FileDispatcherImpl_seek0(env, clazz, fd, offset);
}
EXPORT int32_t Java_sun_nio_ch_UnixFileDispatcherImpl_truncate0(void *env, void *clazz, void *fd, int64_t size) {
    return Java_sun_nio_ch_FileDispatcherImpl_truncate0(env, clazz, fd, size);
}
EXPORT int64_t Java_sun_nio_ch_UnixFileDispatcherImpl_map0(void *env, void *clazz, void *fd, int32_t prot, int64_t position, int64_t length, int32_t isSync) {
    return Java_sun_nio_ch_FileDispatcherImpl_map0(env, clazz, fd, prot, position, length, isSync);
}
EXPORT int32_t Java_sun_nio_ch_UnixFileDispatcherImpl_unmap0(void *env, void *clazz, int64_t address, int64_t length) {
    return Java_sun_nio_ch_FileDispatcherImpl_unmap0(env, clazz, address, length);
}
EXPORT int32_t Java_sun_nio_ch_UnixFileDispatcherImpl_force0(void *env, void *clazz, void *fd, int32_t md) {
    return Java_sun_nio_ch_FileDispatcherImpl_force0(env, clazz, fd, md);
}
EXPORT int32_t Java_sun_nio_ch_UnixFileDispatcherImpl_pread0(void *env, void *clazz, void *fd, int64_t address, int32_t len, int64_t position) {
    return Java_sun_nio_ch_FileDispatcherImpl_pread0(env, clazz, fd, address, len, position);
}
EXPORT int32_t Java_sun_nio_ch_UnixFileDispatcherImpl_pwrite0(void *env, void *clazz, void *fd, int64_t address, int32_t len, int64_t position) {
    return Java_sun_nio_ch_FileDispatcherImpl_pwrite0(env, clazz, fd, address, len, position);
}
EXPORT int32_t Java_sun_nio_ch_UnixFileDispatcherImpl_lock0(void *env, void *clazz, void *fd, int32_t blocking, int64_t position, int64_t size, int32_t shared) {
    return Java_sun_nio_ch_FileDispatcherImpl_lock0(env, clazz, fd, blocking, position, size, shared);
}
EXPORT void Java_sun_nio_ch_UnixFileDispatcherImpl_release0(void *env, void *clazz, void *fd, int64_t position, int64_t size) {
    Java_sun_nio_ch_FileDispatcherImpl_release0(env, clazz, fd, position, size);
}
EXPORT int32_t Java_sun_nio_ch_UnixFileDispatcherImpl_setDirect0(void *env, void *clazz, void *fd) {
    return 0;
}
EXPORT int64_t Java_sun_nio_ch_UnixFileDispatcherImpl_allocationGranularity0(void *env, void *clazz) {
    return (int64_t)getpagesize();
}

// UnixNativeDispatcher (JDK 18 base names -> JDK 21 "0" suffix)
extern int32_t Java_sun_nio_fs_UnixNativeDispatcher_fchmod(void *env, void *clazz, int32_t fd, int32_t mode);
extern int32_t Java_sun_nio_fs_UnixNativeDispatcher_fchown(void *env, void *clazz, int32_t fd, int32_t uid, int32_t gid);
extern int32_t Java_sun_nio_fs_UnixNativeDispatcher_fstat(void *env, void *clazz, int32_t fd, void *buf);
extern void    Java_sun_nio_fs_UnixNativeDispatcher_futimens(void *env, void *clazz, int32_t fd, int64_t asec, int64_t ansec, int64_t msec, int64_t mnsec);
extern void    Java_sun_nio_fs_UnixNativeDispatcher_futimes(void *env, void *clazz, int32_t fd, int64_t atime, int64_t mtime);
extern int32_t Java_sun_nio_fs_UnixNativeDispatcher_read(void *env, void *clazz, int32_t fd, int64_t address, int32_t len);
extern int32_t Java_sun_nio_fs_UnixNativeDispatcher_readdir(void *env, void *clazz, int64_t ptr, void *entry);
extern int32_t Java_sun_nio_fs_UnixNativeDispatcher_write(void *env, void *clazz, int32_t fd, int64_t address, int32_t len);

EXPORT int32_t Java_sun_nio_fs_UnixNativeDispatcher_fchmod0(void *env, void *clazz, int32_t fd, int32_t mode) {
    return Java_sun_nio_fs_UnixNativeDispatcher_fchmod(env, clazz, fd, mode);
}
EXPORT int32_t Java_sun_nio_fs_UnixNativeDispatcher_fchown0(void *env, void *clazz, int32_t fd, int32_t uid, int32_t gid) {
    return Java_sun_nio_fs_UnixNativeDispatcher_fchown(env, clazz, fd, uid, gid);
}
EXPORT int32_t Java_sun_nio_fs_UnixNativeDispatcher_fstat0(void *env, void *clazz, int32_t fd, void *buf) {
    return Java_sun_nio_fs_UnixNativeDispatcher_fstat(env, clazz, fd, buf);
}
EXPORT void Java_sun_nio_fs_UnixNativeDispatcher_futimens0(void *env, void *clazz, int32_t fd, int64_t asec, int64_t ansec, int64_t msec, int64_t mnsec) {
    Java_sun_nio_fs_UnixNativeDispatcher_futimens(env, clazz, fd, asec, ansec, msec, mnsec);
}
EXPORT void Java_sun_nio_fs_UnixNativeDispatcher_futimes0(void *env, void *clazz, int32_t fd, int64_t atime, int64_t mtime) {
    Java_sun_nio_fs_UnixNativeDispatcher_futimes(env, clazz, fd, atime, mtime);
}
EXPORT int32_t Java_sun_nio_fs_UnixNativeDispatcher_read0(void *env, void *clazz, int32_t fd, int64_t address, int32_t len) {
    return Java_sun_nio_fs_UnixNativeDispatcher_read(env, clazz, fd, address, len);
}
EXPORT int32_t Java_sun_nio_fs_UnixNativeDispatcher_readdir0(void *env, void *clazz, int64_t ptr, void *entry) {
    return Java_sun_nio_fs_UnixNativeDispatcher_readdir(env, clazz, ptr, entry);
}
EXPORT int32_t Java_sun_nio_fs_UnixNativeDispatcher_write0(void *env, void *clazz, int32_t fd, int64_t address, int32_t len) {
    return Java_sun_nio_fs_UnixNativeDispatcher_write(env, clazz, fd, address, len);
}

// FileDispatcherImpl init0, transfer, NativeThread, Net, SocketDispatcher, UnixDispatcher
extern void    Java_sun_nio_ch_FileDispatcherImpl_init(void *env, void *clazz);
extern int64_t Java_sun_nio_ch_NativeThread_current(void *env, void *clazz);
extern void    Java_sun_nio_ch_NativeThread_signal(void *env, void *clazz, int64_t thread);

EXPORT void Java_sun_nio_ch_FileDispatcherImpl_init0(void *env, void *clazz) {
    Java_sun_nio_ch_FileDispatcherImpl_init(env, clazz);
}
EXPORT int64_t Java_sun_nio_ch_FileDispatcherImpl_transferFrom0(void *env, void *clazz, void *srcFD, void *dstFD, int64_t position, int64_t count) {
    return -1;
}
EXPORT int64_t Java_sun_nio_ch_FileDispatcherImpl_transferTo0(void *env, void *clazz, void *srcFD, int64_t position, int64_t count, void *dstFD) {
    return -1;
}
EXPORT int64_t Java_sun_nio_ch_NativeThread_current0(void *env, void *clazz) {
    return Java_sun_nio_ch_NativeThread_current(env, clazz);
}
EXPORT void Java_sun_nio_ch_NativeThread_signal0(void *env, void *clazz, int64_t thread) {
    Java_sun_nio_ch_NativeThread_signal(env, clazz, thread);
}
EXPORT int32_t Java_sun_nio_ch_Net_shouldShutdownWriteBeforeClose0(void *env, void *clazz) {
    return 0;
}
EXPORT int32_t Java_sun_nio_ch_SocketDispatcher_write0(void *env, void *clazz, void *fd, int64_t address, int32_t len) {
    return (int32_t)write(*(int*)fd, (const void*)(uintptr_t)address, (size_t)len);
}
EXPORT int64_t Java_sun_nio_ch_SocketDispatcher_writev0(void *env, void *clazz, void *fd, int64_t address, int32_t len) {
    return (int64_t)writev(*(int*)fd, (const struct iovec*)(uintptr_t)address, len);
}
EXPORT void Java_sun_nio_ch_UnixDispatcher_close0(void *env, void *clazz, void *fd) {
    close(*(int*)fd);
}
EXPORT void Java_sun_nio_ch_UnixDispatcher_preClose0(void *env, void *clazz, void *fd) {
    close(*(int*)fd);
}

// Miscellaneous JDK 21 stubs
EXPORT int32_t Java_java_net_InetAddress_isIPv6Supported(void *env, void *clazz) {
    return 1;
}
EXPORT int64_t Java_jdk_internal_platform_CgroupMetrics_getTotalMemorySize0(void *env, void *clazz) {
    return 0;
}
EXPORT int64_t Java_jdk_internal_platform_CgroupMetrics_getTotalSwapSize0(void *env, void *clazz) {
    return 0;
}
EXPORT int32_t Java_jdk_net_LinuxSocketOptions_getIpDontFragment0(void *env, void *clazz, int32_t fd) {
    return 0;
}
EXPORT void Java_jdk_net_LinuxSocketOptions_setIpDontFragment0(void *env, void *clazz, int32_t fd, int32_t opt) {
}
EXPORT int32_t Java_jdk_net_LinuxSocketOptions_getTcpKeepAliveProbes0(void *env, void *clazz, int32_t fd) {
    return 0;
}
EXPORT void Java_jdk_net_LinuxSocketOptions_setTcpKeepAliveProbes0(void *env, void *clazz, int32_t fd, int32_t opt) {
}
EXPORT int32_t Java_sun_nio_fs_LinuxNativeDispatcher_directCopy0(void *env, void *clazz, int32_t dst, int32_t src, int64_t address) {
    return -1;
}
EXPORT int32_t Java_sun_nio_fs_LinuxNativeDispatcher_posix_1fadvise(void *env, void *clazz, int32_t fd, int64_t offset, int64_t len, int32_t advice) {
    return posix_fadvise(fd, offset, len, advice);
}
EXPORT int32_t Java_sun_nio_fs_UnixFileSystem_bufferedCopy0(void *env, void *clazz, int32_t dst, int32_t src, int64_t address) {
    return -1;
}
