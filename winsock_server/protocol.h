#ifndef PROTOCOL_H
#define PROTOCOL_H

#include <cstdint>
#include <string>

// 协议魔数
#define PROTOCOL_MAGIC 0x46415246  // "FARM"

// 最大数据包大小
#define MAX_PACKET_SIZE 65536

// 命令类型定义 - 客户端到服务器
namespace Command {
    constexpr uint32_t CONNECT              = 0x0001;
    constexpr uint32_t DISCONNECT           = 0x0002;
    constexpr uint32_t GET_STATE            = 0x0010;
    constexpr uint32_t GET_PLANTS           = 0x0011;
    constexpr uint32_t MOVE_CART            = 0x0020;
    constexpr uint32_t ROTATE_CART          = 0x0021;
    constexpr uint32_t PLANT_SEED           = 0x0030;
    constexpr uint32_t WATER_PLANT          = 0x0031;
    constexpr uint32_t HARVEST              = 0x0032;
    constexpr uint32_t REMOVE_WEED          = 0x0033;
    constexpr uint32_t AUTO_FARM_START      = 0x0040;
    constexpr uint32_t AUTO_FARM_STOP       = 0x0041;
    constexpr uint32_t AUTO_FARM_STATUS     = 0x0042;
    constexpr uint32_t SWITCH_EQUIPMENT     = 0x0050;
    constexpr uint32_t SWITCH_CAMERA        = 0x0051;
}

// 响应类型定义 - 服务器到客户端
namespace Response {
    constexpr uint32_t SUCCESS              = 0x1001;
    constexpr uint32_t ERROR                = 0x1002;
    constexpr uint32_t STATE_UPDATE         = 0x1010;
    constexpr uint32_t PLANT_DATA           = 0x1011;
    constexpr uint32_t CART_MOVED           = 0x1020;
    constexpr uint32_t ACTION_COMPLETE      = 0x1030;
    constexpr uint32_t AUTO_STATUS          = 0x1040;
    constexpr uint32_t LOG_MESSAGE          = 0x1050;
}

// 错误代码定义
namespace ErrorCode {
    constexpr uint32_t INVALID_COMMAND      = 0xE001;
    constexpr uint32_t INVALID_DATA         = 0xE002;
    constexpr uint32_t NOT_AUTHORIZED       = 0xE003;
    constexpr uint32_t RESOURCE_BUSY        = 0xE004;
    constexpr uint32_t INSUFFICIENT_ENERGY  = 0xE005;
    constexpr uint32_t INSUFFICIENT_COINS   = 0xE006;
    constexpr uint32_t INVALID_POSITION     = 0xE007;
    constexpr uint32_t PLANT_NOT_FOUND      = 0xE008;
    constexpr uint32_t OPERATION_FAILED     = 0xE009;
}

// 数据包头结构
#pragma pack(push, 1)
struct PacketHeader {
    uint32_t magic;      // 魔数 0x46415246
    uint32_t command;    // 命令类型
    uint32_t length;     // 数据长度
    
    PacketHeader() : magic(PROTOCOL_MAGIC), command(0), length(0) {}
    PacketHeader(uint32_t cmd, uint32_t len) 
        : magic(PROTOCOL_MAGIC), command(cmd), length(len) {}
};
#pragma pack(pop)

// 数据包结构
struct Packet {
    PacketHeader header;
    std::string data;  // JSON格式数据
    
    Packet() {}
    Packet(uint32_t command, const std::string& jsonData) 
        : header(command, static_cast<uint32_t>(jsonData.length())), data(jsonData) {}
    
    // 序列化为字节流
    std::string serialize() const;
    
    // 从字节流反序列化
    static bool deserialize(const char* buffer, size_t bufferSize, Packet& packet);
    
    // 验证数据包
    bool isValid() const {
        return header.magic == PROTOCOL_MAGIC && 
               header.length <= MAX_PACKET_SIZE;
    }
};

// 客户端信息
struct ClientInfo {
    int clientId;
    std::string ipAddress;
    uint16_t port;
    time_t connectTime;
    time_t lastActivityTime;
    bool isAuthorized;
    
    ClientInfo() : clientId(-1), port(0), connectTime(0), 
                   lastActivityTime(0), isAuthorized(false) {}
};

// 装备类型
enum class EquipmentType {
    LASER,
    SCANNER,
    WATER_SPRAYER,
    SEED_PLANTER,
    HARVESTER,
    PESTICIDE_SPRAYER
};

// 相机模式
enum class CameraMode {
    THIRD_PERSON,
    FIRST_PERSON,
    TOP_DOWN,
    FREE
};

// 任务类型
enum class TaskType {
    WEED_REMOVAL,
    HARVEST,
    WATERING,
    FERTILIZING,
    PLANTING,
    SOIL_PREPARATION
};

// 任务优先级
enum class TaskPriority {
    CRITICAL = 0,
    HIGH = 1,
    MEDIUM = 2,
    LOW = 3
};

// 辅助函数
std::string equipmentTypeToString(EquipmentType type);
std::string cameraModeToString(CameraMode mode);
std::string taskTypeToString(TaskType type);
std::string taskPriorityToString(TaskPriority priority);

EquipmentType stringToEquipmentType(const std::string& str);
CameraMode stringToCameraMode(const std::string& str);

#endif // PROTOCOL_H
