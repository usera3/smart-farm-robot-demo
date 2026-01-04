#!/usr/bin/env python3
"""
小车移动控制接口扩展
为server_game.py添加小车自动移动功能
"""
import time
import math
import threading
from flask import request, jsonify

# 这些接口应该添加到 server_game.py 中

# ==================== 工具函数 ====================

def calculate_distance(x1, z1, x2, z2):
    """计算两点之间的距离"""
    return math.sqrt((x2 - x1)**2 + (z2 - z1)**2)

def calculate_angle(x1, z1, x2, z2):
    """计算从点1到点2的角度（度数）"""
    angle_rad = math.atan2(z2 - z1, x2 - x1)
    angle_deg = math.degrees(angle_rad)
    return angle_deg

def normalize_angle(angle):
    """将角度标准化到 [-180, 180] 范围"""
    while angle > 180:
        angle -= 360
    while angle < -180:
        angle += 360
    return angle

def interpolate(start, end, t):
    """线性插值"""
    return start + (end - start) * t

def calculate_plant_position(row, col, grid_size=8, cell_size=0.5):
    """计算植物在世界坐标系中的位置"""
    offset_x = -2.0
    offset_z = -2.0
    x = offset_x + col * cell_size + cell_size / 2
    z = offset_z + row * cell_size + cell_size / 2
    return {'x': x, 'z': z}

# ==================== 移动控制接口 ====================

def cart_move_to(app, socketio, game_state):
    """
    小车移动到指定坐标（带动画）
    """
    @app.route('/api/cart/move_to', methods=['POST'])
    def move_to():
        data = request.get_json()
        target_x = data.get('target_x')
        target_z = data.get('target_z')
        speed = data.get('speed', 3.0)  # 默认速度
        smooth = data.get('smooth', True)  # 是否平滑移动
        
        if target_x is None or target_z is None:
            return jsonify({
                'success': False,
                'message': '缺少目标坐标'
            })
        
        # 启动移动线程（非阻塞）
        movement_thread = threading.Thread(
            target=_execute_movement,
            args=(game_state, socketio, target_x, target_z, speed, smooth)
        )
        movement_thread.daemon = True
        movement_thread.start()
        
        return jsonify({
            'success': True,
            'message': f'小车开始移动到 ({target_x:.2f}, {target_z:.2f})'
        })

def _execute_movement(game_state, socketio, target_x, target_z, speed, smooth):
    """
    在后台线程中执行小车移动
    """
    start_x = game_state['cart']['x']
    start_z = game_state['cart']['z']
    
    # 计算总距离和所需时间
    distance = calculate_distance(start_x, start_z, target_x, target_z)
    duration = distance / speed  # 秒
    
    # 计算目标角度并旋转
    target_rotation = calculate_angle(start_x, start_z, target_x, target_z)
    
    # 先旋转到目标方向
    _execute_rotation(game_state, socketio, target_rotation, smooth=True)
    
    # 执行移动
    steps = int(duration * 30)  # 30fps
    if steps < 1:
        steps = 1
    
    for i in range(steps + 1):
        t = i / steps if steps > 0 else 1.0
        
        # 平滑移动（使用缓动函数）
        if smooth:
            # ease-in-out
            t = t * t * (3.0 - 2.0 * t)
        
        # 更新位置
        current_x = interpolate(start_x, target_x, t)
        current_z = interpolate(start_z, target_z, t)
        
        game_state['cart']['x'] = current_x
        game_state['cart']['z'] = current_z
        game_state['cart']['speed'] = speed if t < 1.0 else 0.0
        
        # 广播位置更新
        socketio.emit('cart_update', {
            'x': current_x,
            'z': current_z,
            'rotation': target_rotation,
            'speed': game_state['cart']['speed']
        })
        
        time.sleep(1.0 / 30)  # 30fps
    
    # 确保到达精确位置
    game_state['cart']['x'] = target_x
    game_state['cart']['z'] = target_z
    game_state['cart']['speed'] = 0.0
    
    socketio.emit('cart_update', {
        'x': target_x,
        'z': target_z,
        'rotation': target_rotation,
        'speed': 0.0
    })
    
    # 发送移动完成事件
    socketio.emit('cart_movement_completed', {
        'x': target_x,
        'z': target_z
    })

def _execute_rotation(game_state, socketio, target_rotation, smooth=True):
    """
    旋转小车到目标角度
    """
    start_rotation = game_state['cart']['rotation']
    
    # 计算最短旋转路径
    angle_diff = normalize_angle(target_rotation - start_rotation)
    
    # 旋转速度（度/秒）
    rotation_speed = 180.0  # 每秒180度
    duration = abs(angle_diff) / rotation_speed
    
    steps = int(duration * 30)  # 30fps
    if steps < 1:
        steps = 1
    
    for i in range(steps + 1):
        t = i / steps if steps > 0 else 1.0
        
        if smooth:
            t = t * t * (3.0 - 2.0 * t)
        
        current_rotation = start_rotation + angle_diff * t
        game_state['cart']['rotation'] = current_rotation
        
        socketio.emit('cart_update', {
            'x': game_state['cart']['x'],
            'z': game_state['cart']['z'],
            'rotation': current_rotation,
            'speed': 0.0
        })
        
        time.sleep(1.0 / 30)
    
    game_state['cart']['rotation'] = target_rotation

def cart_move_to_plant(app, socketio, game_state):
    """
    小车移动到植物操作位置
    """
    @app.route('/api/cart/move_to_plant', methods=['POST'])
    def move_to_plant():
        data = request.get_json()
        plant_id = data.get('plant_id')
        offset = data.get('offset', 0.3)  # 距离植物的偏移
        speed = data.get('speed', 3.0)
        
        # 查找植物
        plant = next((p for p in game_state['plants'] if p['id'] == plant_id), None)
        
        if not plant:
            return jsonify({
                'success': False,
                'message': f'未找到植物: {plant_id}'
            })
        
        # 从植物ID或属性中获取行列信息
        row = plant.get('row')
        col = plant.get('col')
        
        if row is None or col is None:
            # 尝试从ID中解析
            try:
                parts = plant_id.split('_')
                row = int(parts[1])
                col = int(parts[2])
            except:
                return jsonify({
                    'success': False,
                    'message': '无法确定植物位置'
                })
        
        # 计算植物位置
        plant_pos = calculate_plant_position(row, col)
        
        # 计算操作位置（植物前方，留出操作空间）
        target_x = plant_pos['x']
        target_z = plant_pos['z'] - offset  # 在植物前方
        
        # 启动移动线程
        movement_thread = threading.Thread(
            target=_execute_movement,
            args=(game_state, socketio, target_x, target_z, speed, True)
        )
        movement_thread.daemon = True
        movement_thread.start()
        
        return jsonify({
            'success': True,
            'message': f'小车开始移动到植物 {plant_id}',
            'plant_position': plant_pos,
            'target_position': {'x': target_x, 'z': target_z}
        })

def cart_rotate_to(app, socketio, game_state):
    """
    小车旋转到指定角度
    """
    @app.route('/api/cart/rotate_to', methods=['POST'])
    def rotate_to():
        data = request.get_json()
        target_rotation = data.get('target_rotation')
        smooth = data.get('smooth', True)
        
        if target_rotation is None:
            return jsonify({
                'success': False,
                'message': '缺少目标角度'
            })
        
        # 启动旋转线程
        rotation_thread = threading.Thread(
            target=_execute_rotation,
            args=(game_state, socketio, target_rotation, smooth)
        )
        rotation_thread.daemon = True
        rotation_thread.start()
        
        return jsonify({
            'success': True,
            'message': f'小车开始旋转到 {target_rotation}°'
        })

def cart_stop(app, game_state):
    """
    立即停止小车
    """
    @app.route('/api/cart/stop', methods=['POST'])
    def stop():
        game_state['cart']['speed'] = 0.0
        
        return jsonify({
            'success': True,
            'message': '小车已停止',
            'position': {
                'x': game_state['cart']['x'],
                'z': game_state['cart']['z'],
                'rotation': game_state['cart']['rotation']
            }
        })

def get_cart_position(app, game_state):
    """
    获取小车当前位置和状态
    """
    @app.route('/api/cart/position', methods=['GET'])
    def position():
        return jsonify({
            'success': True,
            'cart': game_state['cart']
        })

# ==================== 路径规划接口 ====================

def cart_follow_path(app, socketio, game_state):
    """
    小车按路径点移动
    """
    @app.route('/api/cart/follow_path', methods=['POST'])
    def follow_path():
        data = request.get_json()
        waypoints = data.get('waypoints', [])
        speed = data.get('speed', 3.0)
        
        if not waypoints:
            return jsonify({
                'success': False,
                'message': '路径点列表为空'
            })
        
        # 启动路径跟随线程
        path_thread = threading.Thread(
            target=_execute_path_following,
            args=(game_state, socketio, waypoints, speed)
        )
        path_thread.daemon = True
        path_thread.start()
        
        return jsonify({
            'success': True,
            'message': f'小车开始跟随路径（{len(waypoints)}个路点）',
            'waypoints': waypoints
        })

def _execute_path_following(game_state, socketio, waypoints, speed):
    """
    执行路径跟随
    """
    for i, waypoint in enumerate(waypoints):
        target_x = waypoint['x']
        target_z = waypoint['z']
        
        # 通知当前路点
        socketio.emit('cart_waypoint_reached', {
            'waypoint_index': i,
            'waypoint': waypoint,
            'total_waypoints': len(waypoints)
        })
        
        # 移动到路点
        _execute_movement(game_state, socketio, target_x, target_z, speed, True)
        
        # 短暂停留
        time.sleep(0.2)
    
    # 路径完成
    socketio.emit('cart_path_completed', {
        'total_waypoints': len(waypoints)
    })

# ==================== 智能导航接口 ====================

def cart_navigate_to_all_plants(app, socketio, game_state):
    """
    智能规划路径访问所有植物（TSP问题简化版）
    """
    @app.route('/api/cart/navigate_all_plants', methods=['POST'])
    def navigate_all_plants():
        data = request.get_json()
        filter_type = data.get('filter')  # 'weed', 'vegetable', 'mature', None
        speed = data.get('speed', 3.0)
        
        # 筛选目标植物
        target_plants = []
        for plant in game_state['plants']:
            if plant.get('is_removed') or plant.get('is_empty'):
                continue
            
            if filter_type == 'weed' and not plant.get('is_weed'):
                continue
            elif filter_type == 'vegetable' and not plant.get('is_vegetable'):
                continue
            elif filter_type == 'mature' and plant.get('growth_stage', 0) < 3:
                continue
            
            target_plants.append(plant)
        
        if not target_plants:
            return jsonify({
                'success': False,
                'message': '没有符合条件的植物'
            })
        
        # 简单的最近邻路径规划
        waypoints = _plan_nearest_neighbor_path(
            game_state['cart']['x'],
            game_state['cart']['z'],
            target_plants
        )
        
        # 执行路径
        path_thread = threading.Thread(
            target=_execute_path_following,
            args=(game_state, socketio, waypoints, speed)
        )
        path_thread.daemon = True
        path_thread.start()
        
        return jsonify({
            'success': True,
            'message': f'开始访问 {len(target_plants)} 株植物',
            'plant_count': len(target_plants),
            'waypoints': waypoints
        })

def _plan_nearest_neighbor_path(start_x, start_z, plants):
    """
    使用最近邻算法规划路径
    """
    waypoints = []
    remaining = plants.copy()
    current_x, current_z = start_x, start_z
    
    while remaining:
        # 找到最近的植物
        nearest = min(
            remaining,
            key=lambda p: calculate_distance(
                current_x, current_z,
                p['position']['x'], p['position']['z']
            )
        )
        
        # 添加到路径
        waypoints.append({
            'x': nearest['position']['x'],
            'z': nearest['position']['z'],
            'plant_id': nearest['id']
        })
        
        # 更新当前位置
        current_x = nearest['position']['x']
        current_z = nearest['position']['z']
        
        # 从剩余列表中移除
        remaining.remove(nearest)
    
    return waypoints

# ==================== 注册所有接口 ====================

def register_cart_movement_apis(app, socketio, game_state):
    """
    注册所有小车移动相关的API
    
    使用方法：
    在 server_game.py 中添加：
    
    from cart_movement_api import register_cart_movement_apis
    register_cart_movement_apis(app, socketio, game_state)
    """
    print("📡 正在注册小车移动API...")
    
    cart_move_to(app, socketio, game_state)
    cart_move_to_plant(app, socketio, game_state)
    cart_rotate_to(app, socketio, game_state)
    cart_stop(app, game_state)
    get_cart_position(app, game_state)
    cart_follow_path(app, socketio, game_state)
    cart_navigate_to_all_plants(app, socketio, game_state)
    
    print("✅ 小车移动API注册完成！")
    print("   - POST /api/cart/move_to")
    print("   - POST /api/cart/move_to_plant")
    print("   - POST /api/cart/rotate_to")
    print("   - POST /api/cart/stop")
    print("   - GET  /api/cart/position")
    print("   - POST /api/cart/follow_path")
    print("   - POST /api/cart/navigate_all_plants")

# ==================== 使用示例 ====================

"""
在 server_game.py 中集成这些接口：

1. 导入模块
from cart_movement_api import register_cart_movement_apis

2. 在 socketio.run() 之前注册接口
register_cart_movement_apis(app, socketio, game_state)

3. 使用示例：

# Python客户端调用
import requests

# 移动到指定坐标
response = requests.post('http://localhost:7070/api/cart/move_to', json={
    'target_x': 1.5,
    'target_z': 2.0,
    'speed': 5.0,
    'smooth': True
})

# 移动到植物位置
response = requests.post('http://localhost:7070/api/cart/move_to_plant', json={
    'plant_id': 'plant_3_4',
    'offset': 0.3,
    'speed': 3.0
})

# 旋转到指定角度
response = requests.post('http://localhost:7070/api/cart/rotate_to', json={
    'target_rotation': 90.0,
    'smooth': True
})

# 跟随路径
response = requests.post('http://localhost:7070/api/cart/follow_path', json={
    'waypoints': [
        {'x': 0.0, 'z': 0.0},
        {'x': 1.0, 'z': 1.0},
        {'x': 2.0, 'z': 1.0}
    ],
    'speed': 4.0
})

# 自动访问所有杂草
response = requests.post('http://localhost:7070/api/cart/navigate_all_plants', json={
    'filter': 'weed',
    'speed': 5.0
})
"""







