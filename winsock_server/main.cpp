#include "FarmServer.h"
#include <iostream>
#include <fstream>
#include <sstream>
#include <signal.h>

// 全局服务器实例（用于信号处理）
FarmServer* g_server = nullptr;

// 信号处理函数
void signalHandler(int signal) {
    if (signal == SIGINT || signal == SIGTERM) {
        std::cout << "\nReceived shutdown signal, stopping server..." << std::endl;
        if (g_server) {
            g_server->stop();
        }
        exit(0);
    }
}

// 加载配置文件
bool loadConfig(const std::string& filename, ServerConfig& config) {
    std::ifstream file(filename);
    if (!file.is_open()) {
        std::cerr << "Failed to open config file: " << filename << std::endl;
        return false;
    }
    
    // 简单的配置文件解析（实际项目中应使用JSON库）
    std::string line;
    while (std::getline(file, line)) {
        // 跳过注释和空行
        if (line.empty() || line[0] == '#' || line[0] == '/') {
            continue;
        }
        
        // 解析键值对
        size_t pos = line.find('=');
        if (pos != std::string::npos) {
            std::string key = line.substr(0, pos);
            std::string value = line.substr(pos + 1);
            
            // 去除空格
            key.erase(0, key.find_first_not_of(" \t"));
            key.erase(key.find_last_not_of(" \t") + 1);
            value.erase(0, value.find_first_not_of(" \t"));
            value.erase(value.find_last_not_of(" \t") + 1);
            
            // 设置配置项
            if (key == "port") {
                config.port = static_cast<uint16_t>(std::stoi(value));
            } else if (key == "max_clients") {
                config.maxClients = std::stoi(value);
            } else if (key == "heartbeat_interval") {
                config.heartbeatInterval = std::stoi(value);
            } else if (key == "client_timeout") {
                config.clientTimeout = std::stoi(value);
            } else if (key == "enable_logging") {
                config.enableLogging = (value == "true" || value == "1");
            } else if (key == "log_file_path") {
                config.logFilePath = value;
            }
        }
    }
    
    file.close();
    return true;
}

// 打印帮助信息
void printHelp() {
    std::cout << "Farm Server - Winsock Remote Control System\n" << std::endl;
    std::cout << "Usage: FarmServer [options]\n" << std::endl;
    std::cout << "Options:" << std::endl;
    std::cout << "  --port <port>        Server port (default: 8888)" << std::endl;
    std::cout << "  --config <file>      Configuration file path" << std::endl;
    std::cout << "  --max-clients <n>    Maximum number of clients (default: 10)" << std::endl;
    std::cout << "  --debug              Enable debug logging" << std::endl;
    std::cout << "  --help               Show this help message" << std::endl;
    std::cout << "\nCommands (while running):" << std::endl;
    std::cout << "  status               Show server status" << std::endl;
    std::cout << "  clients              List connected clients" << std::endl;
    std::cout << "  logs [n]             Show last n log entries (default: 10)" << std::endl;
    std::cout << "  broadcast <msg>      Broadcast message to all clients" << std::endl;
    std::cout << "  quit                 Stop server and exit" << std::endl;
}

// 打印服务器状态
void printStatus(FarmServer& server) {
    ServerStatus status = server.getStatus();
    
    std::cout << "\n=== Server Status ===" << std::endl;
    std::cout << "Running: " << (status.isRunning ? "Yes" : "No") << std::endl;
    std::cout << "Connected Clients: " << status.connectedClients << std::endl;
    std::cout << "Total Connections: " << status.totalConnections << std::endl;
    std::cout << "Commands Processed: " << status.totalCommandsProcessed << std::endl;
    
    time_t uptime = time(nullptr) - status.startTime;
    int hours = uptime / 3600;
    int minutes = (uptime % 3600) / 60;
    int seconds = uptime % 60;
    std::cout << "Uptime: " << hours << "h " << minutes << "m " << seconds << "s" << std::endl;
    std::cout << "Python Status: " << status.pythonStatus << std::endl;
    std::cout << "=====================\n" << std::endl;
}

// 打印客户端列表
void printClients(FarmServer& server) {
    std::vector<ClientInfo> clients = server.getConnectedClients();
    
    std::cout << "\n=== Connected Clients ===" << std::endl;
    if (clients.empty()) {
        std::cout << "No clients connected." << std::endl;
    } else {
        std::cout << "ID\tIP Address\t\tPort\tConnected\tLast Activity" << std::endl;
        std::cout << "------------------------------------------------------------" << std::endl;
        
        for (const auto& client : clients) {
            time_t connectedTime = time(nullptr) - client.connectTime;
            time_t lastActivityTime = time(nullptr) - client.lastActivityTime;
            
            std::cout << client.clientId << "\t"
                     << client.ipAddress << "\t\t"
                     << client.port << "\t"
                     << connectedTime << "s ago\t"
                     << lastActivityTime << "s ago" << std::endl;
        }
    }
    std::cout << "=========================\n" << std::endl;
}

// 打印日志
void printLogs(FarmServer& server, int count) {
    std::vector<LogEntry> logs = server.getRecentLogs(count);
    
    std::cout << "\n=== Recent Logs ===" << std::endl;
    for (const auto& log : logs) {
        char timeStr[64];
        struct tm* timeInfo = localtime(&log.timestamp);
        strftime(timeStr, sizeof(timeStr), "%H:%M:%S", timeInfo);
        
        std::cout << "[" << timeStr << "] ";
        
        switch (log.level) {
            case LogLevel::INFO:    std::cout << "[INFO] "; break;
            case LogLevel::WARNING: std::cout << "[WARN] "; break;
            case LogLevel::ERROR:   std::cout << "[ERROR] "; break;
            case LogLevel::DEBUG:   std::cout << "[DEBUG] "; break;
        }
        
        if (!log.clientInfo.empty()) {
            std::cout << "[" << log.clientInfo << "] ";
        }
        
        std::cout << log.message << std::endl;
    }
    std::cout << "===================\n" << std::endl;
}

// 主函数
int main(int argc, char* argv[]) {
    std::cout << "========================================" << std::endl;
    std::cout << "  Farm Server - Winsock Control System  " << std::endl;
    std::cout << "========================================\n" << std::endl;
    
    // 默认配置
    ServerConfig config;
    config.port = 8888;
    config.maxClients = 10;
    config.heartbeatInterval = 5;
    config.clientTimeout = 30;
    config.enableLogging = true;
    config.logFilePath = "server.log";
    
    std::string configFile;
    bool debugMode = false;
    
    // 解析命令行参数
    for (int i = 1; i < argc; i++) {
        std::string arg = argv[i];
        
        if (arg == "--help" || arg == "-h") {
            printHelp();
            return 0;
        } else if (arg == "--port" && i + 1 < argc) {
            config.port = static_cast<uint16_t>(std::stoi(argv[++i]));
        } else if (arg == "--config" && i + 1 < argc) {
            configFile = argv[++i];
        } else if (arg == "--max-clients" && i + 1 < argc) {
            config.maxClients = std::stoi(argv[++i]);
        } else if (arg == "--debug") {
            debugMode = true;
        }
    }
    
    // 加载配置文件
    if (!configFile.empty()) {
        if (!loadConfig(configFile, config)) {
            std::cerr << "Warning: Failed to load config file, using defaults" << std::endl;
        }
    }
    
    // 创建服务器实例
    FarmServer server;
    g_server = &server;
    
    // 设置信号处理
    signal(SIGINT, signalHandler);
    signal(SIGTERM, signalHandler);
    
    // 设置日志回调（可选）
    if (debugMode) {
        server.setLogCallback([](const LogEntry& entry) {
            // 日志已经在FarmServer内部输出到控制台
        });
    }
    
    // 启动服务器
    std::cout << "Starting server on port " << config.port << "..." << std::endl;
    if (!server.start(config)) {
        std::cerr << "Failed to start server!" << std::endl;
        return 1;
    }
    
    std::cout << "Server started successfully!" << std::endl;
    std::cout << "Type 'help' for available commands, 'quit' to stop.\n" << std::endl;
    
    // TODO: 初始化Python（如果需要）
    // server.initializePython("C:/Python38");
    
    // 命令循环
    std::string command;
    while (true) {
        std::cout << "> ";
        std::getline(std::cin, command);
        
        if (command.empty()) {
            continue;
        }
        
        // 解析命令
        std::istringstream iss(command);
        std::string cmd;
        iss >> cmd;
        
        if (cmd == "quit" || cmd == "exit") {
            std::cout << "Stopping server..." << std::endl;
            server.stop();
            break;
        } else if (cmd == "help") {
            printHelp();
        } else if (cmd == "status") {
            printStatus(server);
        } else if (cmd == "clients") {
            printClients(server);
        } else if (cmd == "logs") {
            int count = 10;
            if (iss >> count) {
                // 使用指定数量
            }
            printLogs(server, count);
        } else if (cmd == "broadcast") {
            std::string message;
            std::getline(iss, message);
            if (!message.empty()) {
                message = message.substr(1);  // 去掉前导空格
                server.broadcastLogMessage(message);
                std::cout << "Message broadcasted." << std::endl;
            } else {
                std::cout << "Usage: broadcast <message>" << std::endl;
            }
        } else {
            std::cout << "Unknown command: " << cmd << std::endl;
            std::cout << "Type 'help' for available commands." << std::endl;
        }
    }
    
    std::cout << "Server stopped. Goodbye!" << std::endl;
    return 0;
}
