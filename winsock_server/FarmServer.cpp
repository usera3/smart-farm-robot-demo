#include "FarmServer.h"
#include <iostream>
#include <sstream>
#include <fstream>
#include <chrono>
#include <iomanip>

// 构造函数
FarmServer::FarmServer() 
    : m_listenSocket(INVALID_SOCKET),
      m_nextClientId(1),
      m_shouldStop(false),
      m_pythonInitialized(false) {
}

// 析构函数
FarmServer::~FarmServer() {
    stop();
    if (m_pythonInitialized) {
        shutdownPython();
    }
}

// 启动服务器
bool FarmServer::start(const ServerConfig& config) {
    if (m_status.isRunning) {
        log(LogLevel::WARNING, "Server is already running");
        return false;
    }
    
    m_config = config;
    m_shouldStop = false;
    
    // 初始化网络库（跨平台）
    if (!initializeNetwork()) {
        log(LogLevel::ERROR, "Network initialization failed");
        return false;
    }
    
    log(LogLevel::INFO, std::string("Platform: ") + getPlatformName());
    
    // 创建监听socket
    m_listenSocket = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
    if (m_listenSocket == INVALID_SOCKET) {
        log(LogLevel::ERROR, "Socket creation failed: " + std::to_string(WSAGetLastError()));
        WSACleanup();
        return false;
    }
    
    // 设置socket选项（跨平台）
    setReuseAddr(m_listenSocket);
    
    // 绑定地址
    sockaddr_in serverAddr;
    serverAddr.sin_family = AF_INET;
    serverAddr.sin_addr.s_addr = INADDR_ANY;
    serverAddr.sin_port = htons(m_config.port);
    
    if (bind(m_listenSocket, (sockaddr*)&serverAddr, sizeof(serverAddr)) == SOCKET_ERROR) {
        log(LogLevel::ERROR, "Bind failed: " + std::to_string(SOCKET_ERROR_CODE));
        CLOSE_SOCKET(m_listenSocket);
        cleanupNetwork();
        return false;
    }
    
    // 开始监听
    if (listen(m_listenSocket, SOMAXCONN) == SOCKET_ERROR) {
        log(LogLevel::ERROR, "Listen failed: " + std::to_string(SOCKET_ERROR_CODE));
        CLOSE_SOCKET(m_listenSocket);
        cleanupNetwork();
        return false;
    }
    
    // 打开日志文件
    if (m_config.enableLogging) {
        m_logFile.open(m_config.logFilePath, std::ios::app);
        if (!m_logFile.is_open()) {
            log(LogLevel::WARNING, "Failed to open log file: " + m_config.logFilePath);
        }
    }
    
    // 更新状态
    m_status.isRunning = true;
    m_status.startTime = time(nullptr);
    m_status.connectedClients = 0;
    m_status.totalConnections = 0;
    m_status.totalCommandsProcessed = 0;
    
    // 启动线程
    m_acceptThread = std::thread(&FarmServer::acceptLoop, this);
    m_heartbeatThread = std::thread(&FarmServer::heartbeatLoop, this);
    
    log(LogLevel::INFO, "Server started on port " + std::to_string(m_config.port));
    
    return true;
}

// 停止服务器
void FarmServer::stop() {
    if (!m_status.isRunning) {
        return;
    }
    
    log(LogLevel::INFO, "Stopping server...");
    
    m_shouldStop = true;
    m_status.isRunning = false;
    
    // 关闭监听socket
    safeCloseSocket(m_listenSocket);
    
    // 断开所有客户端
    {
        std::lock_guard<std::mutex> lock(m_clientsMutex);
        for (auto& pair : m_clientSockets) {
            CLOSE_SOCKET(pair.second);
        }
        m_clientSockets.clear();
        m_clientInfos.clear();
    }
    
    // 等待线程结束
    if (m_acceptThread.joinable()) {
        m_acceptThread.join();
    }
    if (m_heartbeatThread.joinable()) {
        m_heartbeatThread.join();
    }
    for (auto& pair : m_clientThreads) {
        if (pair.second.joinable()) {
            pair.second.join();
        }
    }
    m_clientThreads.clear();
    
    // 关闭日志文件
    if (m_logFile.is_open()) {
        m_logFile.close();
    }
    
    // 清理网络库（跨平台）
    cleanupNetwork();
    
    log(LogLevel::INFO, "Server stopped");
}

// 接受连接循环
void FarmServer::acceptLoop() {
    while (!m_shouldStop) {
        sockaddr_in clientAddr;
        socklen_t clientAddrSize = sizeof(clientAddr);
        
        socket_t clientSocket = accept(m_listenSocket, (sockaddr*)&clientAddr, &clientAddrSize);
        
        if (clientSocket == INVALID_SOCKET) {
            if (!m_shouldStop) {
                log(LogLevel::ERROR, "Accept failed: " + std::to_string(SOCKET_ERROR_CODE));
            }
            continue;
        }
        
        // 检查客户端数量限制
        {
            std::lock_guard<std::mutex> lock(m_clientsMutex);
            if (m_clientSockets.size() >= (size_t)m_config.maxClients) {
                log(LogLevel::WARNING, "Max clients reached, rejecting connection");
                CLOSE_SOCKET(clientSocket);
                continue;
            }
        }
        
        // 获取客户端信息
        char ipStr[INET_ADDRSTRLEN];
        inet_ntop(AF_INET, &clientAddr.sin_addr, ipStr, INET_ADDRSTRLEN);
        uint16_t clientPort = ntohs(clientAddr.sin_port);
        
        // 分配客户端ID
        int clientId = m_nextClientId++;
        
        // 保存客户端信息
        {
            std::lock_guard<std::mutex> lock(m_clientsMutex);
            m_clientSockets[clientId] = clientSocket;
            
            ClientInfo info;
            info.clientId = clientId;
            info.ipAddress = ipStr;
            info.port = clientPort;
            info.connectTime = time(nullptr);
            info.lastActivityTime = time(nullptr);
            info.isAuthorized = false;
            m_clientInfos[clientId] = info;
            
            m_status.connectedClients++;
            m_status.totalConnections++;
        }
        
        log(LogLevel::INFO, "Client connected: " + std::string(ipStr) + ":" + 
            std::to_string(clientPort), clientId);
        
        // 触发回调
        if (m_connectCallback) {
            m_connectCallback(clientId, ipStr);
        }
        
        // 启动客户端处理线程
        m_clientThreads[clientId] = std::thread(&FarmServer::clientLoop, this, clientId, clientSocket);
    }
}

// 客户端处理循环
void FarmServer::clientLoop(int clientId, socket_t clientSocket) {
    log(LogLevel::DEBUG, "Client thread started", clientId);
    
    while (!m_shouldStop) {
        Packet packet;
        if (!receivePacket(clientSocket, packet)) {
            break;  // 连接断开或错误
        }
        
        // 更新最后活动时间
        {
            std::lock_guard<std::mutex> lock(m_clientsMutex);
            auto it = m_clientInfos.find(clientId);
            if (it != m_clientInfos.end()) {
                it->second.lastActivityTime = time(nullptr);
            }
        }
        
        // 处理命令
        handleCommand(clientId, packet);
        
        m_status.totalCommandsProcessed++;
    }
    
    // 清理客户端
    cleanupClient(clientId);
    
    log(LogLevel::DEBUG, "Client thread ended", clientId);
}

// 心跳检测循环
void FarmServer::heartbeatLoop() {
    while (!m_shouldStop) {
        std::this_thread::sleep_for(std::chrono::seconds(m_config.heartbeatInterval));
        
        if (m_shouldStop) break;
        
        checkClientTimeouts();
    }
}

// 接收数据包
bool FarmServer::receivePacket(socket_t socket, Packet& packet) {
    // 接收头部
    char headerBuffer[sizeof(PacketHeader)];
    int received = recv(socket, headerBuffer, sizeof(PacketHeader), MSG_WAITALL);
    
    if (received != sizeof(PacketHeader)) {
        return false;  // 连接断开或错误
    }
    
    // 解析头部
    memcpy(&packet.header, headerBuffer, sizeof(PacketHeader));
    
    // 验证魔数
    if (packet.header.magic != PROTOCOL_MAGIC) {
        return false;
    }
    
    // 接收数据
    if (packet.header.length > 0) {
        if (packet.header.length > MAX_PACKET_SIZE) {
            return false;  // 数据过大
        }
        
        std::vector<char> dataBuffer(packet.header.length);
        received = recv(socket, dataBuffer.data(), packet.header.length, MSG_WAITALL);
        
        if (received != (int)packet.header.length) {
            return false;
        }
        
        packet.data.assign(dataBuffer.begin(), dataBuffer.end());
    }
    
    return true;
}

// 发送数据包
bool FarmServer::sendPacket(socket_t socket, const Packet& packet) {
    std::string buffer = packet.serialize();
    
    int sent = send(socket, buffer.c_str(), (int)buffer.length(), 0);
    
    return sent == (int)buffer.length();
}

// 处理命令
void FarmServer::handleCommand(int clientId, const Packet& packet) {
    log(LogLevel::DEBUG, "Received command: 0x" + 
        std::to_string(packet.header.command), clientId);
    
    switch (packet.header.command) {
        case Command::CONNECT:
            handleConnect(clientId, packet.data);
            break;
        case Command::DISCONNECT:
            cleanupClient(clientId);
            break;
        case Command::GET_STATE:
            handleGetState(clientId);
            break;
        case Command::GET_PLANTS:
            handleGetPlants(clientId);
            break;
        case Command::MOVE_CART:
            handleMoveCart(clientId, packet.data);
            break;
        case Command::ROTATE_CART:
            handleRotateCart(clientId, packet.data);
            break;
        case Command::PLANT_SEED:
            handlePlantSeed(clientId, packet.data);
            break;
        case Command::WATER_PLANT:
            handleWaterPlant(clientId, packet.data);
            break;
        case Command::HARVEST:
            handleHarvest(clientId, packet.data);
            break;
        case Command::REMOVE_WEED:
            handleRemoveWeed(clientId, packet.data);
            break;
        case Command::AUTO_FARM_START:
            handleAutoFarmStart(clientId);
            break;
        case Command::AUTO_FARM_STOP:
            handleAutoFarmStop(clientId);
            break;
        case Command::AUTO_FARM_STATUS:
            handleAutoFarmStatus(clientId);
            break;
        case Command::SWITCH_EQUIPMENT:
            handleSwitchEquipment(clientId, packet.data);
            break;
        case Command::SWITCH_CAMERA:
            handleSwitchCamera(clientId, packet.data);
            break;
        default:
            sendError(clientId, ErrorCode::INVALID_COMMAND, "Unknown command");
            break;
    }
}

// 发送成功响应
void FarmServer::sendSuccess(int clientId, const std::string& message) {
    std::string jsonData = "{\"status\":\"success\"";
    if (!message.empty()) {
        jsonData += ",\"message\":\"" + message + "\"";
    }
    jsonData += "}";
    
    Packet response(Response::SUCCESS, jsonData);
    
    std::lock_guard<std::mutex> lock(m_clientsMutex);
    auto it = m_clientSockets.find(clientId);
    if (it != m_clientSockets.end()) {
        sendPacket(it->second, response);
    }
}

// 发送错误响应
void FarmServer::sendError(int clientId, uint32_t errorCode, const std::string& message) {
    std::ostringstream oss;
    oss << "{\"status\":\"error\",\"error_code\":" << errorCode 
        << ",\"error_message\":\"" << message << "\"}";
    
    Packet response(Response::ERROR, oss.str());
    
    std::lock_guard<std::mutex> lock(m_clientsMutex);
    auto it = m_clientSockets.find(clientId);
    if (it != m_clientSockets.end()) {
        sendPacket(it->second, response);
    }
}

// 记录日志
void FarmServer::log(LogLevel level, const std::string& message, int clientId) {
    LogEntry entry;
    entry.timestamp = time(nullptr);
    entry.level = level;
    entry.message = message;
    
    if (clientId >= 0) {
        std::lock_guard<std::mutex> lock(m_clientsMutex);
        auto it = m_clientInfos.find(clientId);
        if (it != m_clientInfos.end()) {
            entry.clientInfo = it->second.ipAddress + ":" + std::to_string(it->second.port);
        }
    }
    
    // 添加到日志队列
    {
        std::lock_guard<std::mutex> lock(m_logMutex);
        m_logQueue.push(entry);
        if (m_logQueue.size() > 1000) {  // 限制队列大小
            m_logQueue.pop();
        }
    }
    
    // 写入文件
    if (m_config.enableLogging) {
        writeLogToFile(entry);
    }
    
    // 触发回调
    if (m_logCallback) {
        m_logCallback(entry);
    }
    
    // 输出到控制台（调试用）
    std::cout << "[" << entry.timestamp << "] ";
    switch (level) {
        case LogLevel::INFO:    std::cout << "[INFO] "; break;
        case LogLevel::WARNING: std::cout << "[WARN] "; break;
        case LogLevel::ERROR:   std::cout << "[ERROR] "; break;
        case LogLevel::DEBUG:   std::cout << "[DEBUG] "; break;
    }
    if (!entry.clientInfo.empty()) {
        std::cout << "[" << entry.clientInfo << "] ";
    }
    std::cout << message << std::endl;
}

// 写入日志文件
void FarmServer::writeLogToFile(const LogEntry& entry) {
    if (!m_logFile.is_open()) return;
    
    char timeStr[64];
    struct tm* timeInfo = localtime(&entry.timestamp);
    strftime(timeStr, sizeof(timeStr), "%Y-%m-%d %H:%M:%S", timeInfo);
    
    m_logFile << "[" << timeStr << "] ";
    
    switch (entry.level) {
        case LogLevel::INFO:    m_logFile << "[INFO] "; break;
        case LogLevel::WARNING: m_logFile << "[WARN] "; break;
        case LogLevel::ERROR:   m_logFile << "[ERROR] "; break;
        case LogLevel::DEBUG:   m_logFile << "[DEBUG] "; break;
    }
    
    if (!entry.clientInfo.empty()) {
        m_logFile << "[" << entry.clientInfo << "] ";
    }
    
    m_logFile << entry.message << std::endl;
    m_logFile.flush();
}

// 清理客户端
void FarmServer::cleanupClient(int clientId) {
    log(LogLevel::INFO, "Disconnecting client", clientId);
    
    {
        std::lock_guard<std::mutex> lock(m_clientsMutex);
        
        auto socketIt = m_clientSockets.find(clientId);
        if (socketIt != m_clientSockets.end()) {
            CLOSE_SOCKET(socketIt->second);
            m_clientSockets.erase(socketIt);
        }
        
        m_clientInfos.erase(clientId);
        m_status.connectedClients--;
    }
    
    // 触发回调
    if (m_disconnectCallback) {
        m_disconnectCallback(clientId);
    }
}

// 检查客户端超时
void FarmServer::checkClientTimeouts() {
    time_t now = time(nullptr);
    std::vector<int> timeoutClients;
    
    {
        std::lock_guard<std::mutex> lock(m_clientsMutex);
        for (const auto& pair : m_clientInfos) {
            if (now - pair.second.lastActivityTime > m_config.clientTimeout) {
                timeoutClients.push_back(pair.first);
            }
        }
    }
    
    for (int clientId : timeoutClients) {
        log(LogLevel::WARNING, "Client timeout", clientId);
        cleanupClient(clientId);
    }
}

// 获取服务器状态
ServerStatus FarmServer::getStatus() const {
    return m_status;
}

// 获取连接的客户端列表
std::vector<ClientInfo> FarmServer::getConnectedClients() const {
    std::lock_guard<std::mutex> lock(m_clientsMutex);
    std::vector<ClientInfo> clients;
    for (const auto& pair : m_clientInfos) {
        clients.push_back(pair.second);
    }
    return clients;
}

// 获取最近的日志
std::vector<LogEntry> FarmServer::getRecentLogs(int count) const {
    std::lock_guard<std::mutex> lock(m_logMutex);
    std::vector<LogEntry> logs;
    
    std::queue<LogEntry> tempQueue = m_logQueue;
    while (!tempQueue.empty() && logs.size() < (size_t)count) {
        logs.push_back(tempQueue.front());
        tempQueue.pop();
    }
    
    return logs;
}

// 命令处理函数（占位符实现）
void FarmServer::handleConnect(int clientId, const std::string& data) {
    // TODO: 验证客户端身份
    {
        std::lock_guard<std::mutex> lock(m_clientsMutex);
        auto it = m_clientInfos.find(clientId);
        if (it != m_clientInfos.end()) {
            it->second.isAuthorized = true;
        }
    }
    sendSuccess(clientId, "Connected successfully");
}

void FarmServer::handleGetState(int clientId) {
    // TODO: 调用Python获取状态
    std::string stateJson = "{\"cart\":{\"x\":0,\"z\":0,\"rotation\":0},\"energy\":100,\"coins\":100}";
    Packet response(Response::STATE_UPDATE, stateJson);
    sendToClient(clientId, response);
}

void FarmServer::handleGetPlants(int clientId) {
    // TODO: 调用Python获取植物信息
    std::string plantsJson = "{\"plants\":[]}";
    Packet response(Response::PLANT_DATA, plantsJson);
    sendToClient(clientId, response);
}

void FarmServer::handleMoveCart(int clientId, const std::string& data) {
    // TODO: 调用Python移动小车
    sendSuccess(clientId, "Cart movement initiated");
}

void FarmServer::handleRotateCart(int clientId, const std::string& data) {
    // TODO: 调用Python旋转小车
    sendSuccess(clientId, "Cart rotation initiated");
}

void FarmServer::handlePlantSeed(int clientId, const std::string& data) {
    // TODO: 调用Python播种
    sendSuccess(clientId, "Seed planted");
}

void FarmServer::handleWaterPlant(int clientId, const std::string& data) {
    // TODO: 调用Python浇水
    sendSuccess(clientId, "Plant watered");
}

void FarmServer::handleHarvest(int clientId, const std::string& data) {
    // TODO: 调用Python收获
    sendSuccess(clientId, "Plant harvested");
}

void FarmServer::handleRemoveWeed(int clientId, const std::string& data) {
    // TODO: 调用Python除草
    sendSuccess(clientId, "Weed removed");
}

void FarmServer::handleAutoFarmStart(int clientId) {
    // TODO: 调用Python启动自动化
    sendSuccess(clientId, "Auto farm started");
}

void FarmServer::handleAutoFarmStop(int clientId) {
    // TODO: 调用Python停止自动化
    sendSuccess(clientId, "Auto farm stopped");
}

void FarmServer::handleAutoFarmStatus(int clientId) {
    // TODO: 调用Python获取自动化状态
    std::string statusJson = "{\"enabled\":false,\"current_task\":null}";
    Packet response(Response::AUTO_STATUS, statusJson);
    sendToClient(clientId, response);
}

void FarmServer::handleSwitchEquipment(int clientId, const std::string& data) {
    // TODO: 调用Python切换装备
    sendSuccess(clientId, "Equipment switched");
}

void FarmServer::handleSwitchCamera(int clientId, const std::string& data) {
    // TODO: 调用Python切换相机
    sendSuccess(clientId, "Camera mode switched");
}

// 发送消息给特定客户端
bool FarmServer::sendToClient(int clientId, const Packet& packet) {
    std::lock_guard<std::mutex> lock(m_clientsMutex);
    auto it = m_clientSockets.find(clientId);
    if (it != m_clientSockets.end()) {
        return sendPacket(it->second, packet);
    }
    return false;
}

// 广播状态更新
void FarmServer::broadcastStateUpdate(const std::string& stateJson) {
    Packet packet(Response::STATE_UPDATE, stateJson);
    
    std::lock_guard<std::mutex> lock(m_clientsMutex);
    for (const auto& pair : m_clientSockets) {
        sendPacket(pair.second, packet);
    }
}

// 广播日志消息
void FarmServer::broadcastLogMessage(const std::string& message) {
    std::string jsonData = "{\"message\":\"" + message + "\"}";
    Packet packet(Response::LOG_MESSAGE, jsonData);
    
    std::lock_guard<std::mutex> lock(m_clientsMutex);
    for (const auto& pair : m_clientSockets) {
        sendPacket(pair.second, packet);
    }
}

// Python集成（占位符）
bool FarmServer::initializePython(const std::string& pythonHome) {
    // TODO: 初始化Python解释器
    m_pythonInitialized = true;
    m_status.pythonStatus = "Initialized";
    log(LogLevel::INFO, "Python initialized");
    return true;
}

void FarmServer::shutdownPython() {
    if (m_pythonInitialized) {
        // TODO: 关闭Python解释器
        m_pythonInitialized = false;
        m_status.pythonStatus = "Shutdown";
        log(LogLevel::INFO, "Python shutdown");
    }
}

std::string FarmServer::callPythonFunction(const std::string& module, 
                                           const std::string& function, 
                                           const std::string& args) {
    if (!m_pythonInitialized) {
        return "{\"error\":\"Python not initialized\"}";
    }
    
    // TODO: 调用Python函数
    return "{}";
}
