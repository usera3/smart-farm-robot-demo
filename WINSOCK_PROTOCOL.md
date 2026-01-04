# Winsock远程控制系统 - 通信协议设计

## 项目概述
将智能农场机器人系统改造为基于Winsock的客户端-服务器远程控制系统。

## 系统架构

```
┌─────────────────────┐         Winsock TCP         ┌─────────────────────┐
│   服务器端 (C++)    │ ◄─────────────────────────► │   客户端 (C++)      │
│                     │                              │                     │
│ - Winsock服务器     │                              │ - Winsock客户端     │
│ - MFC/Qt图形界面    │                              │ - 图形控制界面      │
│ - Python业务逻辑    │                              │ - 命令发送          │
│ - 设备状态管理      │                              │ - 状态显示          │
└─────────────────────┘                              └─────────────────────┘
         │
         ▼
┌─────────────────────┐
│  Python后端模块     │
│                     │
│ - 植物管理          │
│ - 路径规划          │
│ - 自动化控制        │
│ - 资源管理          │
└─────────────────────┘
```

## 通信协议设计

### 1. 数据包格式

所有数据包采用统一格式：

```
┌────────────┬────────────┬────────────┬────────────────────┐
│   Header   │  Command   │   Length   │       Data         │
│  (4 bytes) │  (4 bytes) │  (4 bytes) │   (variable)       │
└────────────┴────────────┴────────────┴────────────────────┘
```

- **Header**: 固定魔数 `0x46415246` ("FARM")
- **Command**: 命令类型代码
- **Length**: 数据部分长度
- **Data**: JSON格式的数据内容

### 2. 命令类型定义

#### 客户端 → 服务器命令

| 命令代码 | 命令名称 | 功能说明 |
|---------|---------|---------|
| 0x0001 | CMD_CONNECT | 客户端连接请求 |
| 0x0002 | CMD_DISCONNECT | 客户端断开连接 |
| 0x0010 | CMD_GET_STATE | 获取系统状态 |
| 0x0011 | CMD_GET_PLANTS | 获取植物信息 |
| 0x0020 | CMD_MOVE_CART | 移动小车 |
| 0x0021 | CMD_ROTATE_CART | 旋转小车 |
| 0x0030 | CMD_PLANT_SEED | 播种 |
| 0x0031 | CMD_WATER_PLANT | 浇水 |
| 0x0032 | CMD_HARVEST | 收获 |
| 0x0033 | CMD_REMOVE_WEED | 除草（激光） |
| 0x0040 | CMD_AUTO_FARM_START | 启动自动化 |
| 0x0041 | CMD_AUTO_FARM_STOP | 停止自动化 |
| 0x0042 | CMD_AUTO_FARM_STATUS | 获取自动化状态 |
| 0x0050 | CMD_SWITCH_EQUIPMENT | 切换装备 |
| 0x0051 | CMD_SWITCH_CAMERA | 切换相机模式 |

#### 服务器 → 客户端响应

| 响应代码 | 响应名称 | 功能说明 |
|---------|---------|---------|
| 0x1001 | RESP_SUCCESS | 操作成功 |
| 0x1002 | RESP_ERROR | 操作失败 |
| 0x1010 | RESP_STATE_UPDATE | 状态更新推送 |
| 0x1011 | RESP_PLANT_DATA | 植物数据 |
| 0x1020 | RESP_CART_MOVED | 小车移动完成 |
| 0x1030 | RESP_ACTION_COMPLETE | 操作完成 |
| 0x1040 | RESP_AUTO_STATUS | 自动化状态 |
| 0x1050 | RESP_LOG_MESSAGE | 日志消息 |

### 3. 数据结构定义

#### 3.1 系统状态 (CMD_GET_STATE)

```json
{
  "cart": {
    "x": 0.0,
    "z": 0.0,
    "rotation": 0.0,
    "speed": 0.0
  },
  "energy": 100,
  "coins": 100,
  "score": 0,
  "current_equipment": "laser",
  "camera_mode": "third_person",
  "timestamp": 1234567890
}
```

#### 3.2 植物信息 (CMD_GET_PLANTS)

```json
{
  "plants": [
    {
      "id": "plant_0_0",
      "row": 0,
      "col": 0,
      "type": "wheat",
      "growth_stage": 2,
      "health": 85,
      "water_level": 60,
      "is_weed": false,
      "is_empty": false
    }
  ]
}
```

#### 3.3 移动命令 (CMD_MOVE_CART)

```json
{
  "target_x": 1.5,
  "target_z": -2.0,
  "speed": 1.0
}
```

#### 3.4 操作命令 (CMD_PLANT_SEED, CMD_WATER_PLANT等)

```json
{
  "plant_id": "plant_3_4",
  "row": 3,
  "col": 4,
  "seed_type": "wheat"  // 仅播种需要
}
```

#### 3.5 自动化状态 (RESP_AUTO_STATUS)

```json
{
  "enabled": true,
  "current_task": {
    "type": "harvest",
    "target": "plant_5_6",
    "priority": "high"
  },
  "stats": {
    "tasks_completed": 45,
    "weeds_removed": 12,
    "plants_harvested": 8,
    "plants_watered": 15
  }
}
```

### 4. 通信流程

#### 4.1 连接建立

```
Client                          Server
  │                               │
  ├─── TCP Connect ──────────────►│
  │                               │
  ├─── CMD_CONNECT ──────────────►│
  │                               │
  │◄──── RESP_SUCCESS ────────────┤
  │     (client_id assigned)      │
```

#### 4.2 状态查询

```
Client                          Server
  │                               │
  ├─── CMD_GET_STATE ────────────►│
  │                               │
  │◄──── RESP_STATE_UPDATE ───────┤
  │     (complete state data)     │
```

#### 4.3 设备控制

```
Client                          Server
  │                               │
  ├─── CMD_MOVE_CART ────────────►│
  │     (target position)         │
  │                               │
  │◄──── RESP_SUCCESS ────────────┤
  │                               │
  │◄──── RESP_CART_MOVED ─────────┤ (异步通知)
  │     (movement complete)       │
```

#### 4.4 自动化控制

```
Client                          Server
  │                               │
  ├─── CMD_AUTO_FARM_START ──────►│
  │                               │
  │◄──── RESP_SUCCESS ────────────┤
  │                               │
  │◄──── RESP_AUTO_STATUS ────────┤ (周期性推送)
  │◄──── RESP_AUTO_STATUS ────────┤
  │◄──── RESP_AUTO_STATUS ────────┤
```

### 5. 错误处理

#### 错误代码定义

| 错误代码 | 错误名称 | 说明 |
|---------|---------|------|
| 0xE001 | ERR_INVALID_COMMAND | 无效命令 |
| 0xE002 | ERR_INVALID_DATA | 数据格式错误 |
| 0xE003 | ERR_NOT_AUTHORIZED | 未授权 |
| 0xE004 | ERR_RESOURCE_BUSY | 资源忙 |
| 0xE005 | ERR_INSUFFICIENT_ENERGY | 能量不足 |
| 0xE006 | ERR_INSUFFICIENT_COINS | 金币不足 |
| 0xE007 | ERR_INVALID_POSITION | 无效位置 |
| 0xE008 | ERR_PLANT_NOT_FOUND | 植物不存在 |
| 0xE009 | ERR_OPERATION_FAILED | 操作失败 |

#### 错误响应格式

```json
{
  "error_code": 0xE005,
  "error_message": "Insufficient energy to perform action",
  "details": {
    "required": 10,
    "available": 5
  }
}
```

### 6. 性能要求

- **连接数**: 支持最多10个并发客户端
- **响应时间**: 命令响应 < 100ms
- **状态更新频率**: 30Hz (每33ms)
- **心跳间隔**: 5秒
- **超时时间**: 30秒无活动自动断开

### 7. 安全考虑

1. **连接验证**: 客户端连接时需要验证
2. **命令权限**: 某些命令需要管理员权限
3. **数据校验**: 所有输入数据进行边界检查
4. **日志记录**: 记录所有操作到日志文件

## 实现要点

### 服务器端
- 使用多线程处理多客户端连接
- 主线程处理GUI更新
- 工作线程处理网络通信
- 使用Python C API调用业务逻辑

### 客户端
- 异步通信避免界面卡顿
- 定时器定期请求状态更新
- 命令队列管理
- 断线重连机制

## 开发工具

- **IDE**: Visual Studio 2019/2022
- **GUI框架**: MFC (推荐) 或 Qt
- **Python集成**: Python C API
- **JSON库**: nlohmann/json (C++)
- **网络库**: Winsock2

## 测试计划

1. **单元测试**: 测试各个命令的收发
2. **压力测试**: 多客户端并发连接
3. **稳定性测试**: 长时间运行测试
4. **异常测试**: 网络中断、数据错误等
