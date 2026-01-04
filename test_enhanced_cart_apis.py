#!/usr/bin/env python3
"""
测试增强型小车移动API接口
"""
import requests
import time
import json

SERVER_URL = "http://localhost:7070"

def test_api(name, method, endpoint, data=None):
    """测试API接口"""
    print(f"\n{'='*60}")
    print(f"🧪 测试: {name}")
    print(f"{'='*60}")
    
    try:
        url = f"{SERVER_URL}{endpoint}"
        print(f"📡 {method} {url}")
        
        if data:
            print(f"📤 请求数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
        if method == "GET":
            response = requests.get(url, timeout=5.0)
        else:
            response = requests.post(url, json=data, timeout=5.0)
        
        print(f"📨 状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 成功: {json.dumps(result, indent=2, ensure_ascii=False)}")
            return True, result
        else:
            print(f"❌ 失败: HTTP {response.status_code}")
            print(f"   响应: {response.text}")
            return False, None
            
    except requests.exceptions.Timeout:
        print("❌ 请求超时")
        return False, None
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败 - 请确认服务器正在运行")
        return False, None
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False, None

print("\n" + "="*70)
print("🚀 测试增强型小车移动API接口")
print("="*70)
print("\n📢 请确保:")
print("1. 服务器正在运行: python server_game.py")
print("2. 浏览器已打开: http://localhost:7070")
print("\n" + "="*70)

# 等待用户确认
input("\n按 Enter 开始测试...")

# 测试1: 获取小车当前位置
test_api(
    "获取小车当前位置",
    "GET",
    "/api/cart/position"
)

time.sleep(0.5)

# 测试2: 移动到指定坐标
test_api(
    "移动到指定坐标 (1.5, 1.5)",
    "POST",
    "/api/cart/move_to",
    {
        'target_x': 1.5,
        'target_z': 1.5,
        'speed': 2.0,
        'smooth': True
    }
)

print("\n⏳ 等待小车移动完成...")
time.sleep(3)

# 测试3: 移动到植物位置
test_api(
    "移动到植物位置 plant_3_3",
    "POST",
    "/api/cart/move_to_plant",
    {
        'plant_id': 'plant_3_3',
        'offset': 0.3,
        'speed': 2.5
    }
)

print("\n⏳ 等待小车移动完成...")
time.sleep(3)

# 测试4: 旋转到指定角度
test_api(
    "旋转到90度",
    "POST",
    "/api/cart/rotate_to",
    {
        'target_rotation': 90.0,
        'smooth': True
    }
)

print("\n⏳ 等待旋转完成...")
time.sleep(2)

# 测试5: 停止小车
test_api(
    "停止小车",
    "POST",
    "/api/cart/stop"
)

time.sleep(0.5)

# 测试6: 跟随路径
test_api(
    "跟随路径（正方形）",
    "POST",
    "/api/cart/follow_path",
    {
        'waypoints': [
            {'x': 1.0, 'z': 1.0},
            {'x': 1.0, 'z': -1.0},
            {'x': -1.0, 'z': -1.0},
            {'x': -1.0, 'z': 1.0},
            {'x': 0.0, 'z': 0.0}
        ],
        'speed': 2.0
    }
)

print("\n⏳ 等待路径跟随完成...")
time.sleep(6)

# 测试7: 智能访问所有杂草
test_api(
    "智能访问所有杂草",
    "POST",
    "/api/cart/navigate_all_plants",
    {
        'filter': 'weed',
        'speed': 3.0
    }
)

print("\n⏳ 等待访问完成...")
time.sleep(5)

# 最后：返回原点
print("\n" + "="*60)
print("返回原点")
print("="*60)
test_api(
    "移动回原点",
    "POST",
    "/api/cart/move_to",
    {
        'target_x': 0.0,
        'target_z': 0.0,
        'speed': 2.0,
        'smooth': True
    }
)

print("\n" + "="*70)
print("✅ 所有测试完成！")
print("="*70)
print("\n💡 如果在网页上看到小车移动动画，说明增强型API工作正常！")
print("\n新增的7个API接口:")
print("  1. GET  /api/cart/position - 获取当前位置")
print("  2. POST /api/cart/move_to - 移动到指定坐标")
print("  3. POST /api/cart/move_to_plant - 移动到植物位置")
print("  4. POST /api/cart/rotate_to - 旋转到指定角度")
print("  5. POST /api/cart/stop - 立即停止")
print("  6. POST /api/cart/follow_path - 跟随路径")
print("  7. POST /api/cart/navigate_all_plants - 智能访问植物\n")







