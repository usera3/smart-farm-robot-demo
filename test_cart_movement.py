#!/usr/bin/env python3
"""
测试小车移动接口 - 观察网页上的小车动画
"""
import requests
import time
import math

SERVER_URL = "http://localhost:7070"

def move_cart(x, z, rotation=0.0, speed=0.0):
    """更新小车位置"""
    response = requests.post(
        f"{SERVER_URL}/api/cart/update",
        json={
            'x': x,
            'z': z,
            'rotation': rotation,
            'speed': speed
        },
        timeout=2.0
    )
    
    if response.status_code == 200:
        print(f"✅ 小车位置已更新: x={x:.2f}, z={z:.2f}, rotation={rotation:.1f}°, speed={speed:.1f}")
        return True
    else:
        print(f"❌ 更新失败: {response.status_code}")
        return False

def test_simple_movement():
    """测试1: 简单移动"""
    print("\n" + "="*60)
    print("测试1: 简单移动 - 小车从原点移动到 (2, 2)")
    print("="*60)
    
    # 回到原点
    print("\n1. 回到原点 (0, 0)")
    move_cart(0.0, 0.0, 0.0, 0.0)
    time.sleep(1)
    
    # 移动到目标位置
    print("\n2. 移动到 (2, 2)")
    move_cart(2.0, 2.0, 0.0, 3.0)
    time.sleep(2)
    
    # 停止
    print("\n3. 停止")
    move_cart(2.0, 2.0, 0.0, 0.0)

def test_smooth_movement():
    """测试2: 平滑移动动画"""
    print("\n" + "="*60)
    print("测试2: 平滑移动 - 小车沿直线平滑移动")
    print("="*60)
    
    # 起点和终点
    start_x, start_z = 0.0, 0.0
    end_x, end_z = 3.0, 0.0
    
    # 移动步数
    steps = 30
    speed = 2.0
    
    print(f"\n从 ({start_x}, {start_z}) 平滑移动到 ({end_x}, {end_z})")
    print("请观察网页上的小车动画...")
    
    for i in range(steps + 1):
        t = i / steps
        current_x = start_x + (end_x - start_x) * t
        current_z = start_z + (end_z - start_z) * t
        
        move_cart(current_x, current_z, 0.0, speed if i < steps else 0.0)
        time.sleep(0.1)  # 100ms 间隔
    
    print("\n✅ 移动完成！")

def test_circular_movement():
    """测试3: 圆周运动"""
    print("\n" + "="*60)
    print("测试3: 圆周运动 - 小车绕圆圈移动")
    print("="*60)
    
    radius = 1.5
    center_x, center_z = 0.0, 0.0
    steps = 60
    speed = 3.0
    
    print(f"\n小车绕圆心 ({center_x}, {center_z}) 旋转，半径={radius}")
    print("请观察网页上的小车动画...")
    
    for i in range(steps + 1):
        angle = (i / steps) * 2 * math.pi  # 0 到 2π
        
        x = center_x + radius * math.cos(angle)
        z = center_z + radius * math.sin(angle)
        rotation = math.degrees(angle + math.pi / 2)  # 切线方向
        
        move_cart(x, z, rotation, speed)
        time.sleep(0.05)  # 50ms 间隔
    
    print("\n✅ 圆周运动完成！")

def test_square_path():
    """测试4: 正方形路径"""
    print("\n" + "="*60)
    print("测试4: 正方形路径 - 小车沿正方形边缘移动")
    print("="*60)
    
    # 正方形的四个顶点
    waypoints = [
        (1.0, 1.0, 0.0),    # 右下
        (1.0, -1.0, 90.0),  # 右上
        (-1.0, -1.0, 180.0), # 左上
        (-1.0, 1.0, 270.0),  # 左下
        (1.0, 1.0, 0.0)      # 回到起点
    ]
    
    steps_per_edge = 20
    speed = 2.0
    
    print("\n小车沿正方形路径移动...")
    
    for i in range(len(waypoints) - 1):
        start_x, start_z, start_rot = waypoints[i]
        end_x, end_z, end_rot = waypoints[i + 1]
        
        print(f"\n边 {i+1}: ({start_x:.1f}, {start_z:.1f}) -> ({end_x:.1f}, {end_z:.1f})")
        
        for step in range(steps_per_edge + 1):
            t = step / steps_per_edge
            x = start_x + (end_x - start_x) * t
            z = start_z + (end_z - start_z) * t
            rotation = start_rot
            
            move_cart(x, z, rotation, speed if step < steps_per_edge else 0.0)
            time.sleep(0.05)
    
    print("\n✅ 正方形路径完成！")

def test_visit_plants():
    """测试5: 访问植物位置"""
    print("\n" + "="*60)
    print("测试5: 访问植物 - 小车移动到几个植物位置")
    print("="*60)
    
    # 植物位置（根据8x8网格计算）
    # cell_size = 0.5, offset_x = -2.0, offset_z = -2.0
    plant_positions = [
        (0, 0),  # plant_0_0: (-1.75, -1.75)
        (2, 3),  # plant_2_3: (-0.25, -0.75)
        (4, 4),  # plant_4_4: (0.25, 0.25)
        (7, 7),  # plant_7_7: (1.75, 1.75)
    ]
    
    def calc_pos(row, col):
        """计算植物在世界坐标的位置"""
        cell_size = 0.5
        offset_x = -2.0
        offset_z = -2.0
        x = offset_x + col * cell_size + cell_size / 2
        z = offset_z + row * cell_size + cell_size / 2
        return x, z
    
    print("\n小车访问植物位置...")
    
    current_x, current_z = 0.0, 0.0
    
    for row, col in plant_positions:
        target_x, target_z = calc_pos(row, col)
        plant_id = f"plant_{row}_{col}"
        
        print(f"\n前往 {plant_id} 位置: ({target_x:.2f}, {target_z:.2f})")
        
        # 计算角度
        dx = target_x - current_x
        dz = target_z - current_z
        rotation = math.degrees(math.atan2(dz, dx))
        
        # 平滑移动
        steps = 20
        for i in range(steps + 1):
            t = i / steps
            x = current_x + (target_x - current_x) * t
            z = current_z + (target_z - current_z) * t
            
            move_cart(x, z, rotation, 3.0 if i < steps else 0.0)
            time.sleep(0.05)
        
        # 停留一下
        time.sleep(0.5)
        
        current_x, current_z = target_x, target_z
    
    print("\n✅ 植物访问完成！")
    
    # 返回原点
    print("\n返回原点...")
    steps = 20
    for i in range(steps + 1):
        t = i / steps
        x = current_x * (1 - t)
        z = current_z * (1 - t)
        move_cart(x, z, 0.0, 2.0 if i < steps else 0.0)
        time.sleep(0.05)

def main():
    """主菜单"""
    print("\n" + "="*60)
    print("🚗 智能农场 - 小车移动测试")
    print("="*60)
    print("\n请确保:")
    print("1. 游戏服务器正在运行 (python server_game.py)")
    print("2. 浏览器已打开游戏页面 (http://localhost:7070)")
    print("\n" + "="*60)
    
    while True:
        print("\n请选择测试:")
        print("1. 简单移动测试")
        print("2. 平滑移动动画")
        print("3. 圆周运动")
        print("4. 正方形路径")
        print("5. 访问植物位置")
        print("0. 退出")
        
        choice = input("\n请输入选项 (0-5): ").strip()
        
        if choice == '0':
            print("\n👋 退出测试")
            break
        elif choice == '1':
            test_simple_movement()
        elif choice == '2':
            test_smooth_movement()
        elif choice == '3':
            test_circular_movement()
        elif choice == '4':
            test_square_path()
        elif choice == '5':
            test_visit_plants()
        else:
            print("\n❌ 无效选项，请重新选择")
        
        print("\n" + "─"*60)
        input("按 Enter 继续...")

if __name__ == "__main__":
    main()







