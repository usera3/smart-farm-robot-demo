#!/usr/bin/env python3
"""
自动化农场示例 - 使用增强型API实现小车自动移动动画

这个示例展示如何：
1. 使用增强型API让小车自动移动到植物位置
2. 执行农场操作（浇水、收获等）
3. 实现完整的自动化流程
"""
import requests
import time

SERVER_URL = "http://localhost:7070"

def get_game_state():
    """获取游戏状态"""
    response = requests.get(f"{SERVER_URL}/api/game/state", timeout=3)
    if response.status_code == 200:
        return response.json()['state']
    return None

def move_to_plant(plant_id):
    """使用增强API移动到植物位置"""
    print(f"🚗 移动小车到 {plant_id}...")
    response = requests.post(
        f"{SERVER_URL}/api/cart/move_to_plant",
        json={'plant_id': plant_id, 'offset': 0.3, 'speed': 3.0},
        timeout=3
    )
    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            print(f"   ✅ {result['message']}")
            return True
    print(f"   ❌ 移动失败")
    return False

def water_plant(plant_id):
    """浇水"""
    print(f"💧 浇水 {plant_id}...")
    response = requests.post(
        f"{SERVER_URL}/api/action/water",
        json={'plant_id': plant_id},
        timeout=3
    )
    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            print(f"   ✅ {result['message']}")
            return True
    print(f"   ❌ 浇水失败")
    return False

def harvest_plant(plant_id):
    """收获"""
    print(f"🌾 收获 {plant_id}...")
    response = requests.post(
        f"{SERVER_URL}/api/action/harvest",
        json={'plant_id': plant_id},
        timeout=3
    )
    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            print(f"   ✅ {result['message']}")
            return True
        else:
            print(f"   ⚠️ {result.get('message', '无法收获')}")
    else:
        print(f"   ❌ 收获失败")
    return False

def laser_weed(plant_id):
    """激光除草"""
    print(f"🔥 激光除草 {plant_id}...")
    response = requests.post(
        f"{SERVER_URL}/api/action/laser",
        json={'plant_id': plant_id},
        timeout=3
    )
    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            print(f"   ✅ {result['message']}")
            return True
    print(f"   ❌ 除草失败")
    return False

def auto_water_all_plants():
    """自动化浇水所有植物"""
    print("\n" + "="*70)
    print("🤖 自动化任务: 浇水所有需要浇水的植物")
    print("="*70)
    
    state = get_game_state()
    if not state:
        print("❌ 无法获取游戏状态")
        return
    
    plants = state.get('plants', [])
    watered_count = 0
    
    for plant in plants:
        # 跳过空地和已移除的植物
        if plant.get('is_empty') or plant.get('is_removed'):
            continue
        
        # 检查是否需要浇水（种子或湿度低的植物）
        if plant.get('is_seed') or plant.get('soil_moisture', 100) < 60:
            plant_id = plant['id']
            
            # 移动到植物位置
            if move_to_plant(plant_id):
                time.sleep(2)  # 等待移动完成
                
                # 浇水
                if water_plant(plant_id):
                    watered_count += 1
                    time.sleep(1)  # 操作间隔
    
    print(f"\n✅ 自动浇水完成！共浇水 {watered_count} 株植物")

def auto_harvest_mature_plants():
    """自动化收获所有成熟植物"""
    print("\n" + "="*70)
    print("🤖 自动化任务: 收获所有成熟植物")
    print("="*70)
    
    state = get_game_state()
    if not state:
        print("❌ 无法获取游戏状态")
        return
    
    plants = state.get('plants', [])
    harvested_count = 0
    total_coins = 0
    
    for plant in plants:
        # 只收获成熟的蔬菜
        if (plant.get('is_vegetable') and 
            plant.get('growth_stage', 0) >= 3 and 
            not plant.get('is_removed')):
            
            plant_id = plant['id']
            
            # 移动到植物位置
            if move_to_plant(plant_id):
                time.sleep(2)  # 等待移动完成
                
                # 收获
                response = requests.post(
                    f"{SERVER_URL}/api/action/harvest",
                    json={'plant_id': plant_id},
                    timeout=3
                )
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        coins = result.get('coins_earned', 0)
                        total_coins += coins
                        harvested_count += 1
                        print(f"   ✅ {result['message']}")
                        time.sleep(1)
    
    print(f"\n✅ 自动收获完成！")
    print(f"   收获植物数: {harvested_count}")
    print(f"   获得金币: {total_coins}")

def auto_remove_all_weeds():
    """自动化清除所有杂草"""
    print("\n" + "="*70)
    print("🤖 自动化任务: 清除所有杂草")
    print("="*70)
    
    state = get_game_state()
    if not state:
        print("❌ 无法获取游戏状态")
        return
    
    plants = state.get('plants', [])
    removed_count = 0
    
    for plant in plants:
        # 只清除杂草
        if plant.get('is_weed') and not plant.get('is_removed'):
            plant_id = plant['id']
            
            # 移动到植物位置
            if move_to_plant(plant_id):
                time.sleep(2)  # 等待移动完成
                
                # 激光除草
                if laser_weed(plant_id):
                    removed_count += 1
                    time.sleep(1)
    
    print(f"\n✅ 除草完成！清除了 {removed_count} 株杂草")

def demo_smart_navigation():
    """演示智能导航功能"""
    print("\n" + "="*70)
    print("🤖 演示: 智能访问所有成熟植物")
    print("="*70)
    
    # 使用智能导航API自动规划路径访问所有成熟植物
    response = requests.post(
        f"{SERVER_URL}/api/cart/navigate_all_plants",
        json={'filter': 'mature', 'speed': 3.0},
        timeout=3
    )
    
    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            plant_count = result.get('plant_count', 0)
            print(f"✅ 开始访问 {plant_count} 株成熟植物")
            print("   请在浏览器中观察小车自动移动...")
            
            # 等待访问完成
            time.sleep(plant_count * 2)
            print("✅ 访问完成！")
        else:
            print(f"⚠️ {result.get('message', '没有符合条件的植物')}")
    else:
        print("❌ 智能导航失败")

def main():
    """主菜单"""
    print("\n" + "="*70)
    print("🤖 自动化农场演示 - 使用增强型API")
    print("="*70)
    print("\n请确保:")
    print("1. 服务器正在运行")
    print("2. 浏览器已打开 http://localhost:7070")
    print("\n" + "="*70)
    
    while True:
        print("\n请选择自动化任务:")
        print("1. 自动浇水所有需要浇水的植物")
        print("2. 自动收获所有成熟植物")
        print("3. 自动清除所有杂草")
        print("4. 演示智能导航（访问成熟植物）")
        print("0. 退出")
        
        choice = input("\n请输入选项 (0-4): ").strip()
        
        if choice == '0':
            print("\n👋 退出程序")
            break
        elif choice == '1':
            auto_water_all_plants()
        elif choice == '2':
            auto_harvest_mature_plants()
        elif choice == '3':
            auto_remove_all_weeds()
        elif choice == '4':
            demo_smart_navigation()
        else:
            print("\n❌ 无效选项")
        
        print("\n" + "-"*70)
        input("按 Enter 继续...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 程序被用户中断")
    except Exception as e:
        print(f"\n❌ 错误: {e}")







