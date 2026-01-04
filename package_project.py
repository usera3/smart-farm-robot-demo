#!/usr/bin/env python3
"""
项目打包脚本 - 打包项目所需的核心代码文件
"""
import os
import shutil
from datetime import datetime
import zipfile

# 定义需要打包的文件
ESSENTIAL_FILES = {
    # 核心Python文件
    'python': [
        'server_game.py',
        'auto_farm_controller.py',
        'auto_task_executor.py',
        'cart_movement_api.py',
        'path_planner.py',
        'plant_manager.py',
        'resource_manager.py',
        'state_monitor.py',
    ],
    # 配置和依赖文件
    'config': [
        'requirements.txt',
        'laser_training_data.json',
    ],
    # 模板文件（HTML）
    'templates': [
        'templates/game.html',
        'templates/test_websocket.html',
    ],
    # 文档文件（可选）
    'docs': [
        'PROJECT_SUMMARY.md',
        'API_VERIFICATION_SUMMARY.md',
        'SMART_FARM_PAPER_CN.md',
    ]
}

# 可选的演示和测试文件
DEMO_FILES = [
    'demo_cart_movement.py',
    'example_auto_farm_with_animation.py',
    'monitor_harvest.py',
]

TEST_FILES = [
    'test_all_apis.py',
    'test_cart_movement.py',
    'test_enhanced_cart_apis.py',
]


def create_package(include_docs=True, include_demos=False, include_tests=False, output_format='zip'):
    """
    创建项目包
    
    Args:
        include_docs: 是否包含文档文件
        include_demos: 是否包含演示文件
        include_tests: 是否包含测试文件
        output_format: 输出格式 ('zip' 或 'folder')
    """
    # 获取项目根目录
    project_root = os.path.dirname(os.path.abspath(__file__))
    
    # 创建打包目录名（带时间戳）
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    package_name = f'smart_farm_game_{timestamp}'
    package_dir = os.path.join(project_root, 'dist', package_name)
    
    # 创建目录
    os.makedirs(package_dir, exist_ok=True)
    os.makedirs(os.path.join(package_dir, 'templates'), exist_ok=True)
    
    copied_files = []
    
    print(f"📦 开始打包项目到: {package_dir}")
    print("=" * 60)
    
    # 复制核心Python文件
    print("\n📄 复制核心Python文件...")
    for file in ESSENTIAL_FILES['python']:
        src = os.path.join(project_root, file)
        dst = os.path.join(package_dir, file)
        if os.path.exists(src):
            shutil.copy2(src, dst)
            copied_files.append(file)
            print(f"  ✓ {file}")
        else:
            print(f"  ✗ {file} (未找到)")
    
    # 复制配置文件
    print("\n⚙️  复制配置文件...")
    for file in ESSENTIAL_FILES['config']:
        src = os.path.join(project_root, file)
        dst = os.path.join(package_dir, file)
        if os.path.exists(src):
            shutil.copy2(src, dst)
            copied_files.append(file)
            print(f"  ✓ {file}")
        else:
            print(f"  ✗ {file} (未找到)")
    
    # 复制模板文件
    print("\n🎨 复制模板文件...")
    for file in ESSENTIAL_FILES['templates']:
        src = os.path.join(project_root, file)
        dst = os.path.join(package_dir, file)
        if os.path.exists(src):
            shutil.copy2(src, dst)
            copied_files.append(file)
            print(f"  ✓ {file}")
        else:
            print(f"  ✗ {file} (未找到)")
    
    # 复制文档文件（如果需要）
    if include_docs:
        print("\n📚 复制文档文件...")
        for file in ESSENTIAL_FILES['docs']:
            src = os.path.join(project_root, file)
            dst = os.path.join(package_dir, file)
            if os.path.exists(src):
                shutil.copy2(src, dst)
                copied_files.append(file)
                print(f"  ✓ {file}")
    
    # 复制演示文件（如果需要）
    if include_demos:
        print("\n🎮 复制演示文件...")
        for file in DEMO_FILES:
            src = os.path.join(project_root, file)
            dst = os.path.join(package_dir, file)
            if os.path.exists(src):
                shutil.copy2(src, dst)
                copied_files.append(file)
                print(f"  ✓ {file}")
    
    # 复制测试文件（如果需要）
    if include_tests:
        print("\n🧪 复制测试文件...")
        for file in TEST_FILES:
            src = os.path.join(project_root, file)
            dst = os.path.join(package_dir, file)
            if os.path.exists(src):
                shutil.copy2(src, dst)
                copied_files.append(file)
                print(f"  ✓ {file}")
    
    # 创建README
    print("\n📝 创建部署说明...")
    create_deployment_readme(package_dir)
    
    # 统计信息
    print("\n" + "=" * 60)
    print(f"✅ 打包完成！共复制 {len(copied_files)} 个文件")
    
    # 如果需要ZIP格式
    if output_format == 'zip':
        print("\n📦 创建ZIP压缩包...")
        zip_path = f"{package_dir}.zip"
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(package_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, os.path.dirname(package_dir))
                    zipf.write(file_path, arcname)
        
        # 删除临时文件夹（可选）
        shutil.rmtree(package_dir)
        print(f"✅ ZIP包已创建: {zip_path}")
        return zip_path
    else:
        print(f"✅ 文件夹包已创建: {package_dir}")
        return package_dir


def create_deployment_readme(package_dir):
    """创建部署说明文件"""
    readme_content = """# 智能农场机器人游戏 - 部署说明

## 📋 项目简介

这是一个基于Flask和SocketIO的智能农场机器人仿真游戏。

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 运行服务器

```bash
python server_game.py
```

服务器默认运行在 `http://localhost:5000`

### 3. 访问游戏

打开浏览器访问: `http://localhost:5000`

## 📁 文件结构

```
.
├── server_game.py              # Flask服务器主文件
├── auto_farm_controller.py     # 自动化农场控制器
├── auto_task_executor.py       # 自动任务执行器
├── cart_movement_api.py        # 小车移动API
├── path_planner.py             # 路径规划器
├── plant_manager.py            # 植物管理器
├── resource_manager.py         # 资源管理器
├── state_monitor.py            # 状态监控器
├── requirements.txt            # Python依赖
├── laser_training_data.json    # 激光训练数据
└── templates/
    ├── game.html               # 游戏主界面
    └── test_websocket.html     # WebSocket测试页面
```

## 🎮 游戏功能

- ✅ 小车移动控制
- ✅ 机械臂控制
- ✅ 植物种植与收获
- ✅ 自动化农场系统
- ✅ 路径规划
- ✅ 资源管理
- ✅ 实时状态监控

## 🔧 配置说明

服务器默认配置:
- 主机: 0.0.0.0
- 端口: 5000
- WebSocket支持: 已启用

如需修改配置，请编辑 `server_game.py` 文件末尾的启动参数。

## 📝 API文档

详细API文档请参考 `API_VERIFICATION_SUMMARY.md`

## 🐛 故障排除

### 端口被占用

如果端口5000被占用，可以修改 `server_game.py` 的启动端口:

```python
socketio.run(app, host='0.0.0.0', port=8080, debug=True)
```

### 依赖安装失败

建议使用虚拟环境:

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\\Scripts\\activate  # Windows
pip install -r requirements.txt
```

## 📞 技术支持

如有问题，请查看项目文档或提交Issue。

---
打包时间: """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """
"""
    
    readme_path = os.path.join(package_dir, 'README.md')
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='智能农场游戏项目打包工具')
    parser.add_argument('--docs', action='store_true', help='包含文档文件')
    parser.add_argument('--demos', action='store_true', help='包含演示文件')
    parser.add_argument('--tests', action='store_true', help='包含测试文件')
    parser.add_argument('--format', choices=['zip', 'folder'], default='zip', 
                        help='输出格式 (默认: zip)')
    parser.add_argument('--all', action='store_true', help='包含所有文件（文档+演示+测试）')
    
    args = parser.parse_args()
    
    # 如果指定了--all，则包含所有内容
    if args.all:
        args.docs = True
        args.demos = True
        args.tests = True
    
    # 执行打包
    output_path = create_package(
        include_docs=args.docs,
        include_demos=args.demos,
        include_tests=args.tests,
        output_format=args.format
    )
    
    print(f"\n🎉 打包成功！输出路径: {output_path}")
    print("\n使用说明:")
    print("  python package_project.py              # 仅核心文件，生成ZIP")
    print("  python package_project.py --docs       # 包含文档")
    print("  python package_project.py --all        # 包含所有文件")
    print("  python package_project.py --format folder  # 输出为文件夹")
