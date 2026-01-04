#ifndef FARM_CLIENT_H
#define FARM_CLIENT_H

#include "../winsock_server/protocol.h"
#include <winsock2.h>
#include <ws2tcpip.h>
#include <string>
#include <functional>
#include <thread>
#include <mutex>
#include <queue>

#pragma comment(lib, "ws2_32.lib")

// 客户端状态
enum class ClientState {
    DISCONNECTED,
    CONNECTING,
    CONNECTED,
    ERROR
};

// 客户端配置
struct ClientConfig {
    std::string serverIP;
    uint16_t serverPort;
    int reconnectInterval;  // 秒
    int receiveTimeout;     // 秒
    bool autoReconnect;
    
    ClientConfig() 
        : serverIP("127.0.0.1"), serverPort(8888), 
          reconnectInterval(5), receiveTimeout(10), 
          autoReconnect(true) {}
};

// 回调函数类型
using ConnectCallback = std::function<void(bool success)>;
using DisconnectCallback = std::function<void()>;
using StateUpdateCallback = std::function<void(const std::string& stateJson)>;
using PlantDataCallback = std::function<void(const std::string& plantsJson)>;
using LogMessageCallback = std::function<void(const std::string& message)>;
using ErrorCallback = std::function<void(uint32_t errorCode, const std::string& message)>;

class FarmClient {
public:
    FarmClient();
    ~FarmClient();
    
    // 连接控制
    bool connect(const ClientConfig& config);
    void disconnect();
    bool isConnected() const { return m_state == ClientState::CONNECTED; }
    ClientState getState() const { return m_state; }
    
    // 命令发送（同步）
    bool sendConnect(const std::string& clientName);
    bool sendGetState();
    bool sendGetPlants();
    bool sendMoveCart(float targetX, float targetZ, float speed = 1.0f);
    bool sendRotateCart(float targetRotation);
    bool sendPlantSeed(int row, int col, const std::string& seedType);
    bool sendWaterPlant(int row, int col);
    bool sendHarvest(int row, int col);
    bool sendRemoveWeed(int row, int col);
    bool sendAutoFarmStart();
    bool sendAutoFarmStop();
    bool sendAutoFarmStatus();
    bool sendSwitchEquipment(const std::string& equipment);
    bool sendSwitchCamera(const std::string& cameraMode);
    
    // 设置回调函数
    void setConnectCallback(ConnectCallback callback) { m_connectCallback = callback; }
    void setDisconnectCallback(DisconnectCallback callback) { m_disconnectCallback = callback; }
    void setStateUpdateCallback(StateUpdateCallback callback) { m_stateUpdateCallback = callback; }
    void setPlantDataCallback(PlantDataCallback callback) { m_plantDataCallback = callback; }
    void setLogMessageCallback(LogMessageCallback callback) { m_logMessageCallback = callback; }
    void setErrorCallback(ErrorCallback callback) { m_errorCallback = callback; }
    
    // 获取最后的错误信息
    std::string getLastError() const { return m_lastError; }
    
private:
    SOCKET m_socket;
    ClientConfig m_config;
    ClientState m_state;
    std::string m_lastError;
    
    // 线程管理
    std::thread m_receiveThread;
    std::thread m_reconnectThread;
    bool m_shouldStop;
    mutable std::mutex m_socketMutex;
    
    // 回调函数
    ConnectCallback m_connectCallback;
    DisconnectCallback m_disconnectCallback;
    StateUpdateCallback m_stateUpdateCallback;
    PlantDataCallback m_plantDataCallback;
    LogMessageCallback m_logMessageCallback;
    ErrorCallback m_errorCallback;
    
    // 内部方法
    bool connectInternal();
    void receiveLoop();
    void reconnectLoop();
    
    bool sendPacket(const Packet& packet);
    bool receivePacket(Packet& packet);
    
    void handleResponse(const Packet& packet);
    void handleSuccess(const std::string& data);
    void handleError(const std::string& data);
    void handleStateUpdate(const std::string& data);
    void handlePlantData(const std::string& data);
    void handleLogMessage(const std::string& data);
    
    void setError(const std::string& error);
    void cleanup();
    
    // 禁止拷贝
    FarmClient(const FarmClient&) = delete;
    FarmClient& operator=(const FarmClient&) = delete;
};

#endif // FARM_CLIENT_H
