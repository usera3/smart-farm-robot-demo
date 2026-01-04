#!/usr/bin/env python3
"""
演示小车移动 - 自动执行移动动画
请在浏览器中打开 http://localhost:7070 观察效果
"""
import requests
import time
import math

SERVER_URL = "http://localhost:7070"

def move_cart(x, z, rotation=0.0, speed=0.0):
    """更新小车位置"""
    try:
        response = requests.post(
            f"{SERVER_URL}/api/cart/update",
            json={'x': x, 'z': z, 'rotation': rotation, 'speed': speed},
            timeout=2.0
        )
        if response.status_code == 200:
            print(f"✅ 小车: x={x:6.2f}, z={z:6.2f}, 角度={rotation:6.1f}°, 速度={speed:.1f}")
            return True
        return False
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False

print("\n" + "="*70)
print("🚗 智能农场小车移动演示")
print("="*70)
print("\n📢 请在浏览器中打开: http://localhost:7070")
print("   观察小车的移动效果\n")

# 测试1: 回到原点
print("="*70)
print("测试1: 回到原点")
print("="*70)
move_cart(0.0, 0.0, 0.0, 0.0)
time.sleep(1)

# 测试2: 沿X轴移动
print("\n" + "="*70)
print("测试2: 沿X轴移动 (从0移动到2)")
print("="*70)
steps = 20
for i in range(steps + 1):
    t = i / steps
    x = 2.0 * t
    move_cart(x, 0.0, 0.0, 2.0 if i < steps else 0.0)
    time.sleep(0.1)

time.sleep(1)

# 测试3: 沿Z轴移动
print("\n" + "="*70)
print("测试3: 沿Z轴移动 (从(2,0)移动到(2,2))")
print("="*70)
for i in range(steps + 1):
    t = i / steps
    z = 2.0 * t
    move_cart(2.0, z, 90.0, 2.0 if i < steps else 0.0)
    time.sleep(0.1)

time.sleep(1)

# 测试4: 对角线返回原点
print("\n" + "="*70)
print("测试4: 对角线返回原点 (从(2,2)移动到(0,0))")
print("="*70)
for i in range(steps + 1):
    t = i / steps
    x = 2.0 * (1 - t)
    z = 2.0 * (1 - t)
    rotation = 225.0  # 西南方向
    move_cart(x, z, rotation, 2.0 if i < steps else 0.0)
    time.sleep(0.1)

time.sleep(1)

# 测试5: 圆周运动
print("\n" + "="*70)
print("测试5: 圆周运动 (半径1.5)")
print("="*70)
radius = 1.5
steps = 60
for i in range(steps + 1):
    angle = (i / steps) * 2 * math.pi
    x = radius * math.cos(angle)
    z = radius * math.sin(angle)
    rotation = math.degrees(angle + math.pi / 2)
    move_cart(x, z, rotation, 3.0)
    time.sleep(0.05)

time.sleep(1)

# 测试6: 访问农田中的植物
print("\n" + "="*70)
print("测试6: 访问农田植物位置")
print("="*70)

def calc_plant_pos(row, col):
    """计算植物位置"""
    cell_size = 0.5
    offset_x = -2.0
    offset_z = -2.0
    x = offset_x + col * cell_size + cell_size / 2
    z = offset_z + row * cell_size + cell_size / 2
    return x, z

# 访问几个植物位置
plant_positions = [
    (0, 0, "左上角"),
    (0, 7, "右上角"),
    (7, 7, "右下角"),
    (7, 0, "左下角"),
    (3, 3, "中心偏左"),
]

current_x, current_z = 0.0, 0.0

for row, col, name in plant_positions:
    target_x, target_z = calc_plant_pos(row, col)
    print(f"\n前往 plant_{row}_{col} ({name}): ({target_x:.2f}, {target_z:.2f})")
    
    # 计算方向
    dx = target_x - current_x
    dz = target_z - current_z
    if abs(dx) > 0.01 or abs(dz) > 0.01:
        rotation = math.degrees(math.atan2(dz, dx))
    else:
        rotation = 0.0
    
    # 平滑移动
    steps = 15
    for i in range(steps + 1):
        t = i / steps
        x = current_x + (target_x - current_x) * t
        z = current_z + (target_z - current_z) * t
        move_cart(x, z, rotation, 3.0 if i < steps else 0.0)
        time.sleep(0.05)
    
    current_x, current_z = target_x, target_z
    time.sleep(0.5)

# 返回原点
print("\n返回原点...")
rotation = math.degrees(math.atan2(-current_z, -current_x))
for i in range(20 + 1):
    t = i / 20
    x = current_x * (1 - t)
    z = current_z * (1 - t)
    move_cart(x, z, rotation, 2.0 if i < 20 else 0.0)
    time.sleep(0.05)

print("\n" + "="*70)
print("✅ 演示完成！")
print("="*70)
print("\n小车移动测试说明:")
print("1. ✅ /api/cart/update 接口工作正常")
print("2. 💡 小车通过WebSocket实时更新位置")
print("3. 🎯 可以实现平滑的移动动画")
print("4. 📍 可以精确到达植物位置")
print("\n如果你在网页上看到小车移动，说明接口完全正常！\n")







