#ifndef SOCKET_COMPAT_H
#define SOCKET_COMPAT_H

/**
 * Socket兼容层 - 跨平台支持
 * 
 * 这个头文件提供了Windows Winsock和POSIX Socket之间的兼容层
 * 使得代码可以在Windows、macOS和Linux上无缝编译运行
 */

#ifdef _WIN32
    // ========== Windows平台 (Winsock) ==========
    #include <winsock2.h>
    #include <ws2tcpip.h>
    #include <windows.h>
    
    // 链接Winsock库
    #pragma comment(lib, "ws2_32.lib")
    
    // 类型定义
    typedef SOCKET socket_t;
    typedef int socklen_t;
    
    // 函数宏
    #define CLOSE_SOCKET closesocket
    #define SOCKET_ERROR_CODE WSAGetLastError()
    
    // 错误码映射
    #define EWOULDBLOCK WSAEWOULDBLOCK
    #define EINPROGRESS WSAEINPROGRESS
    #define ECONNRESET WSAECONNRESET
    
#else
    // ========== POSIX平台 (BSD Socket) - macOS/Linux ==========
    #include <sys/types.h>
    #include <sys/socket.h>
    #include <netinet/in.h>
    #include <netinet/tcp.h>
    #include <arpa/inet.h>
    #include <unistd.h>
    #include <fcntl.h>
    #include <errno.h>
    #include <netdb.h>
    #include <string.h>
    
    // 类型定义
    typedef int socket_t;
    
    // 常量定义（兼容Winsock）
    #ifndef INVALID_SOCKET
    #define INVALID_SOCKET -1
    #endif
    
    #ifndef SOCKET_ERROR
    #define SOCKET_ERROR -1
    #endif
    
    #ifndef SOMAXCONN
    #define SOMAXCONN 128
    #endif
    
    // 函数宏
    #define CLOSE_SOCKET close
    #define SOCKET_ERROR_CODE errno
    
    // Winsock兼容函数（空实现）
    inline int WSAStartup(unsigned short, void*) { 
        return 0; 
    }
    
    inline int WSACleanup() { 
        return 0; 
    }
    
    inline int WSAGetLastError() { 
        return errno; 
    }
    
    // Socket选项兼容
    #ifndef SD_RECEIVE
    #define SD_RECEIVE SHUT_RD
    #endif
    
    #ifndef SD_SEND
    #define SD_SEND SHUT_WR
    #endif
    
    #ifndef SD_BOTH
    #define SD_BOTH SHUT_RDWR
    #endif
    
#endif

// ========== 跨平台辅助函数 ==========

/**
 * 设置socket为非阻塞模式
 */
inline bool setNonBlocking(socket_t sock) {
#ifdef _WIN32
    unsigned long mode = 1;
    return ioctlsocket(sock, FIONBIO, &mode) == 0;
#else
    int flags = fcntl(sock, F_GETFL, 0);
    if (flags == -1) return false;
    return fcntl(sock, F_SETFL, flags | O_NONBLOCK) != -1;
#endif
}

/**
 * 设置socket选项 - 地址重用
 */
inline bool setReuseAddr(socket_t sock) {
    int optval = 1;
    return setsockopt(sock, SOL_SOCKET, SO_REUSEADDR, 
                     (const char*)&optval, sizeof(optval)) == 0;
}

/**
 * 设置socket选项 - 保持连接
 */
inline bool setKeepAlive(socket_t sock, bool enable) {
    int optval = enable ? 1 : 0;
    return setsockopt(sock, SOL_SOCKET, SO_KEEPALIVE, 
                     (const char*)&optval, sizeof(optval)) == 0;
}

/**
 * 设置socket选项 - TCP_NODELAY (禁用Nagle算法)
 */
inline bool setTcpNoDelay(socket_t sock, bool enable) {
    int optval = enable ? 1 : 0;
    return setsockopt(sock, IPPROTO_TCP, TCP_NODELAY, 
                     (const char*)&optval, sizeof(optval)) == 0;
}

/**
 * 获取socket错误信息
 */
inline const char* getSocketError() {
#ifdef _WIN32
    static char buffer[256];
    FormatMessageA(FORMAT_MESSAGE_FROM_SYSTEM | FORMAT_MESSAGE_IGNORE_INSERTS,
                  NULL, WSAGetLastError(), 0, buffer, sizeof(buffer), NULL);
    return buffer;
#else
    return strerror(errno);
#endif
}

/**
 * 检查socket是否有效
 */
inline bool isValidSocket(socket_t sock) {
    return sock != INVALID_SOCKET;
}

/**
 * 安全关闭socket
 */
inline void safeCloseSocket(socket_t& sock) {
    if (isValidSocket(sock)) {
        CLOSE_SOCKET(sock);
        sock = INVALID_SOCKET;
    }
}

/**
 * 初始化网络库（跨平台）
 */
inline bool initializeNetwork() {
#ifdef _WIN32
    WSADATA wsaData;
    return WSAStartup(MAKEWORD(2, 2), &wsaData) == 0;
#else
    // POSIX系统不需要初始化
    return true;
#endif
}

/**
 * 清理网络库（跨平台）
 */
inline void cleanupNetwork() {
#ifdef _WIN32
    WSACleanup();
#else
    // POSIX系统不需要清理
#endif
}

// ========== 平台信息 ==========

inline const char* getPlatformName() {
#ifdef _WIN32
    return "Windows (Winsock)";
#elif __APPLE__
    return "macOS (BSD Socket)";
#elif __linux__
    return "Linux (BSD Socket)";
#else
    return "Unknown Platform";
#endif
}

#endif // SOCKET_COMPAT_H
