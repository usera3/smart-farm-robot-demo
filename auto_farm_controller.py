#!/usr/bin/env python3
"""
智能农场自动化控制中心
作为整个自动化系统的中央调度器
"""
import time
import json
import requests
import threading
from datetime import datetime
from enum import Enum
import logging
import json
from typing import Dict, List, Any, Optional, Tuple
import requests
import random

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('AutoFarmController')

# 避免循环导入的函数
def _get_socketio():
    """动态获取socketio实例，避免循环导入"""
    try:
        import importlib
        server_game = importlib.import_module('server_game')
        return server_game.socketio
    except (ImportError, AttributeError) as e:
        logger.warning(f"无法获取socketio实例: {e}")
        return None

def _get_game_state():
    """动态获取game_state，避免循环导入"""
    try:
        import importlib
        server_game = importlib.import_module('server_game')
        return server_game.game_state
    except (ImportError, AttributeError) as e:
        logger.warning(f"无法获取game_state: {e}")
        return None

def emit_socket_event(event, data):
    """发送Socket.IO事件，如果可用的话"""
    try:
        socket = _get_socketio()
        if socket:
            socket.emit(event, data)
            return True
        return False
    except Exception as e:
        logger.error(f"发送Socket.IO事件失败: {e}")
        return False

def broadcast_game_state():
    """广播游戏状态更新"""
    try:
        socket = _get_socketio()
        game_state = _get_game_state()
        if socket and game_state:
            socket.emit('game_state_updated', game_state)
            return True
        return False
    except Exception as e:
        logger.error(f"广播游戏状态失败: {e}")
        return False
    socketio = None
    game_state = {}
    SOCKETIO_AVAILABLE = False

# 配置日志
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('AutoFarmController')

class TaskPriority(Enum):
    """任务优先级枚举"""
    CRITICAL = 0  # 紧急（如快速生长的杂草）
    HIGH = 1      # 高优先级（如成熟植物收获）
    MEDIUM = 2    # 中等优先级（如浇水、施肥）
    LOW = 3       # 低优先级（如空地播种）

class TaskType(Enum):
    """任务类型枚举"""
    WEED_REMOVAL = "weed_removal"
    HARVEST = "harvest"
    WATERING = "watering"
    FERTILIZING = "fertilizing"
    PLANTING = "planting"
    SOIL_PREPARATION = "soil_preparation"

class AutoFarmController:
    """
    自动化农场控制中心
    负责调度和执行所有自动化任务
    """
    def __init__(self, server_url="http://localhost:7070"):
        self.server_url = server_url
        self.running = False
        self.task_queue = []  # 任务队列
        self.harvest_queue = []  # 持久化的收获队列（不会被清空）
        self.current_cart_position = {'x': 0.0, 'z': 0.0}  # 小车当前位置
        self.lock = threading.Lock()  # 线程锁
        self.current_task = None
        self.stats = {
            'cycles': 0,
            'tasks_completed': 0,
            'weeds_removed': 0,
            'plants_harvested': 0,
            'plants_watered': 0,
            'plants_fertilized': 0,
            'plants_planted': 0,
            'errors': 0
        }
        self.last_state_update = None
        self.game_state = None
        self.harvest_mode_active = False  # 是否正在执行收获模式
        
    def start(self):
        """启动自动化控制中心"""
        logger.info("🚀 智能农场自动化控制系统启动中...")
        self.running = True
        
        try:
            # 启动主循环
            while self.running:
                self.run_cycle()
                time.sleep(1)  # 每秒执行一次循环
        except KeyboardInterrupt:
            logger.warning("⚠️ 用户中断自动化系统")
        except Exception as e:
            logger.error(f"❌ 自动化系统发生错误: {str(e)}")
            self.stats['errors'] += 1
        finally:
            self.running = False
            self.print_summary()
            logger.info("✅ 自动化系统已停止")
    
    def stop(self):
        """停止自动化控制中心"""
        self.running = False
        # 更新游戏状态
        if self.game_state and 'auto_farm' in self.game_state:
            self.game_state['auto_farm']['enabled'] = False
            self.game_state['auto_farm']['status'] = 'idle'
            self.game_state['auto_farm']['current_task'] = None
        logger.info("🛑 自动化控制中心已停止")
    
    def run_cycle(self):
        """执行一个自动化周期"""
        self.stats['cycles'] += 1
        print(f"\n🔄 执行自动化周期 #{self.stats['cycles']}")
        
        # 1. 更新游戏状态
        if not self._update_game_state():
            print("❌ 无法获取游戏状态，跳过本轮")
            return
        
        # 2. 检查是否有未完成的收获队列
        if self.harvest_queue:
            logger.info(f"🌾 收获模式：还有 {len(self.harvest_queue)} 个植物待收获")
            self._execute_harvest_batch()
            return
        
        # 3. 扫描并初始化收获队列
        harvestable_plants = self._scan_harvestable_plants()
        if harvestable_plants:
            logger.info(f"🌾 发现 {len(harvestable_plants)} 个成熟植物，开始收获模式")
            self.harvest_queue = harvestable_plants
            self.harvest_mode_active = True
            self._execute_harvest_batch()
            return
        
        # 4. 没有收获任务，执行其他任务
        self._analyze_farm_state()
        
        if self.task_queue:
            # 统计高优先级任务
            high_priority_tasks = [t for t in self.task_queue if t['type'] == TaskType.WEED_REMOVAL]
            
            if high_priority_tasks:
                # 除草任务，连续执行多个
                tasks_to_execute = min(3, len(high_priority_tasks))
                logger.info(f"🎯 发现 {len(high_priority_tasks)} 个除草任务，本轮执行 {tasks_to_execute} 个")
                
                for i in range(tasks_to_execute):
                    if self.task_queue:
                        self._execute_next_task()
                        time.sleep(0.2)
            else:
                # 只有低优先级任务（浇水、播种），执行一个即可
                self._execute_next_task()
        else:
            print("✅ 当前无任务需要执行")
    
    def _update_game_state(self):
        """从服务器获取最新的游戏状态"""
        try:
            # 尝试使用正确的API端点
            response = requests.get(f"{self.server_url}/api/game/state", timeout=5.0)
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.game_state = data.get('state')
                    self.last_state_update = datetime.now()
                    logger.info(f"📊 已更新游戏状态，当前金币: {self.game_state.get('coins', 0)}")
                    return True
            
            # 如果/api/game/state失败，尝试备用端点
            logger.warning(f"尝试备用API端点: {self.server_url}/api/game_state")
            response = requests.get(f"{self.server_url}/api/game_state", timeout=5.0)
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.game_state = data.get('state')
                    self.last_state_update = datetime.now()
                    logger.info(f"📊 已更新游戏状态，当前金币: {self.game_state.get('coins', 0)}")
                    return True
                    
            logger.error(f"❌ 获取游戏状态失败: HTTP {response.status_code}")
            return False
        except requests.exceptions.Timeout:
            logger.error("❌ 获取游戏状态超时")
            return False
        except Exception as e:
            logger.error(f"❌ 获取游戏状态出错: {str(e)}")
            return False
    
    def _analyze_farm_state(self):
        """分析农场状态并生成任务"""
        if not self.game_state:
            return
        
        # 获取植物数据，适配不同的数据结构
        plants = self.game_state.get('plants', [])
        
        # 处理二维数组形式的植物数据
        if isinstance(plants, list) and plants and isinstance(plants[0], list):
            flattened_plants = []
            for row_idx, row in enumerate(plants):
                for col_idx, plant in enumerate(row):
                    if plant:
                        # 为二维数组中的植物添加行列信息和ID
                        plant_copy = plant.copy()
                        plant_copy['row'] = row_idx
                        plant_copy['col'] = col_idx
                        plant_copy['id'] = f"plant_{row_idx}_{col_idx}"
                        flattened_plants.append(plant_copy)
                    else:
                        # 添加空地信息
                        flattened_plants.append({
                            'id': f"empty_{row_idx}_{col_idx}",
                            'row': row_idx,
                            'col': col_idx,
                            'is_empty': True,
                            'state': 'empty'
                        })
            plants = flattened_plants
        
        with self.lock:
            # 清空当前任务队列
            self.task_queue = []
            
            # 检查机器人能量
            robot_energy = self.game_state.get('robot', {}).get('energy', 100)
            if robot_energy < 20:
                logger.warning("⚠️ 机器人能量不足，暂停执行任务")
                if 'auto_farm' in self.game_state:
                    self.game_state['auto_farm']['status'] = 'energy_low'
                return
            
            # 统计植物状态
            harvestable_count = 0
            weed_count = 0
            need_water_count = 0
            empty_count = 0
            
            # 分析每株植物
            for plant in plants:
                if plant.get('is_removed') or plant.get('removed'):
                    continue
                    
                # 检查是否是空地或空地块
                if plant.get('is_empty') or plant.get('state') == 'empty' or plant.get('type') == 'empty':
                    empty_count += 1
                    # 检查金币是否足够播种
                    if self.game_state.get('coins', 0) >= 10:
                        # 创建播种任务
                        self._add_task(
                            TaskType.PLANTING,
                            plant_id=plant['id'],
                            priority=TaskPriority.LOW,
                            row=plant.get('row'),
                            col=plant.get('col')
                        )
                elif plant.get('is_weed') or plant.get('type') == 'weed' or plant.get('state') == 'weed':
                    weed_count += 1
                    # 创建除草任务 - 杂草应该是高优先级
                    self._add_task(
                        TaskType.WEED_REMOVAL,
                        plant_id=plant['id'],
                        priority=TaskPriority.HIGH,
                        row=plant.get('row'),
                        col=plant.get('col')
                    )
                else:
                    # 不再在这里生成收获任务（由专门的收获队列管理）
                    # 只统计可收获植物数量
                    if self._is_harvestable(plant):
                        harvestable_count += 1
                    
                    # 检查是否需要浇水
                    if self._needs_watering(plant):
                        need_water_count += 1
                        self._add_task(
                            TaskType.WATERING,
                            plant_id=plant['id'],
                            priority=TaskPriority.MEDIUM,
                            row=plant.get('row'),
                            col=plant.get('col')
                        )
            
            # 按优先级排序任务
            self.task_queue.sort(key=lambda t: t['priority'].value)
            
            # 详细的任务统计
            water_tasks = sum(1 for t in self.task_queue if t['type'] == TaskType.WATERING)
            weed_tasks = sum(1 for t in self.task_queue if t['type'] == TaskType.WEED_REMOVAL)
            plant_tasks = sum(1 for t in self.task_queue if t['type'] == TaskType.PLANTING)
            
            logger.info(f"📋 农场状态分析完成:")
            logger.info(f"   🌾 可收获植物: {harvestable_count} 个 (由收获队列管理)")
            logger.info(f"   💧 需要浇水: {need_water_count} 个 -> 生成 {water_tasks} 个浇水任务")
            logger.info(f"   🌿 杂草: {weed_count} 个 -> 生成 {weed_tasks} 个除草任务")
            logger.info(f"   🌱 空地: {empty_count} 个 -> 生成 {plant_tasks} 个播种任务")
            logger.info(f"   📊 总任务数: {len(self.task_queue)}")
    
    def _add_task(self, task_type, plant_id, priority, row=None, col=None):
        """添加任务到队列"""
        task = {
            'id': f"task_{int(time.time())}_{len(self.task_queue)}",
            'type': task_type,
            'plant_id': plant_id,
            'priority': priority,
            'row': row,
            'col': col,
            'created_at': datetime.now().isoformat(),
            'attempts': 0
        }
        self.task_queue.append(task)
    
    def _needs_watering(self, plant):
        """判断植物是否需要浇水"""
        # 检查是否是空地、杂草或已移除的植物
        if plant.get('is_empty') or plant.get('is_weed') or plant.get('is_removed') or plant.get('removed'):
            return False
        
        # 检查是否是种子（需要浇水才能发芽）
        if plant.get('is_seed'):
            return True
            
        # 检查是否是成熟植物（阶段3）
        if plant.get('growth_stage') == 3:
            return False  # 成熟植物不需要浇水
            
        # 检查土壤湿度（如果有数据）
        soil_moisture = plant.get('soil_moisture', 50)
        if soil_moisture < 50:
            return True
            
        # 检查上次浇水时间（如果有数据）
        last_watered = plant.get('last_watered')
        if last_watered and (time.time() - last_watered > 300):  # 5分钟没浇水
            return True
            
        # 对于有害虫的植物，优先浇水以帮助恢复健康
        if plant.get('has_pests', False) and plant.get('pests_count', 0) > 0:
            return True
            
        return False
    
    def _is_harvestable(self, plant):
        """判断植物是否可以收获"""
        # 检查是否是蔬菜、是否已移除
        if not plant.get('is_vegetable', False) or plant.get('is_removed') or plant.get('removed'):
            return False
            
        # 检查是否是种子或幼苗阶段
        if plant.get('is_seed'):
            return False
            
        # 检查生长阶段（server_game.py中只有阶段3才能收获）
        growth_stage = plant.get('growth_stage', 1)
        if growth_stage < 3:
            return False
            
        # 检查健康度（健康度过低可能无法收获）
        health = plant.get('health', 100)
        if health < 30:
            return False
            
        return True
    
    def _scan_harvestable_plants(self):
        """扫描所有可收获的植物，返回植物列表"""
        if not self.game_state:
            return []
        
        plants = self.game_state.get('plants', [])
        harvestable = []
        
        # 处理二维数组形式的植物数据
        if isinstance(plants, list) and plants and isinstance(plants[0], list):
            for row_idx, row in enumerate(plants):
                for col_idx, plant in enumerate(row):
                    if plant and self._is_harvestable(plant):
                        plant_info = {
                            'id': plant.get('id', f"plant_{row_idx}_{col_idx}"),
                            'row': row_idx,
                            'col': col_idx,
                            'type': plant.get('type', 'unknown'),
                            'health': plant.get('health', 100),
                            'position': plant.get('position', {})
                        }
                        harvestable.append(plant_info)
        else:
            # 一维数组
            for plant in plants:
                if plant and self._is_harvestable(plant):
                    plant_info = {
                        'id': plant.get('id'),
                        'row': plant.get('row'),
                        'col': plant.get('col'),
                        'type': plant.get('type', 'unknown'),
                        'health': plant.get('health', 100),
                        'position': plant.get('position', {})
                    }
                    harvestable.append(plant_info)
        
        logger.info(f"🔍 扫描完成：找到 {len(harvestable)} 个可收获植物")
        for p in harvestable:
            logger.info(f"   - {p['id']} ({p['row']}, {p['col']}): {p['type']}, 健康{p['health']}%")
        
        return harvestable
    
    def _execute_harvest_batch(self):
        """执行批量收获（使用贪心算法）"""
        if not self.harvest_queue:
            logger.info("✅ 收获队列为空，收获模式结束")
            self.harvest_mode_active = False
            return
        
        # 更新小车位置
        if self.game_state and 'cart' in self.game_state:
            self.current_cart_position = {
                'x': self.game_state['cart'].get('x', 0.0),
                'z': self.game_state['cart'].get('z', 0.0)
            }
        
        # 使用贪心算法：找到离当前位置最近的植物
        min_distance = float('inf')
        nearest_plant = None
        nearest_index = -1
        
        for idx, plant in enumerate(self.harvest_queue):
            pos = plant.get('position', {})
            plant_x = pos.get('x', 0.0)
            plant_z = pos.get('z', 0.0)
            
            # 计算距离
            distance = ((plant_x - self.current_cart_position['x']) ** 2 + 
                       (plant_z - self.current_cart_position['z']) ** 2) ** 0.5
            
            if distance < min_distance:
                min_distance = distance
                nearest_plant = plant
                nearest_index = idx
        
        if nearest_plant:
            logger.info(f"🎯 [贪心算法] 选择最近的植物: {nearest_plant['id']} ({nearest_plant['row']}, {nearest_plant['col']}), 距离: {min_distance:.2f}m")
            
            # 执行收获
            success = self._harvest_plant(nearest_plant['id'])
            
            if success:
                # 从队列中移除已收获的植物
                self.harvest_queue.pop(nearest_index)
                logger.info(f"✅ 收获成功！剩余 {len(self.harvest_queue)} 个植物待收获")
                self.stats['plants_harvested'] += 1
            else:
                # 收获失败，也从队列移除（避免死循环）
                logger.warning(f"⚠️ 收获失败: {nearest_plant['id']}, 从队列移除以继续")
                self.harvest_queue.pop(nearest_index)
        
        # 如果队列为空，结束收获模式
        if not self.harvest_queue:
            logger.info("🎉 所有植物收获完成！")
            self.harvest_mode_active = False
        
    def _find_plant_by_id(self, plant_id):
        """通过ID查找植物"""
        if not self.game_state:
            return None
            
        plants = self.game_state.get('plants', [])
        
        # 处理不同的数据结构
        if isinstance(plants, list):
            if plants and isinstance(plants[0], list):
                # 二维数组
                for row_idx, row in enumerate(plants):
                    for col_idx, plant in enumerate(row):
                        if plant and (plant.get('id') == plant_id or f"plant_{row_idx}_{col_idx}" == plant_id):
                            return plant
            else:
                # 一维数组
                for plant in plants:
                    if plant.get('id') == plant_id:
                        return plant
        elif isinstance(plants, dict):
            # 字典结构
            return plants.get(plant_id)
            
        return None
    
    def _move_cart_to_plant(self, plant_id, offset=0.0):
        """移动小车到植物所在格子（精确对齐，确保前端范围检查通过）"""
        try:
            # 获取植物信息
            plant = self._find_plant_by_id(plant_id)
            if not plant:
                logger.warning(f"找不到植物: {plant_id}")
                return False
            
            # 计算植物所在格子的中心位置（精确对齐）
            row = plant.get('row')
            col = plant.get('col')
            
            if row is None or col is None:
                logger.warning(f"植物缺少行列信息: {plant_id}")
                return False
            
            # 根据游戏网格计算精确位置
            # 为了满足前端的isCardinalDirection检查，小车需要在植物的相邻格子（上下左右）
            cell_size = 0.5
            offset_x = -2.0
            offset_z = -2.0
            grid_size = 8  # 8x8网格
            
            # 智能选择相邻格子（优先级：左->右->上->下）
            target_row = row
            target_col = col
            
            # 尝试左侧
            if col > 0:
                target_col = col - 1
                logger.info(f"🚗 选择植物 ({row}, {col}) 的左侧格子 ({target_row}, {target_col})")
            # 尝试右侧
            elif col < grid_size - 1:
                target_col = col + 1
                logger.info(f"🚗 选择植物 ({row}, {col}) 的右侧格子 ({target_row}, {target_col})")
            # 尝试上方
            elif row > 0:
                target_row = row - 1
                logger.info(f"🚗 选择植物 ({row}, {col}) 的上方格子 ({target_row}, {target_col})")
            # 尝试下方
            elif row < grid_size - 1:
                target_row = row + 1
                logger.info(f"🚗 选择植物 ({row}, {col}) 的下方格子 ({target_row}, {target_col})")
            else:
                # 极端情况：单个格子（不应该发生）
                logger.warning(f"⚠️ 无法找到相邻格子，小车将移动到植物位置")
            
            target_x = offset_x + target_col * cell_size + cell_size / 2
            target_z = offset_z + target_row * cell_size + cell_size / 2
            
            # 使用 /api/cart/move_to 精确移动
            response = requests.post(
                f"{self.server_url}/api/cart/move_to",
                json={
                    'x': target_x,
                    'z': target_z,
                    'speed': 5.0,
                    'smooth': True
                },
                timeout=5.0
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    # 等待小车移动完成（减少等待时间以提高效率）
                    time.sleep(0.5)  # 给小车一些移动时间
                    logger.info(f"✅ 小车已移动到目标位置")
                    return True
                else:
                    logger.warning(f"小车移动失败: {data.get('message', '未知错误')}")
            else:
                logger.warning(f"小车移动API返回错误: HTTP {response.status_code}")
            return False
        except requests.exceptions.Timeout:
            logger.warning("移动小车超时")
            return False
        except Exception as e:
            logger.warning(f"移动小车异常: {str(e)}")
            return False
    
    def _execute_next_task(self):
        """执行下一个优先级最高的任务"""
        with self.lock:
            if self.task_queue:
                self.current_task = self.task_queue.pop(0)
            else:
                return
        
        try:
            task_type = self.current_task['type']
            plant_id = self.current_task['plant_id']
            row = self.current_task.get('row')
            col = self.current_task.get('col')
            
            logger.info(f"⚡ 执行任务: {task_type.value} - 植物ID: {plant_id} - 位置: ({row}, {col})")
            
            # 更新当前任务到游戏状态
            if 'auto_farm' in self.game_state:
                self.game_state['auto_farm']['current_task'] = {
                    'type': task_type.value,
                    'priority': self.current_task['priority'].value,
                    'target': plant_id,
                    'row': row,
                    'col': col
                }
            
            # 通知游戏服务器当前执行的任务
            try:
                requests.post(
                    f"{self.server_url}/api/auto_farm/task_update",
                    json={
                        'task_type': task_type.value,
                        'row': row,
                        'col': col,
                        'status': 'executing'
                    },
                    timeout=2.0
                )
            except:
                pass  # 忽略通知失败
            
            # 发送任务开始事件到前端
            emit_socket_event('auto_farm_task_started', {
                'task_type': task_type.value,
                'plant_id': plant_id,
                'row': row,
                'col': col
            })
            
            if task_type == TaskType.WEED_REMOVAL:
                success = self._remove_weed(plant_id)
                # 发送除草事件通知前端
                emit_socket_event('auto_farm_action', {
                    'action': 'weed',
                    'plant_id': plant_id,
                    'row': row,
                    'col': col,
                    'success': success
                })
                if success:
                    self.stats['weeds_removed'] += 1
                    self.stats['tasks_completed'] += 1
                    # 更新游戏状态统计
                    if 'auto_farm' in self.game_state:
                        self.game_state['auto_farm']['stats']['weeds_removed'] += 1
            elif task_type == TaskType.PLANTING:
                success = self._plant_seed(plant_id)
                # 发送播种事件通知前端
                emit_socket_event('auto_farm_action', {
                    'action': 'plant',
                    'plant_id': plant_id,
                    'row': row,
                    'col': col,
                    'success': success
                })
                if success:
                    self.stats['plants_planted'] += 1
                    self.stats['tasks_completed'] += 1
                    # 更新游戏状态统计
                    if 'auto_farm' in self.game_state:
                        self.game_state['auto_farm']['stats']['seeds_planted'] += 1
            elif task_type == TaskType.WATERING:
                success = self._water_plant(plant_id)
                # 发送浇水事件通知前端
                emit_socket_event('auto_farm_action', {
                    'action': 'water',
                    'plant_id': plant_id,
                    'row': row,
                    'col': col,
                    'success': success
                })
                if success:
                    self.stats['plants_watered'] += 1
                    self.stats['tasks_completed'] += 1
                    # 更新游戏状态统计
                    if 'auto_farm' in self.game_state:
                        self.game_state['auto_farm']['stats']['waterings_done'] += 1
            elif task_type == TaskType.HARVEST:
                success = self._harvest_plant(plant_id)
                # 发送收获事件通知前端
                emit_socket_event('auto_farm_action', {
                    'action': 'harvest',
                    'plant_id': plant_id,
                    'row': row,
                    'col': col,
                    'success': success
                })
                if success:
                    self.stats['plants_harvested'] += 1
                    self.stats['tasks_completed'] += 1
                    # 更新游戏状态统计
                    if 'auto_farm' in self.game_state:
                        self.game_state['auto_farm']['stats']['plants_harvested'] += 1
            
            # 更新游戏状态并广播
            if 'auto_farm' in self.game_state:
                emit_socket_event('auto_farm_status_changed', {
                    'enabled': self.game_state['auto_farm']['enabled'],
                    'status': self.game_state['auto_farm']['status'],
                    'current_task': self.game_state['auto_farm']['current_task'],
                    'stats': self.game_state['auto_farm']['stats']
                })
                # 广播游戏状态更新
            broadcast_game_state()
            
            # 任务完成后暂停一小段时间，避免操作过快
            time.sleep(0.5)
            
        except Exception as e:
            logger.error(f"❌ 执行任务时出错: {str(e)}")
            self.stats['errors'] += 1
            # 发送错误事件到前端
            emit_socket_event('auto_farm_error', {
                'task_type': task_type.value if 'task_type' in locals() else None,
                'error': str(e)
            })
        finally:
            # 清除当前任务
            self.current_task = None
            if 'auto_farm' in self.game_state:
                self.game_state['auto_farm']['current_task'] = None
            
            # 通知游戏服务器任务完成
            try:
                requests.post(
                    f"{self.server_url}/api/auto_farm/task_update",
                    json={
                        'task_type': task_type.value if 'task_type' in locals() else None,
                        'row': row if 'row' in locals() else None,
                        'col': col if 'col' in locals() else None,
                        'status': 'completed'
                    },
                    timeout=2.0
                )
            except:
                pass  # 忽略通知失败
            
            # 发送任务完成事件到前端
            emit_socket_event('auto_farm_task_completed', {
                'task_type': task_type.value if 'task_type' in locals() else None,
                'plant_id': plant_id if 'plant_id' in locals() else None
            })
    
    def _remove_weed(self, plant_id):
        """使用激光除草并触发前端动画"""
        try:
            plant = self._find_plant_by_id(plant_id)
            if plant:
                row = plant.get('row')
                col = plant.get('col')
                
                logger.info(f"🌿 准备清除杂草: 植物ID {plant_id}, 位置({row}, {col})")
                
                # 🚗 先移动小车到植物附近（避免位置重叠）
                if not self._move_cart_to_plant(plant_id):
                    logger.warning(f"⚠️ 无法移动小车到植物 {plant_id}，尝试直接除草")
                
                # 发送除草操作开始事件
                emit_socket_event('auto_farm_operation_started', {
                    'operation': 'weed_removal',
                    'plant_id': plant_id,
                    'row': row,
                    'col': col
                })
                
                response = requests.post(
                    f"{self.server_url}/api/action/laser",
                    json={'plant_id': plant_id},
                    timeout=3.0
                )
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if data.get('success'):
                            print(f"✅ 成功清除杂草: {plant_id} ({row}, {col})")
                            # 更新本地游戏状态
                            if self.game_state:
                                self.game_state['score'] = self.game_state.get('score', 0) + 50
                                self.game_state['coins'] = self.game_state.get('coins', 0) + 10
                            
                            # 发送成功事件
                            emit_socket_event('auto_farm_operation_completed', {
                                'operation': 'weed_removal',
                                'plant_id': plant_id,
                                'row': row,
                                'col': col,
                                'success': True
                            })
                            # 触发激光动画
                            emit_socket_event('laser_fired', data)
                            
                            # 广播游戏状态更新
                            broadcast_game_state()
                            
                            return True
                        print(f"❌ 除草失败: {data.get('message', '未知错误')}")
                    except json.JSONDecodeError:
                        print(f"❌ 除草响应解析失败")
                else:
                    print(f"❌ 除草请求失败: HTTP {response.status_code}")
            else:
                print(f"❌ 未找到植物: {plant_id}")
            return False
        except requests.exceptions.Timeout:
            print(f"❌ 除草请求超时")
            # 发送错误事件
            emit_socket_event('auto_farm_operation_error', {
                'operation': 'weed_removal',
                'plant_id': plant_id,
                'error': '请求超时'
            })
            return False
        except Exception as e:
            print(f"❌ 除草操作出错: {str(e)}")
            # 发送错误事件
            emit_socket_event('auto_farm_operation_error', {
                'operation': 'weed_removal',
                'plant_id': plant_id,
                'error': str(e)
            })
            return False
    
    def _plant_seed(self, plant_id):
        """播种"""
        try:
            plant = self._find_plant_by_id(plant_id)
            if plant:
                # 获取行列位置信息
                row = plant.get('row')
                col = plant.get('col')
                
                # 验证行列信息
                if row is None or col is None:
                    print(f"❌ 植物缺少位置信息，无法播种: {plant_id}")
                    return False
                    
                # 检查金币是否足够（server_game.py中种子需要5金币）
                if self.game_state.get('coins', 0) < 5:
                    print(f"❌ 金币不足，无法播种（需要5金币，当前: {self.game_state.get('coins', 0)}）")
                    return False
                    
                # 构建请求参数
                request_data = {'row': row, 'col': col}
                logger.info(f"🌱 准备播种: 位置({row}, {col})")
                
                # 🚗 先移动小车到植物附近（避免位置重叠）
                if not self._move_cart_to_plant(plant_id):
                    logger.warning(f"⚠️ 无法移动小车到植物 {plant_id}，尝试直接播种")
                
                # 发送播种操作开始事件
                emit_socket_event('auto_farm_operation_started', {
                    'operation': 'plant_seed',
                    'row': row,
                    'col': col,
                    'plant_id': plant_id
                })
                
                # 发送请求到正确的API端点
                response = requests.post(
                    f"{self.server_url}/api/action/plant",
                    json=request_data,
                    timeout=3.0
                )
                
                # 处理响应
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if data.get('success'):
                            print(f"✅ 成功播种: {plant_id} ({row}, {col})")
                            # 更新本地游戏状态
                            if self.game_state:
                                self.game_state['coins'] = self.game_state.get('coins', 0) - 5
                                self.game_state['score'] = self.game_state.get('score', 0) + 10
                            
                            # 发送成功事件
                            emit_socket_event('auto_farm_operation_completed', {
                                'operation': 'plant_seed',
                                'row': row,
                                'col': col,
                                'plant_id': plant_id,
                                'success': True
                            })
                            # 广播植物状态更新
                            if 'plant' in data:
                                emit_socket_event('plant_updated', data['plant'])
                            # 广播游戏状态更新
                            broadcast_game_state()
                            
                            return True
                        print(f"❌ 播种失败: {data.get('message', '未知错误')}")
                        # 发送失败事件
                        emit_socket_event('auto_farm_operation_completed', {
                            'operation': 'plant_seed',
                            'row': row,
                            'col': col,
                            'plant_id': plant_id,
                            'success': False,
                            'error': data.get('message', '未知错误')
                        })
                    except json.JSONDecodeError:
                        print(f"❌ 播种响应解析失败")
                        # 发送解析错误事件
                        emit_socket_event('auto_farm_operation_error', {
                            'operation': 'plant_seed',
                            'row': row,
                            'col': col,
                            'plant_id': plant_id,
                            'error': '响应解析失败'
                        })
                else:
                    print(f"❌ 播种请求失败: HTTP {response.status_code}")
                    # 发送请求失败事件
                    emit_socket_event('auto_farm_operation_error', {
                        'operation': 'plant_seed',
                        'row': row,
                        'col': col,
                        'plant_id': plant_id,
                        'error': f'HTTP错误: {response.status_code}'
                    })
            else:
                print(f"❌ 未找到植物: {plant_id}")
            return False
        except requests.exceptions.Timeout:
            print(f"❌ 播种请求超时")
            # 发送超时事件
            emit_socket_event('auto_farm_operation_error', {
                'operation': 'plant_seed',
                'row': row if 'row' in locals() else None,
                'col': col if 'col' in locals() else None,
                'plant_id': plant_id,
                'error': '请求超时'
            })
            return False
        except Exception as e:
            print(f"❌ 播种操作出错: {str(e)}")
            # 发送异常事件
            emit_socket_event('auto_farm_operation_error', {
                'operation': 'plant_seed',
                'row': row if 'row' in locals() else None,
                'col': col if 'col' in locals() else None,
                'plant_id': plant_id,
                'error': str(e)
            })
            return False
    
    def _water_plant(self, plant_id):
        """浇水"""
        try:
            plant = self._find_plant_by_id(plant_id)
            if plant:
                row = plant.get('row')
                col = plant.get('col')
                
                logger.info(f"💧 准备浇水: 植物ID {plant_id}, 位置({row}, {col})")
                
                # 🚗 先移动小车到植物附近（避免位置重叠）
                if not self._move_cart_to_plant(plant_id):
                    logger.warning(f"⚠️ 无法移动小车到植物 {plant_id}，尝试直接浇水")
                
                # 发送浇水操作开始事件
                emit_socket_event('auto_farm_operation_started', {
                    'operation': 'water_plant',
                    'plant_id': plant_id,
                    'row': row,
                    'col': col
                })
                
                response = requests.post(
                    f"{self.server_url}/api/action/water",
                    json={'plant_id': plant_id},
                    timeout=3.0
                )
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if data.get('success'):
                            print(f"✅ 成功浇水: {plant_id} ({row}, {col})")
                            # 更新本地游戏状态中的分数
                            score_change = 10 if data.get('stage_changed') else 5
                            if self.game_state:
                                self.game_state['score'] = self.game_state.get('score', 0) + score_change
                            
                            # 发送成功事件
                            emit_socket_event('auto_farm_operation_completed', {
                                'operation': 'water_plant',
                                'plant_id': plant_id,
                                'row': row,
                                'col': col,
                                'success': True,
                                'growth_stage': data.get('growth_stage')
                            })
                            # 如果种子发芽，通知前端
                            if data.get('germinated'):
                                emit_socket_event('seed_germinated', data)
                            # 广播植物状态更新
                            emit_socket_event('plant_updated', plant)
                            
                            return True
                        print(f"❌ 浇水失败: {data.get('message', '未知错误')}")
                        # 发送失败事件
                        emit_socket_event('auto_farm_operation_completed', {
                            'operation': 'water_plant',
                            'plant_id': plant_id,
                            'row': row,
                            'col': col,
                            'success': False,
                            'error': data.get('message', '未知错误')
                        })
                    except json.JSONDecodeError:
                        print(f"❌ 浇水响应解析失败")
                        # 发送解析错误事件
                        emit_socket_event('auto_farm_operation_error', {
                            'operation': 'water_plant',
                            'plant_id': plant_id,
                            'row': row,
                            'col': col,
                            'error': '响应解析失败'
                        })
                else:
                    print(f"❌ 浇水请求失败: HTTP {response.status_code}")
                    # 发送请求失败事件
                    emit_socket_event('auto_farm_operation_error', {
                        'operation': 'water_plant',
                        'plant_id': plant_id,
                        'row': row,
                        'col': col,
                        'error': f'HTTP错误: {response.status_code}'
                    })
            else:
                print(f"❌ 未找到植物: {plant_id}")
            return False
        except requests.exceptions.Timeout:
            print(f"❌ 浇水请求超时")
            # 发送超时事件
            emit_socket_event('auto_farm_operation_error', {
                'operation': 'water_plant',
                'plant_id': plant_id,
                'error': '请求超时'
            })
            return False
        except Exception as e:
            print(f"❌ 浇水操作出错: {str(e)}")
            # 发送异常事件
            emit_socket_event('auto_farm_operation_error', {
                'operation': 'water_plant',
                'plant_id': plant_id,
                'error': str(e)
            })
            return False
    
    def _harvest_plant(self, plant_id):
        """收获成熟植物"""
        try:
            plant = self._find_plant_by_id(plant_id)
            if plant:
                row = plant.get('row')
                col = plant.get('col')
                
                # 确保植物可以收获
                if not self._is_harvestable(plant):
                    print(f"❌ 植物不可收获: {plant_id}")
                    return False
                    
                logger.info(f"🚜 准备收获: 植物ID {plant_id}, 位置({row}, {col})")
                
                # 🚗 先移动小车到植物附近（避免位置重叠）
                if not self._move_cart_to_plant(plant_id):
                    logger.warning(f"⚠️ 无法移动小车到植物 {plant_id}，尝试直接收获")
                
                # 发送收获操作开始事件
                emit_socket_event('auto_farm_operation_started', {
                    'operation': 'harvest_plant',
                    'plant_id': plant_id,
                    'row': row,
                    'col': col
                })
                
                response = requests.post(
                    f"{self.server_url}/api/action/harvest",
                    json={'plant_id': plant_id},
                    timeout=3.0
                )
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if data.get('success'):
                            coins_earned = data.get('coins_earned', 20)  # 默认20金币
                            logger.info(f"✅ 成功收获: {plant_id} ({row}, {col}) - 获得 {coins_earned} 金币")
                            print(f"✅ 成功收获: {plant_id} ({row}, {col}) - 获得 {coins_earned} 金币")
                            # 更新本地游戏状态
                            if self.game_state:
                                self.game_state['coins'] = self.game_state.get('coins', 0) + coins_earned
                                self.game_state['score'] = self.game_state.get('score', 0) + coins_earned
                            
                            # 发送成功事件
                            emit_socket_event('auto_farm_operation_completed', {
                                'operation': 'harvest_plant',
                                'plant_id': plant_id,
                                'row': row,
                                'col': col,
                                'success': True,
                                'coins_earned': coins_earned,
                                'fruit_count': data.get('fruit_count', 0),
                                'quality': data.get('quality', '普通')
                            })
                            # 广播收获成功事件，触发动画
                            emit_socket_event('plant_harvested', {
                                'plant_id': plant_id,
                                'row': row,
                                'col': col,
                                'coins_earned': coins_earned,
                                'message': data.get('message', '')
                            })
                            # 更新植物状态为空地
                            updated_plant = {
                                'id': plant_id,
                                'row': row,
                                'col': col,
                                'is_empty': True,
                                'is_removed': False
                            }
                            emit_socket_event('plant_updated', updated_plant)
                            broadcast_game_state()
                            
                            return True
                        error_msg = data.get('message', '未知错误')
                        logger.error(f"❌ 收获失败: {plant_id} ({row}, {col}) - {error_msg}")
                        print(f"❌ 收获失败: {plant_id} ({row}, {col}) - {error_msg}")
                        # 发送失败事件
                        emit_socket_event('auto_farm_operation_completed', {
                            'operation': 'harvest_plant',
                            'plant_id': plant_id,
                            'row': row,
                            'col': col,
                            'success': False,
                            'error': data.get('message', '未知错误')
                        })
                    except json.JSONDecodeError:
                        print(f"❌ 收获响应解析失败")
                        # 发送解析错误事件
                        emit_socket_event('auto_farm_operation_error', {
                            'operation': 'harvest_plant',
                            'plant_id': plant_id,
                            'row': row,
                            'col': col,
                            'error': '响应解析失败'
                        })
                else:
                    print(f"❌ 收获请求失败: HTTP {response.status_code}")
                    # 发送请求失败事件
                    emit_socket_event('auto_farm_operation_error', {
                        'operation': 'harvest_plant',
                        'plant_id': plant_id,
                        'row': row,
                        'col': col,
                        'error': f'HTTP错误: {response.status_code}'
                    })
            else:
                print(f"❌ 未找到植物: {plant_id}")
            return False
        except requests.exceptions.Timeout:
            print(f"❌ 收获请求超时")
            # 发送超时事件
            emit_socket_event('auto_farm_operation_error', {
                'operation': 'harvest_plant',
                'plant_id': plant_id,
                'error': '请求超时'
            })
            return False
        except Exception as e:
            print(f"❌ 收获操作出错: {str(e)}")
            # 发送异常事件
            emit_socket_event('auto_farm_operation_error', {
                'operation': 'harvest_plant',
                'plant_id': plant_id,
                'error': str(e)
            })
            return False
    
    def print_summary(self):
        """打印自动化系统运行摘要"""
        logging.info("\n" + "="*60)
        logging.info("📊 智能农场自动化系统运行摘要")
        logging.info("="*60)
        logging.info(f"🔄 总运行周期: {self.stats['cycles']}")
        logging.info(f"✅ 完成任务数: {self.stats['tasks_completed']}")
        logging.info(f"🌿 清除杂草数: {self.stats['weeds_removed']}")
        logging.info(f"🌱 种植植物数: {self.stats['plants_planted']}")
        logging.info(f"💧 浇水次数: {self.stats['plants_watered']}")
        logging.info(f"🚜 收获次数: {self.stats['plants_harvested']}")
        logging.info(f"❌ 错误次数: {self.stats['errors']}")
        logging.info("="*60)
        
        # 如果有游戏状态，输出额外的系统状态
        if self.game_state and 'auto_farm' in self.game_state:
            logging.info("🔄 游戏状态中记录的统计:")
            game_stats = self.game_state['auto_farm']['stats']
            for key, value in game_stats.items():
                logging.info(f"  - {key}: {value}")

if __name__ == "__main__":
    # 测试运行自动化控制器
    controller = AutoFarmController()
    controller.start()
