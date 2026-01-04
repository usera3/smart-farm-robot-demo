#include "protocol.h"
#include <cstring>
#include <sstream>

// 序列化数据包为字节流
std::string Packet::serialize() const {
    std::string buffer;
    buffer.resize(sizeof(PacketHeader) + data.length());
    
    // 复制头部
    memcpy(&buffer[0], &header, sizeof(PacketHeader));
    
    // 复制数据
    if (!data.empty()) {
        memcpy(&buffer[sizeof(PacketHeader)], data.c_str(), data.length());
    }
    
    return buffer;
}

// 从字节流反序列化数据包
bool Packet::deserialize(const char* buffer, size_t bufferSize, Packet& packet) {
    // 检查缓冲区大小
    if (bufferSize < sizeof(PacketHeader)) {
        return false;
    }
    
    // 读取头部
    memcpy(&packet.header, buffer, sizeof(PacketHeader));
    
    // 验证魔数
    if (packet.header.magic != PROTOCOL_MAGIC) {
        return false;
    }
    
    // 验证数据长度
    if (packet.header.length > MAX_PACKET_SIZE) {
        return false;
    }
    
    // 检查缓冲区是否包含完整数据
    if (bufferSize < sizeof(PacketHeader) + packet.header.length) {
        return false;
    }
    
    // 读取数据
    if (packet.header.length > 0) {
        packet.data.assign(buffer + sizeof(PacketHeader), packet.header.length);
    } else {
        packet.data.clear();
    }
    
    return true;
}

// 装备类型转字符串
std::string equipmentTypeToString(EquipmentType type) {
    switch (type) {
        case EquipmentType::LASER:              return "laser";
        case EquipmentType::SCANNER:            return "scanner";
        case EquipmentType::WATER_SPRAYER:      return "water_sprayer";
        case EquipmentType::SEED_PLANTER:       return "seed_planter";
        case EquipmentType::HARVESTER:          return "harvester";
        case EquipmentType::PESTICIDE_SPRAYER:  return "pesticide_sprayer";
        default:                                return "unknown";
    }
}

// 相机模式转字符串
std::string cameraModeToString(CameraMode mode) {
    switch (mode) {
        case CameraMode::THIRD_PERSON:  return "third_person";
        case CameraMode::FIRST_PERSON:  return "first_person";
        case CameraMode::TOP_DOWN:      return "top_down";
        case CameraMode::FREE:          return "free";
        default:                        return "unknown";
    }
}

// 任务类型转字符串
std::string taskTypeToString(TaskType type) {
    switch (type) {
        case TaskType::WEED_REMOVAL:        return "weed_removal";
        case TaskType::HARVEST:             return "harvest";
        case TaskType::WATERING:            return "watering";
        case TaskType::FERTILIZING:         return "fertilizing";
        case TaskType::PLANTING:            return "planting";
        case TaskType::SOIL_PREPARATION:    return "soil_preparation";
        default:                            return "unknown";
    }
}

// 任务优先级转字符串
std::string taskPriorityToString(TaskPriority priority) {
    switch (priority) {
        case TaskPriority::CRITICAL:    return "critical";
        case TaskPriority::HIGH:        return "high";
        case TaskPriority::MEDIUM:      return "medium";
        case TaskPriority::LOW:         return "low";
        default:                        return "unknown";
    }
}

// 字符串转装备类型
EquipmentType stringToEquipmentType(const std::string& str) {
    if (str == "laser")             return EquipmentType::LASER;
    if (str == "scanner")           return EquipmentType::SCANNER;
    if (str == "water_sprayer")     return EquipmentType::WATER_SPRAYER;
    if (str == "seed_planter")      return EquipmentType::SEED_PLANTER;
    if (str == "harvester")         return EquipmentType::HARVESTER;
    if (str == "pesticide_sprayer") return EquipmentType::PESTICIDE_SPRAYER;
    return EquipmentType::LASER;  // 默认
}

// 字符串转相机模式
CameraMode stringToCameraMode(const std::string& str) {
    if (str == "third_person")  return CameraMode::THIRD_PERSON;
    if (str == "first_person")  return CameraMode::FIRST_PERSON;
    if (str == "top_down")      return CameraMode::TOP_DOWN;
    if (str == "free")          return CameraMode::FREE;
    return CameraMode::THIRD_PERSON;  // 默认
}
