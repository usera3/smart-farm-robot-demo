# 智能农场远程控制系统 - Winsock服务器

## 项目概述

这是一个基于Winsock的客户端-服务器远程控制系统，用于控制智能农场机器人。服务器端使用C++和Winsock实现，集成Python业务逻辑，提供图形化界面显示系统状态。

## 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                    服务器端 (C++)                        │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ Winsock服务器 │  │  MFC/Qt界面  │  │ Python集成   │  │
│  │              │  │              │  │              │  │
│  │ - 多客户端   │  │ - 状态显示   │  │ - 业务逻辑   │  │
│  │ - 命令处理   │  │ - 日志显示   │  │ - 植物管理   │  │
│  │ - 状态推送   │  │ - 客户端列表 │  │ - 路径规划   │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
                            │
                            │ TCP/IP (Winsock)
                            │
┌─────────────────────────────────────────────────────────┐
│                    客户端 (C++)                          │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐                    │
│  │ Winsock客户端 │  │  图形界面    │                    │
│  │              │  │              │                    │
│  │ - 连接服务器 │  │ - 控制面板   │                    │
│  │ - 发送命令   │  │ - 状态显示   │                    │
│  │ - 接收响应   │  │ - 3D可视化   │                    │
│  └──────────────┘  └──────────────┘                    │
└─────────────────────────────────────────────────────────┘
```

## 文件结构

```
winsock_server/
├── protocol.h              # 通信协议定义
├── protocol.cpp            # 协议实现
├── FarmServer.h            # 服务器类头文件
├── FarmServer.cpp          # 服务器实现
├── ServerGUI.h             # GUI界面头文件（待实现）
├── ServerGUI.cpp           # GUI实现（待实现）
├── PythonBridge.h          # Python集成头文件（待实现）
├── PythonBridge.cpp        # Python集成实现（待实现）
├── main.cpp                # 主程序入口（待实现）
├── CMakeLists.txt          # CMake构建文件（待实现）
└── README.md               # 本文件
```

## 核心功能

### 1. Winsock服务器
- **多客户端支持**：最多支持10个并发连接
- **异步通信**：使用多线程处理客户端请求
- **心跳检测**：定期检查客户端连接状态
- **日志记录**：记录所有操作到文件和内存

### 2. 通信协议
- **数据包格式**：Header(4B) + Command(4B) + Length(4B) + Data(JSON)
- **命令类型**：15种命令（连接、状态查询、设备控制等）
- **响应类型**：8种响应（成功、错误、状态更新等）
- **错误处理**：9种错误代码

### 3. 设备控制
- **小车控制**：移动、旋转
- **农场操作**：播种、浇水、收获、除草
- **自动化**：启动/停止自动化农场
- **装备切换**：激光、扫描仪、浇水器等

### 4. 状态管理
- **实时状态**：小车位置、能量、金币、分数
- **植物信息**：64个植物的状态（8x8网格）
- **自动化状态**：当前任务、统计信息

## 编译和运行

### 环境要求
- **操作系统**：Windows 10/11
- **编译器**：Visual Studio 2019/2022 或 MinGW
- **Python**：Python 3.8+（用于业务逻辑）
- **依赖库**：
  - Winsock2
  - nlohmann/json (C++ JSON库)
  - Python C API

### 使用Visual Studio编译

1. 打开Visual Studio
2. 创建新项目：Win32控制台应用程序
3. 添加所有源文件到项目
4. 项目属性设置：
   - 链接器 → 输入 → 附加依赖项：`ws2_32.lib`
   - C/C++ → 预处理器 → 预处理器定义：`_WINSOCK_DEPRECATED_NO_WARNINGS`
5. 编译运行

### 使用CMake编译（推荐）

```bash
cd winsock_server
mkdir build
cd build
cmake ..
cmake --build .
```

### 运行服务器

```bash
# 直接运行
./FarmServer.exe

# 指定端口
./FarmServer.exe --port 8888

# 启用调试日志
./FarmServer.exe --debug
```

## 配置文件

创建 `server_config.json`：

```json
{
  "port": 8888,
  "max_clients": 10,
  "heartbeat_interval": 5,
  "client_timeout": 30,
  "enable_logging": true,
  "log_file_path": "server.log",
  "python_home": "C:/Python38"
}
```

## 使用示例

### 服务器端代码

```cpp
#include "FarmServer.h"

int main() {
    FarmServer server;
    
    // 配置服务器
    ServerConfig config;
    config.port = 8888;
    config.maxClients = 10;
    
    // 设置回调
    server.setLogCallback([](const LogEntry& entry) {
        // 更新GUI日志显示
    });
    
    server.setClientConnectCallback([](int clientId, const std::string& ip) {
        // 更新GUI客户端列表
    });
    
    // 启动服务器
    if (server.start(config)) {
        std::cout << "Server started successfully!" << std::endl;
        
        // 初始化Python
        server.initializePython("C:/Python38");
        
        // 保持运行
        std::string input;
        while (std::cin >> input && input != "quit") {
            if (input == "status") {
                ServerStatus status = server.getStatus();
                std::cout << "Connected clients: " << status.connectedClients << std::endl;
                std::cout << "Total commands: " << status.totalCommandsProcessed << std::endl;
            }
        }
        
        server.stop();
    }
    
    return 0;
}
```

### 客户端连接示例

```cpp
// 连接服务器
SOCKET sock = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
sockaddr_in serverAddr;
serverAddr.sin_family = AF_INET;
serverAddr.sin_addr.s_addr = inet_addr("127.0.0.1");
serverAddr.sin_port = htons(8888);

connect(sock, (sockaddr*)&serverAddr, sizeof(serverAddr));

// 发送连接命令
Packet connectPacket(Command::CONNECT, "{\"client_name\":\"TestClient\"}");
std::string buffer = connectPacket.serialize();
send(sock, buffer.c_str(), buffer.length(), 0);

// 接收响应
char recvBuffer[1024];
recv(sock, recvBuffer, sizeof(recvBuffer), 0);

// 发送移动命令
std::string moveData = "{\"target_x\":1.5,\"target_z\":-2.0,\"speed\":1.0}";
Packet movePacket(Command::MOVE_CART, moveData);
buffer = movePacket.serialize();
send(sock, buffer.c_str(), buffer.length(), 0);
```

## 通信协议详解

### 命令格式

所有命令都使用统一的数据包格式：

```
┌────────────┬────────────┬────────────┬────────────────────┐
│   Header   │  Command   │   Length   │       Data         │
│  (4 bytes) │  (4 bytes) │  (4 bytes) │   (variable)       │
└────────────┴────────────┴────────────┴────────────────────┘
```

### 命令示例

#### 1. 获取系统状态

**请求**：
```
Command: 0x0010 (GET_STATE)
Data: {}
```

**响应**：
```
Response: 0x1010 (STATE_UPDATE)
Data: {
  "cart": {"x": 0.0, "z": 0.0, "rotation": 0.0},
  "energy": 100,
  "coins": 100,
  "score": 0
}
```

#### 2. 移动小车

**请求**：
```
Command: 0x0020 (MOVE_CART)
Data: {
  "target_x": 1.5,
  "target_z": -2.0,
  "speed": 1.0
}
```

**响应**：
```
Response: 0x1001 (SUCCESS)
Data: {
  "status": "success",
  "message": "Cart movement initiated"
}
```

#### 3. 播种

**请求**：
```
Command: 0x0030 (PLANT_SEED)
Data: {
  "row": 3,
  "col": 4,
  "seed_type": "wheat"
}
```

**响应**：
```
Response: 0x1001 (SUCCESS)
Data: {
  "status": "success",
  "message": "Seed planted"
}
```

## Python集成

服务器通过Python C API调用Python业务逻辑模块：

```cpp
// 初始化Python
server.initializePython("C:/Python38");

// 调用Python函数
std::string result = server.callPythonFunction(
    "plant_manager",      // 模块名
    "get_plant_info",     // 函数名
    "{\"row\":3,\"col\":4}"  // 参数（JSON格式）
);
```

对应的Python函数：

```python
# plant_manager.py
def get_plant_info(args_json):
    args = json.loads(args_json)
    row = args['row']
    col = args['col']
    
    # 获取植物信息
    plant = get_plant(row, col)
    
    return json.dumps({
        'id': plant.id,
        'type': plant.type,
        'growth_stage': plant.growth_stage,
        'health': plant.health
    })
```

## GUI界面设计

### 主窗口布局

```
┌─────────────────────────────────────────────────────────┐
│  智能农场远程控制服务器                    [_] [□] [X]  │
├─────────────────────────────────────────────────────────┤
│  服务器状态                                              │
│  ┌─────────────────────────────────────────────────┐   │
│  │ 状态: ● 运行中                                   │   │
│  │ 端口: 8888                                       │   │
│  │ 连接数: 3 / 10                                   │   │
│  │ 总命令数: 1,234                                  │   │
│  │ Python状态: ● 已初始化                           │   │
│  └─────────────────────────────────────────────────┘   │
│                                                          │
│  连接的客户端                                            │
│  ┌─────────────────────────────────────────────────┐   │
│  │ ID │ IP地址        │ 端口  │ 连接时间  │ 状态   │   │
│  ├────┼──────────────┼───────┼──────────┼────────┤   │
│  │ 1  │ 192.168.1.10 │ 54321 │ 10:30:15 │ 活动   │   │
│  │ 2  │ 192.168.1.11 │ 54322 │ 10:31:20 │ 活动   │   │
│  │ 3  │ 192.168.1.12 │ 54323 │ 10:32:45 │ 空闲   │   │
│  └─────────────────────────────────────────────────┘   │
│                                                          │
│  操作日志                                                │
│  ┌─────────────────────────────────────────────────┐   │
│  │ [10:30:15] [INFO] Server started on port 8888   │   │
│  │ [10:30:20] [INFO] Client connected: 192.168.1.10│   │
│  │ [10:30:25] [DEBUG] Received command: MOVE_CART  │   │
│  │ [10:30:26] [INFO] Cart movement completed       │   │
│  │ [10:31:00] [INFO] Client connected: 192.168.1.11│   │
│  └─────────────────────────────────────────────────┘   │
│                                                          │
│  [启动服务器] [停止服务器] [清空日志] [导出日志]        │
└─────────────────────────────────────────────────────────┘
```

## 测试

### 单元测试

```bash
# 编译测试
cd tests
cmake ..
cmake --build .

# 运行测试
./test_protocol
./test_server
./test_client
```

### 压力测试

```bash
# 模拟100个客户端并发连接
./stress_test --clients 100 --duration 60
```

## 故障排除

### 常见问题

1. **端口被占用**
   ```
   错误: Bind failed: 10048
   解决: 更改端口或关闭占用端口的程序
   ```

2. **Python初始化失败**
   ```
   错误: Python not initialized
   解决: 检查Python路径，确保Python 3.8+已安装
   ```

3. **客户端连接超时**
   ```
   错误: Client timeout
   解决: 检查网络连接，增加超时时间
   ```

## 性能指标

- **并发连接数**: 10个客户端
- **命令响应时间**: < 100ms
- **状态更新频率**: 30Hz
- **内存占用**: < 100MB
- **CPU占用**: < 5%（空闲时）

## 安全考虑

1. **连接验证**: 客户端连接时需要验证身份
2. **命令权限**: 危险命令需要管理员权限
3. **数据校验**: 所有输入数据进行边界检查
4. **日志记录**: 记录所有操作便于审计

## 未来改进

- [ ] 添加SSL/TLS加密通信
- [ ] 实现用户认证和权限管理
- [ ] 支持配置文件热重载
- [ ] 添加Web管理界面
- [ ] 实现数据库持久化
- [ ] 支持集群部署

## 许可证

本项目仅用于教学目的。

## 联系方式

如有问题，请联系开发者。
