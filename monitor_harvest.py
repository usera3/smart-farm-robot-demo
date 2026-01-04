#!/usr/bin/env python3
"""
收获监控脚本 - 实时监控小车收获情况
"""
import requests
import time
import json
from datetime import datetime

SERVER_URL = "http://localhost:7070"

def get_game_state():
    """获取游戏状态"""
    try:
        response = requests.get(f"{SERVER_URL}/api/game/state", timeout=5)
        if response.status_code == 200:
            return response.json().get('state', {})
    except:
        pass
    return None

def count_harvestable_plants(state):
    """统计可收获的植物数量"""
    if not state:
        return 0, []
    
    plants = state.get('plants', [])
    harvestable = []
    
    for plant in plants:
        # 检查是否可收获
        if (plant.get('is_vegetable', False) and 
            not plant.get('is_removed', False) and 
            not plant.get('removed', False) and
            not plant.get('is_seed', False) and
            plant.get('growth_stage', 0) >= 3 and
            plant.get('health', 0) >= 30):
            harvestable.append({
                'id': plant.get('id'),
                'row': plant.get('row'),
                'col': plant.get('col'),
                'stage': plant.get('growth_stage'),
                'health': plant.get('health')
            })
    
    return len(harvestable), harvestable

def count_plants_by_type(state):
    """统计各类型植物数量"""
    if not state:
        return {}
    
    plants = state.get('plants', [])
    counts = {
        'empty': 0,
        'weeds': 0,
        'growing': 0,
        'mature': 0,
        'total': len(plants)
    }
    
    for plant in plants:
        if plant.get('is_empty', False):
            counts['empty'] += 1
        elif plant.get('is_weed', False) or plant.get('type') == 'weed':
            counts['weeds'] += 1
        elif plant.get('is_vegetable', False):
            if plant.get('growth_stage', 0) >= 3:
                counts['mature'] += 1
            else:
                counts['growing'] += 1
    
    return counts

def get_auto_farm_status():
    """获取自动农场状态"""
    try:
        response = requests.get(f"{SERVER_URL}/api/auto_farm/status", timeout=5)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None

def start_auto_farm():
    """启动自动农场系统"""
    try:
        response = requests.post(f"{SERVER_URL}/api/auto_farm/start", timeout=5)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"❌ 启动失败: {e}")
    return None

def print_separator():
    print("=" * 80)

def main():
    print_separator()
    print("🔍 收获监控系统启动")
    print_separator()
    
    # 等待服务器启动
    print("\n⏳ 等待服务器启动...")
    for i in range(10):
        state = get_game_state()
        if state:
            print("✅ 服务器已就绪")
            break
        time.sleep(1)
    else:
        print("❌ 服务器启动失败")
        return
    
    # 获取初始状态
    print("\n📊 初始状态:")
    state = get_game_state()
    counts = count_plants_by_type(state)
    harvestable_count, harvestable_list = count_harvestable_plants(state)
    
    print(f"  总格子数: {counts['total']}")
    print(f"  空地: {counts['empty']}")
    print(f"  杂草: {counts['weeds']}")
    print(f"  生长中: {counts['growing']}")
    print(f"  成熟植物: {counts['mature']}")
    print(f"  🎯 可收获植物: {harvestable_count}")
    
    if harvestable_list:
        print(f"\n  可收获植物详情:")
        for p in harvestable_list[:5]:
            print(f"    - {p['id']} (行{p['row']},列{p['col']}) 阶段{p['stage']} 健康度{p['health']}")
        if len(harvestable_list) > 5:
            print(f"    ... 还有 {len(harvestable_list) - 5} 个")
    
    # 检查自动农场状态
    auto_status = get_auto_farm_status()
    if auto_status:
        print(f"\n🤖 自动农场状态: {auto_status.get('status', 'unknown')}")
        print(f"  是否启用: {auto_status.get('enabled', False)}")
        stats = auto_status.get('stats', {})
        print(f"  已收获: {stats.get('plants_harvested', 0)}")
        print(f"  已播种: {stats.get('seeds_planted', 0)}")
        print(f"  已浇水: {stats.get('waterings_done', 0)}")
        print(f"  已除草: {stats.get('weeds_removed', 0)}")
        
        if not auto_status.get('enabled', False):
            print("\n🚀 正在启动自动农场系统...")
            result = start_auto_farm()
            if result and result.get('success'):
                print("✅ 自动农场已启动")
            else:
                print("❌ 自动农场启动失败")
    
    print_separator()
    print("\n🔄 开始实时监控 (按 Ctrl+C 停止)...")
    print_separator()
    
    last_harvested = 0
    last_harvestable = harvestable_count
    cycle = 0
    
    try:
        while True:
            cycle += 1
            time.sleep(3)  # 每3秒检查一次
            
            # 获取当前状态
            state = get_game_state()
            if not state:
                print("⚠️ 无法获取游戏状态")
                continue
            
            counts = count_plants_by_type(state)
            harvestable_count, harvestable_list = count_harvestable_plants(state)
            auto_status = get_auto_farm_status()
            
            current_harvested = auto_status.get('stats', {}).get('plants_harvested', 0) if auto_status else 0
            
            # 检测收获变化
            if current_harvested != last_harvested or harvestable_count != last_harvestable:
                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"\n[{timestamp}] 周期 #{cycle}")
                print(f"  📦 已收获: {current_harvested} (+{current_harvested - last_harvested})")
                print(f"  🌱 可收获: {harvestable_count} (变化: {harvestable_count - last_harvestable:+d})")
                print(f"  🌾 生长中: {counts['growing']}")
                print(f"  🌿 空地: {counts['empty']}")
                print(f"  🥀 杂草: {counts['weeds']}")
                
                if auto_status:
                    current_task = auto_status.get('current_task')
                    if current_task:
                        print(f"  ⚡ 当前任务: {current_task.get('type', 'unknown')} - 位置({current_task.get('row')},{current_task.get('col')})")
                    
                    cart = state.get('cart', {})
                    print(f"  🚗 小车位置: ({cart.get('x', 0):.2f}, {cart.get('z', 0):.2f})")
                
                last_harvested = current_harvested
                last_harvestable = harvestable_count
            else:
                # 每10个周期输出一次状态
                if cycle % 10 == 0:
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    print(f"[{timestamp}] 运行中... 已收获:{current_harvested} 可收获:{harvestable_count}")
    
    except KeyboardInterrupt:
        print("\n\n🛑 监控已停止")
        print_separator()
        
        # 最终统计
        print("\n📊 最终统计:")
        state = get_game_state()
        if state:
            counts = count_plants_by_type(state)
            harvestable_count, _ = count_harvestable_plants(state)
            auto_status = get_auto_farm_status()
            
            if auto_status:
                stats = auto_status.get('stats', {})
                print(f"  总收获数: {stats.get('plants_harvested', 0)}")
                print(f"  总播种数: {stats.get('seeds_planted', 0)}")
                print(f"  总浇水数: {stats.get('waterings_done', 0)}")
                print(f"  总除草数: {stats.get('weeds_removed', 0)}")
            
            print(f"\n  当前农场状态:")
            print(f"    成熟植物: {counts['mature']}")
            print(f"    生长中: {counts['growing']}")
            print(f"    空地: {counts['empty']}")
            print(f"    杂草: {counts['weeds']}")
        
        print_separator()

if __name__ == "__main__":
    main()


