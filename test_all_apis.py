#!/usr/bin/env python3
"""
智能农场游戏 - API接口测试脚本
测试所有已实现的API接口
"""
import requests
import json
import time
from datetime import datetime
from typing import Dict, Any

# 服务器配置
SERVER_URL = "http://localhost:7070"
TIMEOUT = 5.0

# 测试结果统计
test_results = {
    'total': 0,
    'passed': 0,
    'failed': 0,
    'errors': []
}

def print_header(text):
    """打印测试分组标题"""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70)

def print_test(test_name):
    """打印测试名称"""
    print(f"\n{'─'*70}")
    print(f"🧪 测试: {test_name}")
    print(f"{'─'*70}")

def print_result(success, message, data=None):
    """打印测试结果"""
    test_results['total'] += 1
    
    if success:
        test_results['passed'] += 1
        print(f"✅ 成功: {message}")
    else:
        test_results['failed'] += 1
        test_results['errors'].append(message)
        print(f"❌ 失败: {message}")
    
    if data:
        print(f"📊 响应数据: {json.dumps(data, indent=2, ensure_ascii=False)}")

def test_api_get(endpoint, test_name, expected_keys=None):
    """测试GET接口"""
    print_test(test_name)
    try:
        url = f"{SERVER_URL}{endpoint}"
        print(f"📡 GET {url}")
        
        response = requests.get(url, timeout=TIMEOUT)
        print(f"📨 状态码: {response.status_code}")
        
        if response.status_code != 200:
            print_result(False, f"HTTP状态码错误: {response.status_code}")
            return None
        
        data = response.json()
        
        # 检查必需的键
        if expected_keys:
            missing_keys = [k for k in expected_keys if k not in data]
            if missing_keys:
                print_result(False, f"缺少必需的字段: {missing_keys}", data)
                return None
        
        print_result(True, "接口响应正常", data)
        return data
    
    except requests.exceptions.Timeout:
        print_result(False, "请求超时")
        return None
    except requests.exceptions.ConnectionError:
        print_result(False, "连接失败 - 服务器可能未启动")
        return None
    except Exception as e:
        print_result(False, f"异常: {str(e)}")
        return None

def test_api_post(endpoint, test_name, data=None, expected_keys=None):
    """测试POST接口"""
    print_test(test_name)
    try:
        url = f"{SERVER_URL}{endpoint}"
        print(f"📡 POST {url}")
        if data:
            print(f"📤 请求数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
        response = requests.post(url, json=data, timeout=TIMEOUT)
        print(f"📨 状态码: {response.status_code}")
        
        if response.status_code != 200:
            print_result(False, f"HTTP状态码错误: {response.status_code}")
            return None
        
        response_data = response.json()
        
        # 检查必需的键
        if expected_keys:
            missing_keys = [k for k in expected_keys if k not in response_data]
            if missing_keys:
                print_result(False, f"缺少必需的字段: {missing_keys}", response_data)
                return None
        
        print_result(True, "接口响应正常", response_data)
        return response_data
    
    except requests.exceptions.Timeout:
        print_result(False, "请求超时")
        return None
    except requests.exceptions.ConnectionError:
        print_result(False, "连接失败 - 服务器可能未启动")
        return None
    except Exception as e:
        print_result(False, f"异常: {str(e)}")
        return None

def check_server_running():
    """检查服务器是否运行"""
    print_header("检查服务器状态")
    try:
        response = requests.get(f"{SERVER_URL}/", timeout=2.0)
        if response.status_code == 200:
            print("✅ 服务器正在运行")
            return True
        else:
            print(f"⚠️ 服务器响应异常: {response.status_code}")
            return False
    except:
        print("❌ 服务器未启动！")
        print(f"请先运行: python server_game.py")
        return False

# ==================== 测试用例 ====================

def test_game_state_apis():
    """测试游戏状态管理API"""
    print_header("1️⃣ 游戏状态管理 API")
    
    # 1.1 获取游戏状态
    state = test_api_get(
        "/api/game/state",
        "获取完整游戏状态",
        expected_keys=['success', 'state']
    )
    
    if state and state.get('success'):
        game_state = state.get('state', {})
        print(f"\n📊 游戏状态概览:")
        print(f"   金币: {game_state.get('coins', 0)}")
        print(f"   分数: {game_state.get('score', 0)}")
        print(f"   能量: {game_state.get('energy', 0)}")
        print(f"   当前装备: {game_state.get('current_equipment', 'unknown')}")
        print(f"   植物数量: {len(game_state.get('plants', []))}")
        print(f"   任务数量: {len(game_state.get('tasks', []))}")
    
    # 1.2 初始化游戏
    test_api_post(
        "/api/game/init",
        "初始化/重置游戏",
        expected_keys=['success', 'message', 'state']
    )

def test_cart_apis():
    """测试小车控制API"""
    print_header("2️⃣ 小车控制 API")
    
    # 2.1 更新小车位置
    test_api_post(
        "/api/cart/update",
        "更新小车位置",
        data={'x': 1.5, 'z': 2.0, 'rotation': 45.0, 'speed': 3.0},
        expected_keys=['success']
    )
    
    # 2.2 停止小车
    test_api_post(
        "/api/cart/update",
        "停止小车",
        data={'speed': 0.0},
        expected_keys=['success']
    )

def test_equipment_apis():
    """测试装备管理API"""
    print_header("3️⃣ 装备管理 API")
    
    equipments = ['laser', 'scanner', 'arm', 'sprayer', 'watering', 'soil_probe']
    
    for equipment in equipments:
        test_api_post(
            "/api/equipment/switch",
            f"切换装备 - {equipment}",
            data={'equipment': equipment},
            expected_keys=['success', 'equipment']
        )
        time.sleep(0.1)

def test_camera_apis():
    """测试相机控制API"""
    print_header("4️⃣ 相机控制 API")
    
    camera_modes = ['third_person', 'first_person', 'top_down', 'free']
    
    for mode in camera_modes:
        test_api_post(
            "/api/camera/mode",
            f"切换相机模式 - {mode}",
            data={'mode': mode},
            expected_keys=['success', 'mode']
        )
        time.sleep(0.1)

def test_auto_farm_apis():
    """测试自动化农场API"""
    print_header("5️⃣ 自动化农场 API")
    
    # 5.1 获取自动化状态
    test_api_get(
        "/api/auto_farm/status",
        "获取自动化农场状态",
        expected_keys=['enabled', 'status']
    )
    
    # 5.2 切换自动化模式（开启）
    result = test_api_post(
        "/api/auto_farm/toggle",
        "开启自动化模式",
        expected_keys=['success', 'enabled']
    )
    
    if result and result.get('enabled'):
        time.sleep(2)  # 等待自动化执行一些任务
        
        # 5.3 再次获取状态
        test_api_get(
            "/api/auto_farm/status",
            "获取运行中的自动化状态",
            expected_keys=['enabled', 'status', 'stats']
        )
        
        # 5.4 关闭自动化模式
        test_api_post(
            "/api/auto_farm/toggle",
            "关闭自动化模式",
            expected_keys=['success', 'enabled']
        )
    
    # 5.5 更新自动化设置
    test_api_post(
        "/api/auto_farm/settings",
        "更新自动化设置",
        data={
            'priority': 'high',
            'auto_plant': True,
            'max_budget': 100
        },
        expected_keys=['success']
    )

def test_farm_operation_apis():
    """测试农场操作API"""
    print_header("6️⃣ 农场操作 API")
    
    # 先获取游戏状态，找到可操作的植物
    state_response = requests.get(f"{SERVER_URL}/api/game/state", timeout=TIMEOUT)
    if state_response.status_code != 200:
        print("⚠️ 无法获取游戏状态，跳过农场操作测试")
        return
    
    game_state = state_response.json().get('state', {})
    plants = game_state.get('plants', [])
    
    # 找到第一株植物用于测试
    test_plant = None
    empty_plot = None
    weed_plant = None
    vegetable_plant = None
    
    for plant in plants:
        if plant.get('is_empty'):
            if not empty_plot:
                empty_plot = plant
        elif plant.get('is_weed'):
            if not weed_plant:
                weed_plant = plant
        elif plant.get('is_vegetable'):
            if not vegetable_plant:
                vegetable_plant = plant
        
        if not test_plant and not plant.get('is_removed'):
            test_plant = plant
    
    # 6.1 扫描植物
    if test_plant:
        test_api_post(
            "/api/action/scan",
            f"扫描植物 - {test_plant['id']}",
            data={'plant_id': test_plant['id']},
            expected_keys=['success']
        )
    
    # 6.2 土壤检测
    if test_plant:
        test_api_post(
            "/api/action/soil_detect",
            f"土壤检测 - {test_plant['id']}",
            data={'plant_id': test_plant['id']},
            expected_keys=['success', 'soil_data']
        )
    
    # 6.3 播种（需要空地）
    if empty_plot:
        test_api_post(
            "/api/action/plant",
            f"在空地播种 - 位置({empty_plot.get('row')}, {empty_plot.get('col')})",
            data={'row': empty_plot.get('row'), 'col': empty_plot.get('col')},
            expected_keys=['success']
        )
        
        # 播种后浇水让种子发芽
        time.sleep(0.5)
        seed_id = f"plant_{empty_plot.get('row')}_{empty_plot.get('col')}"
        test_api_post(
            "/api/action/water",
            f"浇水让种子发芽 - {seed_id}",
            data={'plant_id': seed_id},
            expected_keys=['success']
        )
    
    # 6.4 浇水（蔬菜）
    if vegetable_plant and not vegetable_plant.get('is_seed'):
        test_api_post(
            "/api/action/water",
            f"浇水蔬菜 - {vegetable_plant['id']}",
            data={'plant_id': vegetable_plant['id']},
            expected_keys=['success']
        )
    
    # 6.5 激光除草
    if weed_plant:
        test_api_post(
            "/api/action/laser",
            f"激光除草 - {weed_plant['id']}",
            data={'plant_id': weed_plant['id']},
            expected_keys=['success', 'message']
        )
    
    # 6.6 收获（需要成熟植物）
    mature_plant = next((p for p in plants 
                        if p.get('is_vegetable') 
                        and p.get('growth_stage', 0) >= 3 
                        and not p.get('is_removed')), None)
    
    if mature_plant:
        test_api_post(
            "/api/action/harvest",
            f"收获成熟植物 - {mature_plant['id']}",
            data={'plant_id': mature_plant['id']},
            expected_keys=['success']
        )
    else:
        print("\n⚠️ 没有成熟植物可以收获，跳过收获测试")
    
    # 6.7 喷洒农药（需要有害虫的植物）
    pest_plant = next((p for p in plants 
                      if p.get('has_pests') 
                      and p.get('pests_count', 0) > 0 
                      and not p.get('is_removed')), None)
    
    if pest_plant:
        test_api_post(
            "/api/action/spray_pesticide",
            f"喷洒农药 - {pest_plant['id']}",
            data={'plant_id': pest_plant['id']},
            expected_keys=['success']
        )
    else:
        print("\n⚠️ 没有害虫植物，跳过农药喷洒测试")

def test_laser_learning_apis():
    """测试激光学习系统API"""
    print_header("7️⃣ 激光学习系统 API")
    
    # 7.1 获取最佳参数
    test_api_get(
        "/api/laser/get_best_params",
        "获取学习到的最佳激光参数",
        expected_keys=['total_shots', 'successful_shots']
    )
    
    # 7.2 记录射击数据
    test_api_post(
        "/api/laser/record_shot",
        "记录激光射击数据",
        data={
            'emitter_pos': {'x': 0, 'y': 0.5, 'z': 0},
            'target_pos': {'x': 1.0, 'y': 0.1, 'z': 1.0},
            'horizontal_dist': 1.414,
            'vertical_diff': -0.4,
            'pitch_angle': -15.5,
            'shoulder_offset': 0.2,
            'elbow_angle': 45.0,
            'wrist_factor': 0.8,
            'success': True,
            'plant_id': 'plant_0_0'
        },
        expected_keys=['success', 'total_shots', 'successful_shots']
    )

def print_summary():
    """打印测试总结"""
    print_header("📊 测试结果总结")
    
    print(f"\n总测试数: {test_results['total']}")
    print(f"✅ 通过: {test_results['passed']}")
    print(f"❌ 失败: {test_results['failed']}")
    
    if test_results['failed'] > 0:
        success_rate = (test_results['passed'] / test_results['total']) * 100
        print(f"📈 成功率: {success_rate:.1f}%")
        
        print(f"\n❌ 失败的测试:")
        for i, error in enumerate(test_results['errors'], 1):
            print(f"   {i}. {error}")
    else:
        print(f"\n🎉 所有测试通过！")
    
    print("\n" + "="*70)

# ==================== 主测试流程 ====================

def main():
    """主测试流程"""
    print("\n")
    print("╔═══════════════════════════════════════════════════════════════════╗")
    print("║                                                                   ║")
    print("║          🧪 智能农场游戏 - API 接口测试                          ║")
    print("║                                                                   ║")
    print("╚═══════════════════════════════════════════════════════════════════╝")
    print(f"\n⏰ 测试开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 服务器地址: {SERVER_URL}")
    
    # 检查服务器
    if not check_server_running():
        print("\n⚠️ 测试终止：服务器未运行")
        return
    
    # 执行各类测试
    try:
        test_game_state_apis()          # 游戏状态
        test_cart_apis()                 # 小车控制
        test_equipment_apis()            # 装备管理
        test_camera_apis()               # 相机控制
        test_auto_farm_apis()            # 自动化农场
        test_farm_operation_apis()       # 农场操作
        test_laser_learning_apis()       # 激光学习
        
    except KeyboardInterrupt:
        print("\n\n⚠️ 测试被用户中断")
    except Exception as e:
        print(f"\n\n❌ 测试过程发生异常: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # 打印总结
    print(f"\n⏰ 测试结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print_summary()

if __name__ == "__main__":
    main()







