#!/usr/bin/env python3
"""
智能农场机器人仿真 - 仿真服务器
第一阶段：基础仿真化改造
"""
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import time
import json
import os
from datetime import datetime

# 导入自动化模块
from auto_farm_controller import AutoFarmController
from state_monitor import StateMonitor
from path_planner import PathPlanner
from auto_task_executor import TaskExecutor
from plant_manager import PlantManager
from resource_manager import ResourceManager

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# 初始化自动化组件
state_monitor = None
path_planner = None
resource_manager = None
plant_manager = None
task_executor = None
auto_farm_controller = None

# 仿真状态
game_state = {
    'cart': {
        'x': 0.0,
        'z': 0.0,
        'rotation': 0.0,
        'speed': 0.0
    },
    'arm': {
        'shoulder': 0,
        'elbow': 0,
        'wrist': 0
    },
    'gripper': 0,
    'energy': 100,
    'score': 0,
    'coins': 100,  # 初始资金，可以购买20颗种子
    'current_equipment': 'laser',
    'camera_mode': 'third_person',
    'plants': [],  # 植物列表
    'tasks': [],   # 任务列表
    'timestamp': time.time(),
    'auto_farm': {
        'enabled': False,
        'current_task': None,
        'status': 'idle',
        'stats': {
            'plants_harvested': 0,
            'weeds_removed': 0,
            'seeds_planted': 0,
            'waterings_done': 0
        }
    }
}

# 初始化自动化系统
def init_auto_farm_system():
    global state_monitor, path_planner, resource_manager, plant_manager, task_executor, auto_farm_controller
    
    # 初始化各组件
    state_monitor = StateMonitor()
    path_planner = PathPlanner(game_state)
    resource_manager = ResourceManager(
        initial_energy=game_state['energy'],
        initial_coins=game_state['coins']
    )
    plant_manager = PlantManager(grid_size=8)  # 使用默认网格大小
    task_executor = TaskExecutor(robot_state=game_state, plants=plant_manager.plants)
    
    # 初始化控制中心
    auto_farm_controller = AutoFarmController(server_url="http://localhost:7070")
    
    print("✅ 自动化农场系统初始化完成")

# 初始化农田植物
def init_plants():
    """初始化8x8农田（全部为空地，等待播种）"""
    plants = []
    
    grid_size = 8  # 8x8网格
    cell_size = 0.5
    offset_x = -2.0  # 调整偏移以居中
    offset_z = -2.0
    
    for row in range(grid_size):
        for col in range(grid_size):
            x = offset_x + col * cell_size + cell_size / 2
            z = offset_z + row * cell_size + cell_size / 2
            
            # 初始化为空地（没有植物）
            plant = {
                'id': f'plant_{row}_{col}',
                'row': row,
                'col': col,
                'position': {'x': x, 'y': 0.01, 'z': z},
                'is_empty': True,  # 标记为空地
                'is_removed': False
            }
            plants.append(plant)
    
    return plants

# 初始化任务
def init_tasks():
    """初始化任务（已禁用）"""
    return []  # 不使用任务系统

# 初始化仿真
game_state['plants'] = init_plants()
game_state['tasks'] = init_tasks()

# 初始化自动化系统
init_auto_farm_system()

# 计算杂草数量（空地没有杂草，初始为0）
weed_count = sum(1 for p in game_state['plants'] if p.get('is_weed', False) and not p.get('is_removed', False))
for task in game_state['tasks']:
    if task['id'] == 'remove_weeds':
        task['target'] = max(1, weed_count)  # 至少设置为1，避免任务无法完成

@app.route('/')
def index():
    """仿真主页"""
    response = app.make_response(render_template('game.html'))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/test')
def test_websocket():
    """WebSocket测试页面"""
    response = app.make_response(render_template('test_websocket.html'))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/api/game/state', methods=['GET'])
def get_game_state():
    """获取完整仿真状态"""
    return jsonify({
        'success': True,
        'state': game_state
    })

@app.route('/api/auto_farm/toggle', methods=['POST'])
def toggle_auto_farm():
    """切换自动化农场模式"""
    global auto_farm_controller
    
    enabled = not game_state['auto_farm']['enabled']
    game_state['auto_farm']['enabled'] = enabled
    
    if enabled:
        auto_farm_controller.start()
        game_state['auto_farm']['status'] = 'running'
        message = '✅ 自动化农场模式已开启！'
    else:
        auto_farm_controller.stop()
        game_state['auto_farm']['status'] = 'idle'
        message = '⚠️ 自动化农场模式已关闭！'
    
    socketio.emit('auto_farm_status_changed', {
        'enabled': enabled,
        'status': game_state['auto_farm']['status']
    })
    
    return jsonify({
        'success': True,
        'message': message,
        'enabled': enabled
    })

@app.route('/api/auto_farm/status', methods=['GET'])
def get_auto_farm_status():
    """获取自动化农场状态"""
    return jsonify({
        'enabled': game_state['auto_farm']['enabled'],
        'status': game_state['auto_farm']['status'],
        'current_task': game_state['auto_farm']['current_task'],
        'stats': game_state['auto_farm']['stats']
    })

@app.route('/api/auto_farm/settings', methods=['POST'])
def update_auto_farm_settings():
    """更新自动化农场设置"""
    data = request.get_json()
    
    # 可以添加各种自动化设置参数
    # 例如任务优先级、工作时间等
    
    return jsonify({
        'success': True,
        'message': '自动化农场设置已更新',
        'settings': data
    })

@app.route('/api/game/init', methods=['POST'])
def init_game():
    """初始化/重置仿真"""
    game_state['cart'] = {'x': 0.0, 'z': 0.0, 'rotation': 0.0, 'speed': 0.0}
    game_state['arm'] = {'shoulder': 0, 'elbow': 0, 'wrist': 0}
    game_state['gripper'] = 0
    game_state['energy'] = 100
    game_state['score'] = 0
    game_state['coins'] = 320  # 初始资金 (64块地 × 5金币 = 320)
    game_state['plants'] = init_plants()
    game_state['tasks'] = init_tasks()
    game_state['timestamp'] = time.time()
    
    # 重新计算杂草数量（空地没有杂草）
    weed_count = sum(1 for p in game_state['plants'] if p.get('is_weed', False) and not p.get('is_removed', False))
    for task in game_state['tasks']:
        if task['id'] == 'remove_weeds':
            task['target'] = max(1, weed_count)  # 至少设置为1
    
    return jsonify({
        'success': True,
        'message': 'Game initialized',
        'state': game_state
    })

@app.route('/api/cart/update', methods=['POST'])
def update_cart():
    """更新小车状态"""
    data = request.get_json()
    
    if 'x' in data:
        game_state['cart']['x'] = float(data['x'])
    if 'z' in data:
        game_state['cart']['z'] = float(data['z'])
    if 'rotation' in data:
        game_state['cart']['rotation'] = float(data['rotation'])
    if 'speed' in data:
        game_state['cart']['speed'] = float(data['speed'])
    
    game_state['timestamp'] = time.time()
    
    # 广播到所有客户端
    socketio.emit('cart_update', game_state['cart'])
    
    return jsonify({'success': True})

@app.route('/api/equipment/switch', methods=['POST'])
def switch_equipment():
    """切换装备"""
    data = request.get_json()
    equipment = data.get('equipment', 'laser')
    
    game_state['current_equipment'] = equipment
    
    socketio.emit('equipment_switch', {'equipment': equipment})
    
    return jsonify({
        'success': True,
        'equipment': equipment
    })

# 激光训练数据文件
TRAINING_DATA_FILE = 'laser_training_data.json'

def load_training_data():
    """加载训练数据"""
    if os.path.exists(TRAINING_DATA_FILE):
        with open(TRAINING_DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'shots': [], 'best_params': None, 'success_count': 0, 'total_count': 0}

def save_training_data(data):
    """保存训练数据"""
    with open(TRAINING_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def analyze_training_data(training_data):
    """分析训练数据，计算最佳参数"""
    successful_shots = [shot for shot in training_data['shots'] if shot['success']]
    
    if len(successful_shots) >= 3:  # 至少3次成功才开始学习
        # 计算成功击中时的平均参数
        avg_shoulder_offset = sum(s['shoulder_offset'] for s in successful_shots) / len(successful_shots)
        avg_elbow_angle = sum(s['elbow_angle'] for s in successful_shots) / len(successful_shots)
        avg_wrist_factor = sum(s['wrist_factor'] for s in successful_shots) / len(successful_shots)
        
        return {
            'shoulder_offset': round(avg_shoulder_offset, 3),
            'elbow_angle': round(avg_elbow_angle, 3),
            'wrist_factor': round(avg_wrist_factor, 3),
            'confidence': len(successful_shots) / max(training_data['total_count'], 1)
        }
    
    return None

@app.route('/api/laser/record_shot', methods=['POST'])
def record_laser_shot():
    """记录激光发射数据（用于学习）"""
    data = request.get_json()
    
    training_data = load_training_data()
    
    shot_record = {
        'timestamp': datetime.now().isoformat(),
        'emitter_pos': data.get('emitter_pos'),
        'target_pos': data.get('target_pos'),
        'horizontal_dist': data.get('horizontal_dist'),
        'vertical_diff': data.get('vertical_diff'),
        'pitch_angle': data.get('pitch_angle'),
        'shoulder_offset': data.get('shoulder_offset'),
        'elbow_angle': data.get('elbow_angle'),
        'wrist_factor': data.get('wrist_factor'),
        'success': data.get('success', False),
        'plant_id': data.get('plant_id')
    }
    
    training_data['shots'].append(shot_record)
    training_data['total_count'] += 1
    if shot_record['success']:
        training_data['success_count'] += 1
    
    # 分析并更新最佳参数
    best_params = analyze_training_data(training_data)
    if best_params:
        training_data['best_params'] = best_params
        print(f"\n🎓 [学习更新] 成功率: {training_data['success_count']}/{training_data['total_count']}")
        print(f"   最佳肩关节偏移: {best_params['shoulder_offset']}")
        print(f"   最佳肘关节角度: {best_params['elbow_angle']}")
        print(f"   最佳腕关节系数: {best_params['wrist_factor']}")
        print(f"   置信度: {best_params['confidence']*100:.1f}%\n")
    
    save_training_data(training_data)
    
    return jsonify({
        'success': True,
        'total_shots': training_data['total_count'],
        'successful_shots': training_data['success_count'],
        'best_params': training_data['best_params']
    })

@app.route('/api/laser/get_best_params', methods=['GET'])
def get_best_laser_params():
    """获取学习到的最佳参数"""
    training_data = load_training_data()
    return jsonify({
        'best_params': training_data.get('best_params'),
        'total_shots': training_data.get('total_count', 0),
        'successful_shots': training_data.get('success_count', 0)
    })

@app.route('/api/action/laser', methods=['POST'])
def action_laser():
    """激光除草"""
    data = request.get_json()
    plant_id = data.get('plant_id')
    
    print("\n" + "="*60)
    print("🔴 [激光调试] 接收到激光请求")
    print(f"   目标ID: {plant_id}")
    
    # 查找植物
    plant = next((p for p in game_state['plants'] if p['id'] == plant_id), None)
    
    if not plant:
        print(f"❌ [激光调试] 未找到植物: {plant_id}")
        print("="*60 + "\n")
        return jsonify({'success': False, 'message': 'Plant not found'})
    
    print(f"🎯 [激光调试] 目标植物信息:")
    print(f"   位置: x={plant['position']['x']:.2f}, y={plant['position']['y']:.2f}, z={plant['position']['z']:.2f}")
    print(f"   类型: {'🌿杂草' if plant.get('is_weed') else '🥬蔬菜'}")
    print(f"   行列: ({plant.get('row', '?')}, {plant.get('col', '?')})")
    print(f"   健康: {plant.get('health', 100)}%")
    
    if plant['is_removed']:
        print(f"⚠️ [激光调试] 植物已被移除")
        print("="*60 + "\n")
        return jsonify({'success': False, 'message': 'Plant already removed'})
    
    # 判断是否是杂草（使用 .get() 避免 KeyError）
    if plant.get('is_weed', False):
        print(f"✅ [激光调试] 击中杂草！准备清除...")
        # 成功清除杂草，土地恢复为空地
        old_id = plant['id']
        plant.clear()  # 清空所有属性
        plant['id'] = old_id
        plant['row'] = int(old_id.split('_')[1])
        plant['col'] = int(old_id.split('_')[2])
        
        # 重新计算位置
        cell_size = 0.5
        offset_x = -2.0
        offset_z = -2.0
        x = offset_x + plant['col'] * cell_size + cell_size / 2
        z = offset_z + plant['row'] * cell_size + cell_size / 2
        
        plant['position'] = {'x': x, 'y': 0.01, 'z': z}
        plant['is_empty'] = True  # 恢复为空地
        plant['is_removed'] = False
        
        game_state['score'] += 50
        game_state['coins'] += 10
        
        # 更新自动农场统计
        if 'auto_farm' in game_state and 'stats' in game_state['auto_farm']:
            game_state['auto_farm']['stats']['weeds_removed'] += 1
        
        # 更新任务进度
        for task in game_state['tasks']:
            if task['id'] == 'remove_weeds' and not task['completed']:
                task['progress'] += 1
                if task['progress'] >= task['target']:
                    task['completed'] = True
                    game_state['coins'] += task['reward_coins']
        
        print(f"🎉 [激光调试] 杂草已清除！+50分 +10💰")
        print(f"   当前分数: {game_state['score']}")
        print(f"   当前金币: {game_state['coins']}")
        print("="*60 + "\n")
        result = {'success': True, 'message': '🔥 杂草清除！土地已清空 +50分 +10💰', 'type': 'weed', 'score_change': 50}
    else:
        print(f"❌ [激光调试] 误伤蔬菜！-100分")
        # 误伤蔬菜
        plant['health'] = max(0, plant['health'] - 30)
        game_state['score'] -= 100
        
        print(f"   蔬菜健康: {plant['health']}%")
        print(f"   当前分数: {game_state['score']}")
        print("="*60 + "\n")
        result = {'success': True, 'message': '误伤蔬菜！-100', 'type': 'vegetable', 'score_change': -100}
    
    socketio.emit('laser_fired', result)
    
    return jsonify(result)

@app.route('/api/action/scan', methods=['POST'])
def action_scan():
    """扫描植物"""
    data = request.get_json()
    plant_id = data.get('plant_id')
    
    plant = next((p for p in game_state['plants'] if p['id'] == plant_id), None)
    
    if not plant:
        return jsonify({'success': False, 'message': 'Plant not found'})
    
    # 更新任务进度
    for task in game_state['tasks']:
        if task['id'] == 'tutorial_scan' and not task['completed']:
            task['progress'] += 1
            if task['progress'] >= task['target']:
                task['completed'] = True
                game_state['coins'] += task['reward_coins']
    
    # 返回植物详细信息
    return jsonify({
        'success': True,
        'plant': plant
    })

@app.route('/api/action/harvest', methods=['POST'])
def action_harvest():
    """收获成熟植物（机械臂）"""
    data = request.get_json()
    plant_id = data.get('plant_id')
    
    # 查找植物
    plant = next((p for p in game_state['plants'] if p['id'] == plant_id), None)
    
    if not plant or plant.get('is_removed'):
        return jsonify({
            'success': False,
            'message': '植物不存在'
        })
    
    # 检查是否是空地或种子
    if plant.get('is_empty', False):
        return jsonify({
            'success': False,
            'message': '这里是空地！请先播种'
        })
    
    if plant.get('is_seed', False):
        return jsonify({
            'success': False,
            'message': '种子还未发芽！请先浇水'
        })
    
    # 检查是否是蔬菜且成熟
    if not plant.get('is_vegetable', False):
        return jsonify({
            'success': False,
            'message': '杂草不能收获！请使用激光除草器'
        })
    
    growth_stage = plant.get('growth_stage', 1)
    if growth_stage < 3:  # 只有阶段3才能收获
        return jsonify({
            'success': False,
            'message': '植物还未成熟，再等等吧！需要阶段3才能收获'
        })
    
    # 🍎 计算果实数量（基于健康度）
    health = plant.get('health', 100)
    if health >= 90:
        fruit_count = 5
    elif health >= 75:
        fruit_count = 4
    elif health >= 60:
        fruit_count = 3
    elif health >= 40:
        fruit_count = 2
    else:
        fruit_count = 1
    
    # 计算收益（基于果实数量和生长阶段）
    base_yield = 10
    fruit_yield = fruit_count * 15  # 每个果实15金币
    growth_bonus = growth_stage * 5
    total_coins = base_yield + fruit_yield + growth_bonus
    
    # 如果是完全成熟（阶段3）且健康度高，额外奖励
    if growth_stage == 3 and health >= 90:
        total_coins += 20  # 完美作物奖励
        quality = '完美'
    elif growth_stage == 3:
        quality = '优质'
    else:
        quality = '普通'
    
    # 保存植物信息（在清空前）
    plant_type = plant.get('type', 'vegetable')
    plant_health = plant.get('health', 100)
    
    # 获得金币
    game_state['coins'] += total_coins
    game_state['score'] += total_coins
    
    # 更新自动农场统计
    if 'auto_farm' in game_state and 'stats' in game_state['auto_farm']:
        game_state['auto_farm']['stats']['plants_harvested'] += 1
    
    # 收获后土地恢复为空地
    plant.clear()  # 清空所有属性
    plant['id'] = plant_id
    plant['row'] = int(plant_id.split('_')[1])
    plant['col'] = int(plant_id.split('_')[2])
    
    # 重新计算位置
    cell_size = 0.5
    offset_x = -2.0
    offset_z = -2.0
    x = offset_x + plant['col'] * cell_size + cell_size / 2
    z = offset_z + plant['row'] * cell_size + cell_size / 2
    
    plant['position'] = {'x': x, 'y': 0.01, 'z': z}
    plant['is_empty'] = True  # 恢复为空地
    plant['is_removed'] = False
    
    # 更新任务进度
    for task in game_state['tasks']:
        if task['id'] == 'harvest_plants' and not task['completed']:
            task['progress'] = min(task['progress'] + 1, task['target'])
            if task['progress'] >= task['target']:
                task['completed'] = True
                game_state['coins'] += task['reward_coins']
    
    # 构建收获消息（始终显示果实数量，增强正反馈）
    message = f'🎉 收获成功！获得 {fruit_count}个🍎果实（{quality}品质）+{total_coins}💰金币'
    
    return jsonify({
        'success': True,
        'message': message,
        'coins_earned': total_coins,
        'fruit_count': fruit_count,
        'quality': quality,
        'plant_type': plant_type,
        'plant_health': plant_health
    })

@app.route('/api/action/plant', methods=['POST'])
def action_plant():
    """在空地种植新植物（机械臂）"""
    import random
    data = request.get_json()
    row = data.get('row')
    col = data.get('col')
    
    # 检查金币（种子需要5金币）
    if game_state['coins'] < 5:
        return jsonify({
            'success': False,
            'message': '金币不足！种子需要5金币'
        })
    
    # 检查该位置
    plant_id = f'plant_{row}_{col}'
    existing_plant = next((p for p in game_state['plants'] if p['id'] == plant_id), None)
    
    if not existing_plant:
        return jsonify({
            'success': False,
            'message': '无效的位置！'
        })
    
    # 检查是否为空地
    if not existing_plant.get('is_empty', False):
        return jsonify({
            'success': False,
            'message': '该位置已有植物或种子！'
        })
    
    # 计算位置
    cell_size = 0.5
    offset_x = -2.0
    offset_z = -2.0
    x = offset_x + col * cell_size + cell_size / 2
    z = offset_z + row * cell_size + cell_size / 2
    
    # 创建种子（未发芽状态）
    seed = {
        'id': plant_id,
        'row': row,
        'col': col,
        'position': {'x': x, 'y': 0.01, 'z': z},
        'type': 'seed',
        'is_seed': True,  # 标记为种子状态
        'is_empty': False,
        'is_vegetable': False,  # 还不知道会长成什么
        'is_weed': False,
        'health': 100,
        'growth_stage': 0,  # 种子阶段
        'has_pests': False,
        'pests_count': 0,
        'soil_ph': round(random.uniform(6.0, 7.0), 1),
        'soil_moisture': 30,  # 初始湿度较低
        'nutrient_n': 70,
        'nutrient_p': 60,
        'nutrient_k': 65,
        'is_removed': False,
        'plant_time': time.time()
    }
    
    # 消耗资源
    game_state['coins'] -= 5
    game_state['score'] += 10
    
    # 更新自动农场统计
    if 'auto_farm' in game_state and 'stats' in game_state['auto_farm']:
        game_state['auto_farm']['stats']['seeds_planted'] += 1
    
    # 替换空地为种子
    index = game_state['plants'].index(existing_plant)
    game_state['plants'][index] = seed
    
    return jsonify({
        'success': True,
        'message': f'🌱 播种成功！请浇水让种子发芽 (-5💰)',
        'plant': seed
    })

@app.route('/api/action/soil_detect', methods=['POST'])
def action_soil_detect():
    """土壤检测探针 - 检测土壤健康"""
    import random
    data = request.get_json()
    plant_id = data.get('plant_id')
    
    # 查找植物（获取所在位置）
    plant = next((p for p in game_state['plants'] if p['id'] == plant_id), None)
    
    if not plant:
        return jsonify({
            'success': False,
            'message': '位置不存在'
        })
    
    # 获取土壤数据
    soil_data = {
        'ph': plant.get('soil_ph', round(random.uniform(5.5, 7.5), 1)),
        'moisture': plant.get('soil_moisture', random.randint(30, 80)),
        'nitrogen': plant.get('nutrient_n', random.randint(50, 90)),
        'phosphorus': plant.get('nutrient_p', random.randint(40, 85)),
        'potassium': plant.get('nutrient_k', random.randint(45, 88)),
        'temperature': round(random.uniform(18, 28), 1),
        'conductivity': random.randint(800, 1500)
    }
    
    # 计算健康评分
    health_score = 0
    issues = []
    recommendations = []
    
    # PH值评估
    if 6.0 <= soil_data['ph'] <= 7.0:
        health_score += 20
    else:
        issues.append(f'PH值异常: {soil_data["ph"]}')
        if soil_data['ph'] < 6.0:
            recommendations.append('建议施加石灰调节PH值')
        else:
            recommendations.append('建议施加硫磺调节PH值')
    
    # 湿度评估
    if 50 <= soil_data['moisture'] <= 70:
        health_score += 20
    else:
        issues.append(f'湿度异常: {soil_data["moisture"]}%')
        if soil_data['moisture'] < 50:
            recommendations.append('土壤偏干，建议浇水')
        else:
            recommendations.append('土壤过湿，注意排水')
    
    # NPK评估
    npk_avg = (soil_data['nitrogen'] + soil_data['phosphorus'] + soil_data['potassium']) / 3
    if npk_avg >= 70:
        health_score += 30
    elif npk_avg >= 50:
        health_score += 20
    else:
        issues.append('营养不足')
        recommendations.append('建议施肥补充NPK')
    
    # 温度评估
    if 20 <= soil_data['temperature'] <= 26:
        health_score += 15
    else:
        issues.append(f'温度异常: {soil_data["temperature"]}°C')
    
    # 电导率评估
    if 1000 <= soil_data['conductivity'] <= 1300:
        health_score += 15
    
    if not issues:
        recommendations.append('土壤状况良好，继续保持')
    
    # 更新任务
    for task in game_state['tasks']:
        if task['id'] == 'soil_check' and not task['completed']:
            task['progress'] += 1
            if task['progress'] >= task['target']:
                task['completed'] = True
                game_state['coins'] += task['reward_coins']
    
    return jsonify({
        'success': True,
        'message': f'土壤检测完成 - 健康评分: {health_score}/100',
        'soil_data': soil_data,
        'health_score': health_score,
        'issues': issues,
        'recommendations': recommendations
    })

@app.route('/api/action/spray_pesticide', methods=['POST'])
def action_spray_pesticide():
    """农药喷洒器 - 消灭害虫"""
    data = request.get_json()
    plant_id = data.get('plant_id')
    
    # 查找植物
    plant = next((p for p in game_state['plants'] if p['id'] == plant_id), None)
    
    if not plant or plant.get('is_removed'):
        return jsonify({
            'success': False,
            'message': '植物不存在'
        })
    
    # 检查是否有害虫
    has_pests = plant.get('has_pests', False)
    pests_count = plant.get('pests_count', 0)
    
    if not has_pests or pests_count == 0:
        return jsonify({
            'success': False,
            'message': '该植物没有害虫',
            'pests_found': False
        })
    
    # 消灭害虫
    plant['has_pests'] = False
    old_pests_count = plant['pests_count']
    plant['pests_count'] = 0
    
    # 恢复健康度
    health_recovery = min(20, 100 - plant['health'])
    plant['health'] = min(100, plant['health'] + health_recovery)
    
    # 获得奖励
    coins_reward = old_pests_count * 5
    game_state['coins'] += coins_reward
    game_state['score'] += coins_reward
    
    # 更新任务
    for task in game_state['tasks']:
        if task['id'] == 'pest_control' and not task['completed']:
            task['progress'] += 1
            if task['progress'] >= task['target']:
                task['completed'] = True
                game_state['coins'] += task['reward_coins']
    
    return jsonify({
        'success': True,
        'message': f'成功消灭{old_pests_count}只害虫！+{coins_reward}金币',
        'pests_found': True,
        'pests_eliminated': old_pests_count,
        'health_recovery': health_recovery,
        'coins_earned': coins_reward
    })

@app.route('/api/action/water', methods=['POST'])
def action_water():
    """浇水系统 - 促进植物生长（包括杂草！）"""
    import time
    import random
    data = request.get_json()
    plant_id = data.get('plant_id')
    
    # 查找植物
    plant = next((p for p in game_state['plants'] if p['id'] == plant_id), None)
    
    if not plant or plant.get('is_removed'):
        return jsonify({
            'success': False,
            'message': '植物不存在'
        })
    
    # 检查是否为空地
    if plant.get('is_empty', False):
        return jsonify({
            'success': False,
            'message': '空地无法浇水！请先播种'
        })
    
    # 🌱 种子发芽机制
    if plant.get('is_seed', False):
        # 种子浇水后发芽成植物或杂草
        # 20%概率长出杂草，80%概率长出蔬菜
        is_vegetable = random.random() < 0.8
        
        vegetable_types = ['tomato', 'lettuce', 'carrot']
        weed_types = ['dandelion', 'crabgrass', 'thistle']
        
        # 随机初始健康度和害虫
        has_pests = random.random() < 0.15  # 15%概率有害虫
        pests_count = random.randint(1, 2) if has_pests else 0
        
        initial_health = 100
        if has_pests:
            pest_damage = pests_count * 20
            initial_health = max(40, 100 - pest_damage)
        
        # 转换为植物
        plant['is_seed'] = False
        plant['type'] = random.choice(vegetable_types if is_vegetable else weed_types)
        plant['is_vegetable'] = is_vegetable
        plant['is_weed'] = not is_vegetable
        plant['health'] = initial_health
        plant['growth_stage'] = 1  # 开始阶段1
        plant['has_pests'] = has_pests
        plant['pests_count'] = pests_count
        plant['soil_moisture'] = 60
        
        return jsonify({
            'success': True,
            'message': f'🌱 种子发芽了！{"🥬 长出了蔬菜" if is_vegetable else "🌿 长出了杂草"}！',
            'growth_stage': 1,
            'stage_changed': True,
            'health': initial_health,
            'health_recovery': 0,
            'pest_damage': 0,
            'moisture_increase': 30,
            'is_weed': not is_vegetable,
            'germinated': True,  # 标记为发芽
            'weed_spread': []
        })
    
    # 🌿 新机制：杂草也能浇水成长并扩散！
    is_weed = plant.get('is_weed', False)
    
    # 检查是否已经成熟
    if plant.get('growth_stage', 1) >= 3:
        if is_weed:
            return jsonify({
                'success': False,
                'message': '杂草已成熟！小心它会扩散！',
                'already_mature': True,
                'is_weed': True
            })
        else:
            return jsonify({
                'success': False,
                'message': '植物已完全成熟！',
                'already_mature': True
            })
    
    # 增加湿度
    old_moisture = plant.get('soil_moisture', 50)
    plant['soil_moisture'] = min(100, old_moisture + 30)
    
    # 促进生长
    old_stage = plant.get('growth_stage', 1)
    if old_stage < 3:
        plant['growth_stage'] = old_stage + 1
        stage_changed = True
    else:
        stage_changed = False
    
    # 蔬菜恢复健康，但害虫会持续损害！
    health_recovery = 0
    pest_damage_per_turn = 0
    if not is_weed:
        # 先扣除害虫持续伤害
        if plant.get('pests_count', 0) > 0:
            pest_damage_per_turn = plant['pests_count'] * 5  # 每只害虫每次-5%
            plant['health'] = max(10, plant['health'] - pest_damage_per_turn)
        
        # 再恢复一些健康（如果没害虫才能有效恢复）
        health_recovery = min(15, 100 - plant['health'])
        plant['health'] = min(100, plant['health'] + health_recovery)
        
        # 净效果：有害虫的植物会越来越不健康！
    
    # 更新浇水时间
    plant['last_watered'] = time.time()
    
    # 🌿 杂草扩散机制
    spread_info = []
    if is_weed and plant['growth_stage'] == 3:
        # 成熟的杂草会扩散到相邻四格
        row = plant['row']
        col = plant['col']
        neighbors = [
            (row - 1, col),  # 上
            (row + 1, col),  # 下
            (row, col - 1),  # 左
            (row, col + 1),  # 右
        ]
        
        weed_types = ['dandelion', 'thistle', 'crabgrass']
        spread_count = 0
        
        for n_row, n_col in neighbors:
            # 检查边界（8x8农田）
            if n_row < 0 or n_row >= 8 or n_col < 0 or n_col >= 8:
                continue
            
            # 查找该位置的植物
            neighbor_plant = next((p for p in game_state['plants'] 
                                   if p['row'] == n_row and p['col'] == n_col 
                                   and not p.get('is_removed')), None)
            
            # 如果是蔬菜，则被侵占（变成杂草）
            if neighbor_plant and neighbor_plant.get('is_vegetable'):
                # 记录旧ID用于前端更新
                old_id = neighbor_plant['id']
                
                # 转变为新杂草
                neighbor_plant['is_vegetable'] = False
                neighbor_plant['is_weed'] = True
                neighbor_plant['type'] = random.choice(weed_types)
                neighbor_plant['growth_stage'] = 1  # 新杂草从阶段1开始
                neighbor_plant['health'] = 100
                neighbor_plant['invaded_by_weed'] = True
                
                spread_info.append({
                    'plant_id': old_id,
                    'row': n_row,
                    'col': n_col,
                    'new_type': neighbor_plant['type']
                })
                spread_count += 1
        
        if spread_count > 0:
            game_state['score'] -= spread_count * 20  # 扩散惩罚
    
    # 获得奖励
    if is_weed:
        score_reward = -5 if stage_changed else -2  # 杂草成长会扣分！
        message = f'⚠️ 杂草成长了！'
        if plant['growth_stage'] == 3:
            message += f' 杂草已成熟，侵占了{len(spread_info)}块菜地！'
    else:
        score_reward = 10 if stage_changed else 5
        message = f'浇水成功！'
        if stage_changed:
            message += f' 植物成长到第{plant["growth_stage"]}阶段'
        
        # 害虫警告（重要！）
        if pest_damage_per_turn > 0:
            message += f' ⚠️ 害虫造成-{pest_damage_per_turn}%伤害！（健康度:{plant["health"]:.0f}%）'
        elif plant.get('pests_count', 0) > 0 and plant['health'] < 50:
            message += f' 🪲 植物不健康！请尽快除虫！'
    
    game_state['score'] += score_reward
    
    # 更新自动农场统计（只有蔬菜浇水才算）
    if not is_weed and 'auto_farm' in game_state and 'stats' in game_state['auto_farm']:
        game_state['auto_farm']['stats']['waterings_done'] += 1
    
    # 更新任务（只有蔬菜浇水才算）
    if not is_weed:
        for task in game_state['tasks']:
            if task['id'] == 'water_plants' and not task['completed']:
                task['progress'] += 1
                if task['progress'] >= task['target']:
                    task['completed'] = True
                    game_state['coins'] += task['reward_coins']
    
    return jsonify({
        'success': True,
        'message': message,
        'growth_stage': plant['growth_stage'],
        'stage_changed': stage_changed,
        'health': plant['health'],  # 返回最新健康度
        'health_recovery': health_recovery,
        'pest_damage': pest_damage_per_turn,  # 返回害虫伤害
        'moisture_increase': plant['soil_moisture'] - old_moisture,
        'is_weed': is_weed,
        'weed_spread': spread_info if is_weed else []
    })

@app.route('/api/camera/mode', methods=['POST'])
def set_camera_mode():
    """切换相机模式"""
    data = request.get_json()
    mode = data.get('mode', 'third_person')
    
    game_state['camera_mode'] = mode
    
    socketio.emit('camera_mode_changed', {'mode': mode})
    
    return jsonify({
        'success': True,
        'mode': mode
    })

# WebSocket事件
@socketio.on('connect')
def handle_connect():
    print(f"Client connected: {request.sid}")
    emit('connected', {'state': game_state})

@socketio.on('disconnect')
def handle_disconnect():
    print(f"Client disconnected: {request.sid}")

@socketio.on('auto_farm/request_status')
def handle_auto_farm_status_request():
    """处理前端请求自动化农场状态"""
    emit('auto_farm/status', {
        'enabled': game_state['auto_farm']['enabled'],
        'status': game_state['auto_farm']['status'],
        'current_task': game_state['auto_farm']['current_task'],
        'stats': game_state['auto_farm']['stats']
    })

# ==================== 增强型小车移动接口 ====================
# 集成 cart_movement_api.py 的功能

print("📡 正在注册增强型小车移动API...")

try:
    from cart_movement_api import register_cart_movement_apis
    register_cart_movement_apis(app, socketio, game_state)
    print("✅ 增强型小车移动API注册成功！")
except ImportError as e:
    print(f"⚠️ 无法导入cart_movement_api: {e}")
    print("   继续使用基础小车控制接口")
except Exception as e:
    print(f"⚠️ 注册增强型API时出错: {e}")

if __name__ == '__main__':
    print("=" * 60)
    print("🎮 智能农场机器人仿真 - 第一阶段")
    print("=" * 60)
    print("仿真界面: http://localhost:7070")
    print("=" * 60)
    print("控制说明:")
    print("  WASD  - 小车移动")
    print("  QE    - 小车旋转")
    print("  空格  - 刹车")
    print("  Shift - 加速")
    print("  F1-F4 - 切换视角")
    print("  1-6   - 切换装备")
    print("  鼠标  - 使用装备")
    print("=" * 60)
    print()
    print("💡 开发提示:")
    print("   - 修改Python代码后，服务器会自动重启")
    print("   - 修改HTML/JS后，按 Ctrl+Shift+R 强制刷新浏览器")
    print("=" * 60)
    socketio.run(app, debug=True, host='0.0.0.0', port=7070, allow_unsafe_werkzeug=True)

