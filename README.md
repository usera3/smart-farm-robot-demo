# 🤖 Smart Farm Robot Demo

智能农场机器人演示项目 - 基于 Flask + WebSocket + Three.js 的自动化农业模拟系统

## 📋 项目简介

这是一个智能农场机器人控制系统，支持：
- 🚜 小车自动导航和路径规划
- 🌱 植物生长模拟和管理
- 🤖 全自动农场操作（播种、浇水、除草、收获）
- 🎮 3D 可视化界面（Three.js）
- 📡 实时通信（WebSocket）

## 🚀 快速开始

### 环境要求

- Python 3.8+
- macOS / Linux / Windows

### 安装依赖

```bash
pip install -r requirements.txt
```

### 启动服务器

```bash
python server_game.py
```

服务器将在 `http://localhost:7070` 启动

### 访问游戏界面

在浏览器中打开：
```
http://localhost:7070
```

## 🎮 操作说明

### 键盘控制

- **WASD** - 小车移动
- **QE** - 小车旋转
- **1-6** - 切换装备（激光、扫描仪、收获器、播种器、浇水器、农药喷雾器）
- **F1-F4** - 切换相机视角
- **空格** - 执行当前装备操作

### 自动化模式

点击界面上的"启动自动化"按钮，系统将自动：
1. 扫描农田状态
2. 规划最优路径
3. 执行农业任务（除草、收获、浇水、播种）
4. 实时显示进度和统计

## 📁 项目文件结构

```
smart-farm-robot-demo/
├── server_game.py              # 🚀 主服务器入口（Flask + SocketIO）
├── requirements.txt            # Python 依赖包
│
├── 核心模块/
│   ├── auto_farm_controller.py # 自动化农场控制器
│   ├── auto_task_executor.py   # 任务执行器
│   ├── path_planner.py         # A* 路径规划算法
│   ├── plant_manager.py        # 植物生长管理
│   ├── resource_manager.py     # 资源（能量/金币）管理
│   ├── state_monitor.py        # 状态监控系统
│   └── cart_movement_api.py    # 小车移动 API
│
├── templates/                  # 前端页面
│   ├── game.html              # 3D 游戏主界面（Three.js）
│   ├── test_websocket.html    # WebSocket 测试页面
│   └── test_step1.html        # 基础测试页面
│
├── winsock_server/            # C++ Winsock 服务器（可选）
│   ├── FarmServer.h/cpp       # 服务器实现
│   ├── protocol.h/cpp         # 通信协议
│   ├── main.cpp               # 入口
│   └── CMakeLists.txt         # 构建配置
│
├── winsock_client/            # C++ 客户端头文件
│   └── FarmClient.h
│
└── 文档/
    ├── README.md              # 本文件
    ├── PROJECT_SUMMARY.md     # 项目详细总结
    ├── PROJECT_STRUCTURE.md   # 架构说明
    ├── API_DOCUMENTATION.md   # API 接口文档
    ├── QUICK_START.md         # 快速开始
    ├── BUILD_ON_MACOS.md      # macOS 构建指南
    ├── CROSS_PLATFORM_SOLUTION.md  # 跨平台方案
    ├── GREEDY_HARVEST_FEATURE.md   # 贪心算法说明
    ├── PACKAGING_GUIDE.md     # 打包指南
    └── WINSOCK_PROTOCOL.md    # Winsock 协议

## 🔧 技术栈

### 后端
- **Flask** - Web 框架
- **Flask-SocketIO** - WebSocket 实时通信
- **Python 3** - 开发语言

### 前端
- **Three.js** - 3D 渲染引擎
- **Socket.IO** - WebSocket 客户端
- **原生 JavaScript** - 游戏逻辑

### 算法
- **A* 算法** - 路径规划
- **贪心算法** - 任务优化
- **优先队列** - 任务调度

## 🌟 核心特性

### 1. 自动化农场系统
- 智能任务调度（优先级队列）
- 贪心最近邻收获算法
- 自动路径规划
- 实时状态监控

### 2. 植物管理
- 多种植物类型（小麦、玉米、胡萝卜、番茄）
- 生长阶段模拟
- 健康度系统
- 杂草扩散机制

### 3. 资源管理
- 能量系统（自动恢复）
- 金币和种子库存
- 工具耐久度
- 成本计算

### 4. 3D 可视化
- 第一人称/第三人称/俯视视角
- 实时渲染
- 平滑动画
- 交互式操作

## 📊 API 接口

### 游戏状态
- `GET /api/game/state` - 获取游戏状态
- `POST /api/game/init` - 初始化游戏

### 小车控制
- `POST /api/cart/update` - 更新小车位置
- `POST /api/cart/move_to` - 移动到指定坐标
- `POST /api/cart/move_to_plant` - 移动到植物位置

### 农场操作
- `POST /api/action/laser` - 激光除草
- `POST /api/action/scan` - 扫描植物
- `POST /api/action/harvest` - 收获植物
- `POST /api/action/plant` - 播种
- `POST /api/action/water` - 浇水

### 自动化控制
- `POST /api/auto_farm/toggle` - 切换自动化模式
- `GET /api/auto_farm/status` - 获取自动化状态

详细 API 文档请查看 `API_DOCUMENTATION.md`

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 👤 作者

usera3

---

**享受智能农场的乐趣！** 🌾🚜🤖
