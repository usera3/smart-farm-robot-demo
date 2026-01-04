#ifndef FARM_SERVER_H
#define FARM_SERVER_H

#include "protocol.h"
#include "socket_compat.h"  // 跨平台Socket兼容层
#include <map>
#include <vector>
#include <thread>
#include <mutex>
#include <functional>
#include <queue>
#include <fstream>
#include <string>
#include <ctime>

// 日志级别
enum class LogLevel {
    INFO,
    WARNING,
    ERROR,
    DEBUG
};

// 日志条目
struct LogEntry {
    time_t timestamp;
    LogLevel level;
    std::string message;
    std::string clientInfo;
};

// 服务器配置
struct ServerConfig {
    uint16_t port;
    int maxClients;
    int heartbeatInterval;  // 秒
    int clientTimeout;      // 秒
    bool enableLogging;
    std::string logFilePath;
    
    ServerConfig() 
        : port(8888), maxClients(10), heartbeatInterval(5), 
          clientTimeout(30), enableLogging(true), 
          logFilePath("server.log") {}
};

// 服务器状态
struct ServerStatus {
    bool isRunning;
    int connectedClients;
    int totalConnections;
    int totalCommandsProcessed;
    time_t startTime;
    std::string pythonStatus;
    
    ServerStatus() 
        : isRunning(false), connectedClients(0), 
          totalConnections(0), totalCommandsProcessed(0), 
          startTime(0), pythonStatus("Not initialized") {}
};

// 回调函数类型定义
using LogCallback = std::function<void(const LogEntry&)>;
using ClientConnectCallback = std::function<void(int clientId, const std::string& ip)>;
using ClientDisconnectCallback = std::function<void(int clientId)>;
using StateUpdateCallback = std::function<void(const std::string& stateJson)>;

class FarmServer {
public:
    FarmServer();
    ~FarmServer();
    
    // 服务器控制
    bool start(const ServerConfig& config);
    void stop();
    bool isRunning() const { return m_status.isRunning; }
    
    // 获取状态
    ServerStatus getStatus() const;
    std::vector<ClientInfo> getConnectedClients() const;
    std::vector<LogEntry> getRecentLogs(int count = 100) const;
    
    // 广播消息
    void broadcastStateUpdate(const std::string& stateJson);
    void broadcastLogMessage(const std::string& message);
    
    // 发送消息给特定客户端
    bool sendToClient(int clientId, const Packet& packet);
    
    // 断开客户端
    void disconnectClient(int clientId);
    
    // 设置回调函数
    void setLogCallback(LogCallback callback) { m_logCallback = callback; }
    void setClientConnectCallback(ClientConnectCallback callback) { m_connectCallback = callback; }
    void setClientDisconnectCallback(ClientDisconnectCallback callback) { m_disconnectCallback = callback; }
    void setStateUpdateCallback(StateUpdateCallback callback) { m_stateUpdateCallback = callback; }
    
    // Python集成接口
    bool initializePython(const std::string& pythonHome);
    void shutdownPython();
    std::string callPythonFunction(const std::string& module, const std::string& function, 
                                   const std::string& args);
    
private:
    // 网络相关
    socket_t m_listenSocket;  // 使用跨平台socket类型
    ServerConfig m_config;
    ServerStatus m_status;
    
    // 客户端管理
    std::map<int, socket_t> m_clientSockets;  // 使用跨平台socket类型
    std::map<int, ClientInfo> m_clientInfos;
    int m_nextClientId;
    mutable std::mutex m_clientsMutex;
    
    // 日志管理
    std::queue<LogEntry> m_logQueue;
    mutable std::mutex m_logMutex;
    std::ofstream m_logFile;
    
    // 线程管理
    std::thread m_acceptThread;
    std::map<int, std::thread> m_clientThreads;
    std::thread m_heartbeatThread;
    bool m_shouldStop;
    
    // 回调函数
    LogCallback m_logCallback;
    ClientConnectCallback m_connectCallback;
    ClientDisconnectCallback m_disconnectCallback;
    StateUpdateCallback m_stateUpdateCallback;
    
    // Python相关
    bool m_pythonInitialized;
    
    // 内部方法
    void acceptLoop();
    void clientLoop(int clientId, socket_t clientSocket);  // 使用跨平台socket类型
    void heartbeatLoop();
    
    bool receivePacket(socket_t socket, Packet& packet);  // 使用跨平台socket类型
    bool sendPacket(socket_t socket, const Packet& packet);  // 使用跨平台socket类型
    
    void handleCommand(int clientId, const Packet& packet);
    void handleConnect(int clientId, const std::string& data);
    void handleGetState(int clientId);
    void handleGetPlants(int clientId);
    void handleMoveCart(int clientId, const std::string& data);
    void handleRotateCart(int clientId, const std::string& data);
    void handlePlantSeed(int clientId, const std::string& data);
    void handleWaterPlant(int clientId, const std::string& data);
    void handleHarvest(int clientId, const std::string& data);
    void handleRemoveWeed(int clientId, const std::string& data);
    void handleAutoFarmStart(int clientId);
    void handleAutoFarmStop(int clientId);
    void handleAutoFarmStatus(int clientId);
    void handleSwitchEquipment(int clientId, const std::string& data);
    void handleSwitchCamera(int clientId, const std::string& data);
    
    void sendSuccess(int clientId, const std::string& message = "");
    void sendError(int clientId, uint32_t errorCode, const std::string& message);
    
    void log(LogLevel level, const std::string& message, int clientId = -1);
    void writeLogToFile(const LogEntry& entry);
    
    void cleanupClient(int clientId);
    void checkClientTimeouts();
    
    // 禁止拷贝
    FarmServer(const FarmServer&) = delete;
    FarmServer& operator=(const FarmServer&) = delete;
};

#endif // FARM_SERVER_H
