# 📦 项目打包指南

## 概述

本指南说明如何使用 `package_project.py` 脚本打包智能农场机器人游戏项目。

## 快速开始

### 基础打包（仅核心文件）

```bash
python3 package_project.py
```

这将创建一个包含所有核心运行文件的ZIP压缩包，输出到 `dist/` 目录。

## 打包选项

### 1. 包含文档

```bash
python3 package_project.py --docs
```

包含以下文档文件：
- `PROJECT_SUMMARY.md` - 项目总结
- `API_VERIFICATION_SUMMARY.md` - API验证文档
- `SMART_FARM_PAPER_CN.md` - 智能农场技术论文

### 2. 包含演示文件

```bash
python3 package_project.py --demos
```

包含演示脚本：
- `demo_cart_movement.py` - 小车移动演示
- `example_auto_farm_with_animation.py` - 自动农场动画示例
- `monitor_harvest.py` - 收获监控工具

### 3. 包含测试文件

```bash
python3 package_project.py --tests
```

包含测试脚本：
- `test_all_apis.py` - 全API测试
- `test_cart_movement.py` - 小车移动测试
- `test_enhanced_cart_apis.py` - 增强小车API测试

### 4. 包含所有内容

```bash
python3 package_project.py --all
```

包含所有文档、演示和测试文件。

### 5. 输出为文件夹（而非ZIP）

```bash
python3 package_project.py --format folder
```

或组合使用：

```bash
python3 package_project.py --all --format folder
```

## 核心文件清单

打包脚本会包含以下核心文件：

### Python核心模块
- ✅ `server_game.py` - Flask服务器主文件
- ✅ `auto_farm_controller.py` - 自动化农场控制器
- ✅ `auto_task_executor.py` - 自动任务执行器
- ✅ `cart_movement_api.py` - 小车移动API
- ✅ `path_planner.py` - 路径规划器
- ✅ `plant_manager.py` - 植物管理器
- ✅ `resource_manager.py` - 资源管理器
- ✅ `state_monitor.py` - 状态监控器

### 配置文件
- ✅ `requirements.txt` - Python依赖列表
- ✅ `laser_training_data.json` - 激光训练数据

### 模板文件
- ✅ `templates/game.html` - 游戏主界面
- ✅ `templates/test_websocket.html` - WebSocket测试页面

### 自动生成文件
- ✅ `README.md` - 部署说明文档（自动生成）

## 输出位置

所有打包文件都会输出到 `dist/` 目录：

```
git_test/
├── dist/
│   ├── smart_farm_game_20251126_163702.zip
│   └── smart_farm_game_20251126_164510.zip
└── ...
```

文件名格式：`smart_farm_game_YYYYMMdd_HHmmss.zip`

## 部署流程

1. **打包项目**
   ```bash
   python3 package_project.py --docs
   ```

2. **解压到目标服务器**
   ```bash
   unzip smart_farm_game_*.zip
   cd smart_farm_game_*
   ```

3. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

4. **运行服务器**
   ```bash
   python3 server_game.py
   ```

5. **访问游戏**
   
   打开浏览器访问 `http://localhost:5000`

## 文件大小

典型打包文件大小：
- 仅核心文件：~150KB（压缩后）
- 包含文档：~200KB（压缩后）
- 包含所有内容：~250KB（压缩后）

## 排除的文件

以下文件/目录不会被打包（已在 `.gitignore` 中定义）：
- `__pycache__/` - Python缓存
- `.venv/` - 虚拟环境
- `.idea/` - IDE配置
- `*.log` - 日志文件
- `*.backup*` - 备份文件
- `dist/` - 打包输出目录（避免递归）

## 常见问题

### Q: 如何修改打包文件列表？

A: 编辑 `package_project.py` 文件中的 `ESSENTIAL_FILES` 字典。

### Q: 打包后的文件能直接运行吗？

A: 是的，只需安装依赖（`pip install -r requirements.txt`）即可运行。

### Q: 如何打包到指定目录？

A: 当前版本打包到 `dist/` 目录。如需修改，请编辑 `package_project.py` 中的 `package_dir` 变量。

### Q: 可以自动上传到服务器吗？

A: 当前脚本只负责打包。您可以使用 `scp` 或其他工具上传ZIP文件：
```bash
scp dist/smart_farm_game_*.zip user@server:/path/to/deploy/
```

## 高级用法

### 仅打包特定文件

编辑 `package_project.py`，自定义 `ESSENTIAL_FILES` 字典：

```python
ESSENTIAL_FILES = {
    'python': [
        'server_game.py',
        # 只添加需要的文件...
    ],
    # ...
}
```

### 创建多个不同的打包配置

复制 `package_project.py` 并创建不同版本：
- `package_minimal.py` - 最小化版本
- `package_full.py` - 完整版本
- `package_demo.py` - 演示版本

## 技术支持

如有问题或建议，请查看项目文档或联系开发团队。

---
最后更新：2025-11-26
