#!/usr/bin/env python3
"""
智能农场自动化任务执行模块
负责控制机器人执行具体的农业任务
"""
import time
import json
import requests
from typing import Dict, List, Tuple, Optional, Any
import random

# API相关配置
API_BASE_URL = "http://localhost:7070"
API_TIMEOUT = 5  # 5秒超时

class TaskExecutor:
    """
    任务执行器
    负责执行各种农业任务
    """
    def __init__(self, robot_state: Dict[str, Any], plants: List[List[Dict[str, Any]]]):
        """
        初始化任务执行器
        
        Args:
            robot_state: 机器人状态信息
            plants: 植物信息二维数组
        """
        self.robot_state = robot_state
        self.plants = plants
        self.current_task = None  # 当前执行的任务
        self.execution_history = []  # 执行历史记录
        self.task_success_rate = {}
        self.energy_consumption_rates = {
            'move': 0.5,  # 移动能耗率
            'sow': 2.0,   # 播种能耗率
            'water': 1.0, # 浇水能耗率
            'weed': 1.5,  # 除草能耗率
            'harvest': 3.0, # 收获能耗率
            'scan': 0.2   # 扫描能耗率
        }
    
    def update_state(self, robot_state: Dict[str, Any], plants: List[List[Dict[str, Any]]]):
        """
        更新状态信息
        
        Args:
            robot_state: 更新后的机器人状态
            plants: 更新后的植物信息
        """
        self.robot_state = robot_state
        self.plants = plants
    
    def execute_sow_task(self, row: int, col: int, plant_type: str = "wheat") -> Dict[str, Any]:
        """
        执行播种任务
        
        Args:
            row: 行坐标
            col: 列坐标
            plant_type: 植物类型
            
        Returns:
            任务执行结果
        """
        start_time = time.time()
        energy_cost = self.energy_consumption_rates['sow']
        
        try:
            # 尝试通过API执行播种
            api_url = f"{API_BASE_URL}/api/sow"
            payload = {
                "row": row,
                "col": col,
                "plant_type": plant_type
            }
            
            response = requests.post(api_url, json=payload, timeout=API_TIMEOUT)
            
            if response.status_code == 200:
                api_result = response.json()
                if api_result.get('success'):
                    # 更新本地状态
                    self.robot_state['energy'] -= energy_cost
                    
                    # 构建结果
                    result = {
                        'success': True,
                        'message': f"成功播种 {plant_type}",
                        'energy_cost': energy_cost,
                        'time_taken': time.time() - start_time,
                        'row': row,
                        'col': col,
                        'task_type': 'sow',
                        'api_response': api_result
                    }
                    self.log_execution(result)
                    return result
                else:
                    # API返回失败
                    result = {
                        'success': False,
                        'message': f"API执行失败: {api_result.get('message', '未知错误')}",
                        'energy_cost': 0,
                        'time_taken': time.time() - start_time,
                        'row': row,
                        'col': col,
                        'task_type': 'sow',
                        'api_response': api_result
                    }
                    self.log_execution(result)
                    return result
            else:
                raise Exception(f"API请求失败，状态码: {response.status_code}")
        
        except Exception as e:
            # API调用失败，尝试本地模拟执行作为备用
            print(f"API调用失败，尝试本地执行: {str(e)}")
            
            # 检查能量是否足够
            if self.robot_state['energy'] < energy_cost:
                result = {
                    'success': False,
                    'message': "能量不足，无法执行播种任务",
                    'energy_cost': 0,
                    'time_taken': time.time() - start_time,
                    'row': row,
                    'col': col,
                    'task_type': 'sow'
                }
                self.log_execution(result)
                return result
            
            # 检查坐标是否有效
            if not (0 <= row < len(self.plants) and 0 <= col < len(self.plants[0])):
                result = {
                    'success': False,
                    'message': "坐标无效",
                    'energy_cost': 0,
                    'time_taken': time.time() - start_time,
                    'row': row,
                    'col': col,
                    'task_type': 'sow'
                }
                self.log_execution(result)
                return result
            
            # 检查该位置是否已有植物
            current_plant = self.plants[row][col]
            if current_plant and current_plant.get('state') not in ['dead', 'harvested']:
                result = {
                    'success': False,
                    'message': "该位置已有植物",
                    'energy_cost': 0,
                    'time_taken': time.time() - start_time,
                    'row': row,
                    'col': col,
                    'task_type': 'sow'
                }
                self.log_execution(result)
                return result
            
            # 执行本地播种模拟
            self.robot_state['energy'] -= energy_cost
            
            # 创建新植物
            new_plant = {
                'type': plant_type,
                'state': 'seed',
                'age': 0,
                'health': 100,
                'growth_stage': 0,
                'last_watered': time.time(),
                'weed_count': 0,
                'position': {'row': row, 'col': col}
            }
            
            self.plants[row][col] = new_plant
            
            result = {
                'success': True,
                'message': f"成功在本地模拟播种 {plant_type}",
                'energy_cost': energy_cost,
                'time_taken': time.time() - start_time,
                'row': row,
                'col': col,
                'task_type': 'sow',
                'plant_info': new_plant
            }
            self.log_execution(result)
            return result
    
    def execute_water_task(self, row: int, col: int) -> Dict[str, Any]:
        """
        执行浇水任务
        
        Args:
            row: 行坐标
            col: 列坐标
            
        Returns:
            任务执行结果
        """
        start_time = time.time()
        energy_cost = self.energy_consumption_rates['water']
        
        try:
            # 尝试通过API执行浇水
            api_url = f"{API_BASE_URL}/api/water"
            payload = {
                "row": row,
                "col": col
            }
            
            response = requests.post(api_url, json=payload, timeout=API_TIMEOUT)
            
            if response.status_code == 200:
                api_result = response.json()
                if api_result.get('success'):
                    # 更新本地状态
                    self.robot_state['energy'] -= energy_cost
                    
                    # 构建结果
                    result = {
                        'success': True,
                        'message': "成功浇水",
                        'energy_cost': energy_cost,
                        'time_taken': time.time() - start_time,
                        'row': row,
                        'col': col,
                        'task_type': 'water',
                        'api_response': api_result
                    }
                    self.log_execution(result)
                    return result
                else:
                    # API返回失败
                    result = {
                        'success': False,
                        'message': f"API执行失败: {api_result.get('message', '未知错误')}",
                        'energy_cost': 0,
                        'time_taken': time.time() - start_time,
                        'row': row,
                        'col': col,
                        'task_type': 'water',
                        'api_response': api_result
                    }
                    self.log_execution(result)
                    return result
            else:
                raise Exception(f"API请求失败，状态码: {response.status_code}")
        
        except Exception as e:
            # API调用失败，尝试本地模拟执行作为备用
            print(f"API调用失败，尝试本地执行: {str(e)}")
            
            # 检查能量是否足够
            if self.robot_state['energy'] < energy_cost:
                result = {
                    'success': False,
                    'message': "能量不足，无法执行浇水任务",
                    'energy_cost': 0,
                    'time_taken': time.time() - start_time,
                    'row': row,
                    'col': col,
                    'task_type': 'water'
                }
                self.log_execution(result)
                return result
            
            # 检查坐标是否有效
            if not (0 <= row < len(self.plants) and 0 <= col < len(self.plants[0])):
                result = {
                    'success': False,
                    'message': "坐标无效",
                    'energy_cost': 0,
                    'time_taken': time.time() - start_time,
                    'row': row,
                    'col': col,
                    'task_type': 'water'
                }
                self.log_execution(result)
                return result
            
            # 检查该位置是否有植物需要浇水
            plant = self.plants[row][col]
            if not plant or plant.get('state') in ['dead', 'harvested']:
                result = {
                    'success': False,
                    'message': "该位置没有需要浇水的植物",
                    'energy_cost': 0,
                    'time_taken': time.time() - start_time,
                    'row': row,
                    'col': col,
                    'task_type': 'water'
                }
                self.log_execution(result)
                return result
            
            # 执行本地浇水模拟
            self.robot_state['energy'] -= energy_cost
            
            # 更新植物状态
            plant['last_watered'] = time.time()
            plant['health'] = min(100, plant['health'] + 10)  # 浇水增加植物健康值
            
            result = {
                'success': True,
                'message': "成功在本地模拟浇水",
                'energy_cost': energy_cost,
                'time_taken': time.time() - start_time,
                'row': row,
                'col': col,
                'task_type': 'water',
                'plant_info': plant
            }
            self.log_execution(result)
            return result
    
    def execute_weed_task(self, row: int, col: int) -> Dict[str, Any]:
        """
        执行除草任务
        
        Args:
            row: 行坐标
            col: 列坐标
            
        Returns:
            任务执行结果
        """
        start_time = time.time()
        energy_cost = self.energy_consumption_rates['weed']
        
        try:
            # 尝试通过API执行激光除草
            api_url = f"{API_BASE_URL}/api/laser"
            payload = {
                "row": row,
                "col": col
            }
            
            response = requests.post(api_url, json=payload, timeout=API_TIMEOUT)
            
            if response.status_code == 200:
                api_result = response.json()
                if api_result.get('success'):
                    # 更新本地状态
                    self.robot_state['energy'] -= energy_cost
                    
                    # 构建结果
                    result = {
                        'success': True,
                        'message': "成功使用激光除草",
                        'energy_cost': energy_cost,
                        'time_taken': time.time() - start_time,
                        'row': row,
                        'col': col,
                        'task_type': 'weed',
                        'api_response': api_result
                    }
                    self.log_execution(result)
                    return result
                else:
                    # API返回失败
                    result = {
                        'success': False,
                        'message': f"API执行失败: {api_result.get('message', '未知错误')}",
                        'energy_cost': 0,
                        'time_taken': time.time() - start_time,
                        'row': row,
                        'col': col,
                        'task_type': 'weed',
                        'api_response': api_result
                    }
                    self.log_execution(result)
                    return result
            else:
                raise Exception(f"API请求失败，状态码: {response.status_code}")
        
        except Exception as e:
            # API调用失败，尝试本地模拟执行作为备用
            print(f"API调用失败，尝试本地执行: {str(e)}")
            
            # 检查能量是否足够
            if self.robot_state['energy'] < energy_cost:
                result = {
                    'success': False,
                    'message': "能量不足，无法执行除草任务",
                    'energy_cost': 0,
                    'time_taken': time.time() - start_time,
                    'row': row,
                    'col': col,
                    'task_type': 'weed'
                }
                self.log_execution(result)
                return result
            
            # 检查坐标是否有效
            if not (0 <= row < len(self.plants) and 0 <= col < len(self.plants[0])):
                result = {
                    'success': False,
                    'message': "坐标无效",
                    'energy_cost': 0,
                    'time_taken': time.time() - start_time,
                    'row': row,
                    'col': col,
                    'task_type': 'weed'
                }
                self.log_execution(result)
                return result
            
            # 检查该位置是否有植物需要除草
            plant = self.plants[row][col]
            if not plant or plant.get('state') in ['dead', 'harvested']:
                result = {
                    'success': False,
                    'message': "该位置没有需要除草的植物",
                    'energy_cost': 0,
                    'time_taken': time.time() - start_time,
                    'row': row,
                    'col': col,
                    'task_type': 'weed'
                }
                self.log_execution(result)
                return result
            
            # 执行本地除草模拟
            self.robot_state['energy'] -= energy_cost
            
            # 更新植物状态
            if plant.get('weed_count', 0) > 0:
                plant['weed_count'] = 0  # 清除所有杂草
                plant['health'] = min(100, plant['health'] + 5)  # 除草增加植物健康值
                message = "成功在本地模拟清除所有杂草"
            else:
                message = "该位置没有杂草"
            
            result = {
                'success': True,
                'message': message,
                'energy_cost': energy_cost,
                'time_taken': time.time() - start_time,
                'row': row,
                'col': col,
                'task_type': 'weed',
                'plant_info': plant
            }
            self.log_execution(result)
            return result
    
    def execute_harvest_task(self, row: int, col: int) -> Dict[str, Any]:
        """
        执行收获任务
        
        Args:
            row: 行坐标
            col: 列坐标
            
        Returns:
            任务执行结果
        """
        start_time = time.time()
        energy_cost = self.energy_consumption_rates['harvest']
        
        try:
            # 尝试通过API执行收获
            api_url = f"{API_BASE_URL}/api/harvest"
            payload = {
                "row": row,
                "col": col
            }
            
            response = requests.post(api_url, json=payload, timeout=API_TIMEOUT)
            
            if response.status_code == 200:
                api_result = response.json()
                if api_result.get('success'):
                    # 更新本地状态
                    self.robot_state['energy'] -= energy_cost
                    # 更新金币（如果API返回了金币奖励）
                    if 'coins_earned' in api_result:
                        self.robot_state['coins'] += api_result['coins_earned']
                    
                    # 构建结果
                    result = {
                        'success': True,
                        'message': "成功收获",
                        'energy_cost': energy_cost,
                        'time_taken': time.time() - start_time,
                        'row': row,
                        'col': col,
                        'task_type': 'harvest',
                        'api_response': api_result,
                        'yield': api_result.get('yield', 0),
                        'coins_earned': api_result.get('coins_earned', 0)
                    }
                    self.log_execution(result)
                    return result
                else:
                    # API返回失败
                    result = {
                        'success': False,
                        'message': f"API执行失败: {api_result.get('message', '未知错误')}",
                        'energy_cost': 0,
                        'time_taken': time.time() - start_time,
                        'row': row,
                        'col': col,
                        'task_type': 'harvest',
                        'api_response': api_result
                    }
                    self.log_execution(result)
                    return result
            else:
                raise Exception(f"API请求失败，状态码: {response.status_code}")
        
        except Exception as e:
            # API调用失败，尝试本地模拟执行作为备用
            print(f"API调用失败，尝试本地执行: {str(e)}")
            
            # 检查能量是否足够
            if self.robot_state['energy'] < energy_cost:
                result = {
                    'success': False,
                    'message': "能量不足，无法执行收获任务",
                    'energy_cost': 0,
                    'time_taken': time.time() - start_time,
                    'row': row,
                    'col': col,
                    'task_type': 'harvest'
                }
                self.log_execution(result)
                return result
            
            # 检查坐标是否有效
            if not (0 <= row < len(self.plants) and 0 <= col < len(self.plants[0])):
                result = {
                    'success': False,
                    'message': "坐标无效",
                    'energy_cost': 0,
                    'time_taken': time.time() - start_time,
                    'row': row,
                    'col': col,
                    'task_type': 'harvest'
                }
                self.log_execution(result)
                return result
            
            # 检查该位置是否有成熟的植物可以收获
            plant = self.plants[row][col]
            if not plant or plant.get('state') in ['dead', 'harvested']:
                result = {
                    'success': False,
                    'message': "该位置没有可以收获的植物",
                    'energy_cost': 0,
                    'time_taken': time.time() - start_time,
                    'row': row,
                    'col': col,
                    'task_type': 'harvest'
                }
                self.log_execution(result)
                return result
            
            # 检查植物是否成熟
            if plant.get('growth_stage', 0) < 3 or plant.get('state') != 'growing':
                result = {
                    'success': False,
                    'message': "植物尚未成熟",
                    'energy_cost': 0,
                    'time_taken': time.time() - start_time,
                    'row': row,
                    'col': col,
                    'task_type': 'harvest'
                }
                self.log_execution(result)
                return result
            
            # 执行本地收获模拟
            self.robot_state['energy'] -= energy_cost
            
            # 根据植物类型和健康值计算产量
            plant_type = plant.get('type', 'wheat')
            health = plant.get('health', 100)
            base_yield = 10  # 基础产量
            
            # 健康值影响产量，健康值越高，产量越高
            yield_amount = int(base_yield * (health / 100) * (0.9 + random.random() * 0.2))  # 添加一些随机波动
            
            # 更新机器人的收获计数和金币
            if 'harvest_count' not in self.robot_state:
                self.robot_state['harvest_count'] = {}
            
            if plant_type not in self.robot_state['harvest_count']:
                self.robot_state['harvest_count'][plant_type] = 0
            
            self.robot_state['harvest_count'][plant_type] += yield_amount
            
            # 增加金币奖励（每收获1个产品获得1个金币）
            self.robot_state['coins'] += yield_amount
            
            # 更新植物状态为已收获
            plant['state'] = 'harvested'
            plant['yield'] = yield_amount
            
            result = {
                'success': True,
                'message': f"成功在本地模拟收获 {plant_type}，产量：{yield_amount}",
                'energy_cost': energy_cost,
                'time_taken': time.time() - start_time,
                'row': row,
                'col': col,
                'task_type': 'harvest',
                'plant_info': plant,
                'yield': yield_amount,
                'coins_earned': yield_amount
            }
            self.log_execution(result)
            return result
    
    def execute_scan_task(self, row: int, col: int) -> Dict[str, Any]:
        """
        执行扫描任务，获取植物详细信息
        
        Args:
            row: 行坐标
            col: 列坐标
            
        Returns:
            任务执行结果，包含植物详细信息
        """
        start_time = time.time()
        energy_cost = self.energy_consumption_rates['scan']
        
        try:
            # 尝试通过API执行扫描
            api_url = f"{API_BASE_URL}/api/scan"
            payload = {
                "row": row,
                "col": col
            }
            
            response = requests.post(api_url, json=payload, timeout=API_TIMEOUT)
            
            if response.status_code == 200:
                api_result = response.json()
                if api_result.get('success'):
                    # 更新本地状态
                    self.robot_state['energy'] -= energy_cost
                    
                    # 构建结果
                    result = {
                        'success': True,
                        'message': "成功扫描",
                        'energy_cost': energy_cost,
                        'time_taken': time.time() - start_time,
                        'row': row,
                        'col': col,
                        'task_type': 'scan',
                        'plant_info': api_result.get('plant_info', None),
                        'care_recommendations': api_result.get('care_recommendations', []),
                        'api_response': api_result
                    }
                    self.log_execution(result)
                    return result
                else:
                    # API返回失败
                    result = {
                        'success': False,
                        'message': f"API执行失败: {api_result.get('message', '未知错误')}",
                        'energy_cost': 0,
                        'time_taken': time.time() - start_time,
                        'row': row,
                        'col': col,
                        'task_type': 'scan',
                        'api_response': api_result
                    }
                    self.log_execution(result)
                    return result
            else:
                raise Exception(f"API请求失败，状态码: {response.status_code}")
        
        except Exception as e:
            # API调用失败，尝试本地模拟执行作为备用
            print(f"API调用失败，尝试本地执行: {str(e)}")
            
            # 检查能量是否足够
            if self.robot_state['energy'] < energy_cost:
                result = {
                    'success': False,
                    'message': "能量不足，无法执行扫描任务",
                    'energy_cost': 0,
                    'time_taken': time.time() - start_time,
                    'row': row,
                    'col': col,
                    'task_type': 'scan'
                }
                self.log_execution(result)
                return result
            
            # 检查坐标是否有效
            if not (0 <= row < len(self.plants) and 0 <= col < len(self.plants[0])):
                result = {
                    'success': False,
                    'message': "坐标无效",
                    'energy_cost': 0,
                    'time_taken': time.time() - start_time,
                    'row': row,
                    'col': col,
                    'task_type': 'scan'
                }
                self.log_execution(result)
                return result
            
            # 执行本地扫描模拟
            self.robot_state['energy'] -= energy_cost
            
            # 获取植物信息
            plant = self.plants[row][col]
            
            # 分析植物状态，生成护理建议
            care_recommendations = []
            if plant and plant.get('state') == 'growing':
                # 检查是否需要浇水（假设超过30秒没浇水需要浇水）
                time_since_watered = time.time() - plant.get('last_watered', 0)
                if time_since_watered > 30:
                    care_recommendations.append("需要浇水")
                
                # 检查是否需要除草
                if plant.get('weed_count', 0) > 0:
                    care_recommendations.append("需要除草")
                
                # 检查植物健康状况
                health = plant.get('health', 100)
                if health < 50:
                    care_recommendations.append("植物健康状况不佳")
            
            result = {
                'success': True,
                'message': "在本地模拟扫描完成",
                'energy_cost': energy_cost,
                'time_taken': time.time() - start_time,
                'row': row,
                'col': col,
                'task_type': 'scan',
                'plant_info': plant,
                'care_recommendations': care_recommendations
            }
            self.log_execution(result)
            return result
    
    def execute_move_task(self, target_x: float, target_z: float, 
                         tolerance: float = 0.1) -> Dict[str, Any]:
        """
        执行移动任务
        
        Args:
            target_x: 目标X坐标
            target_z: 目标Z坐标
            tolerance: 到达目标的容差
            
        Returns:
            任务执行结果
        """
        start_time = time.time()
        
        # 计算移动距离
        current_x = self.robot_state.get('x', 0)
        current_z = self.robot_state.get('z', 0)
        
        distance = ((target_x - current_x) ** 2 + (target_z - current_z) ** 2) ** 0.5
        
        # 计算能耗
        energy_cost = min(self.energy_consumption_rates['move'] * distance, 
                         self.robot_state['energy'])
        
        try:
            # 尝试通过API执行移动
            api_url = f"{API_BASE_URL}/api/move"
            payload = {
                "target_x": target_x,
                "target_z": target_z
            }
            
            response = requests.post(api_url, json=payload, timeout=API_TIMEOUT)
            
            if response.status_code == 200:
                api_result = response.json()
                if api_result.get('success'):
                    # 更新本地状态
                    self.robot_state['energy'] -= energy_cost
                    self.robot_state['x'] = target_x
                    self.robot_state['z'] = target_z
                    
                    # 构建结果
                    result = {
                        'success': True,
                        'message': "成功移动到目标位置",
                        'energy_cost': energy_cost,
                        'time_taken': time.time() - start_time,
                        'distance': distance,
                        'target_x': target_x,
                        'target_z': target_z,
                        'task_type': 'move',
                        'api_response': api_result
                    }
                    self.log_execution(result)
                    return result
                else:
                    # API返回失败
                    result = {
                        'success': False,
                        'message': f"API执行失败: {api_result.get('message', '未知错误')}",
                        'energy_cost': 0,
                        'time_taken': time.time() - start_time,
                        'distance': distance,
                        'target_x': target_x,
                        'target_z': target_z,
                        'task_type': 'move',
                        'api_response': api_result
                    }
                    self.log_execution(result)
                    return result
            else:
                raise Exception(f"API请求失败，状态码: {response.status_code}")
        
        except Exception as e:
            # API调用失败，尝试本地模拟执行作为备用
            print(f"API调用失败，尝试本地执行: {str(e)}")
            
            # 检查能量是否足够
            if self.robot_state['energy'] < energy_cost:
                result = {
                    'success': False,
                    'message': "能量不足，无法执行移动任务",
                    'energy_cost': 0,
                    'time_taken': time.time() - start_time,
                    'target_x': target_x,
                    'target_z': target_z,
                    'task_type': 'move'
                }
                self.log_execution(result)
                return result
            
            # 执行本地移动
            self.robot_state['energy'] -= energy_cost
            self.robot_state['x'] = target_x
            self.robot_state['z'] = target_z
            
            result = {
                'success': True,
                'message': f"在本地模拟成功移动到目标位置 ({target_x}, {target_z})",
                'energy_cost': energy_cost,
                'time_taken': time.time() - start_time,
                'distance': distance,
                'target_x': target_x,
                'target_z': target_z,
                'task_type': 'move'
            }
            self.log_execution(result)
            return result
    
    def execute_task_series(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        执行一系列任务，支持与游戏服务器API交互
        
        Args:
            tasks: 任务列表，每个任务包含'task_type'字段和其他必要参数
            
        Returns:
            所有任务的执行结果列表
        """
        results = []
        
        for task in tasks:
            # 更新当前任务
            self.current_task = task
            task_type = task.get('task_type')
            
            # 估计任务能耗
            estimated_energy = self.estimate_task_energy(task_type, task)
            if self.robot_state['energy'] < estimated_energy:
                result = {
                    'success': False,
                    'message': f"能量不足，无法执行任务: {task_type}",
                    'task_type': task_type,
                    'energy_required': estimated_energy,
                    'current_energy': self.robot_state['energy']
                }
                results.append(result)
                self.log_execution(result)
                continue
            
            # 根据任务类型执行相应的任务
            try:
                # 记录任务开始
                print(f"开始执行任务: {task_type}，参数: {task}")
                
                if task_type == 'sow':
                    result = self.execute_sow_task(
                        task.get('row'), 
                        task.get('col'), 
                        task.get('plant_type', 'wheat')
                    )
                elif task_type == 'water':
                    result = self.execute_water_task(task.get('row'), task.get('col'))
                elif task_type == 'weed':
                    result = self.execute_weed_task(task.get('row'), task.get('col'))
                elif task_type == 'harvest':
                    result = self.execute_harvest_task(task.get('row'), task.get('col'))
                elif task_type == 'scan':
                    result = self.execute_scan_task(task.get('row'), task.get('col'))
                elif task_type == 'move':
                    result = self.execute_move_task(
                        task.get('target_x'), 
                        task.get('target_z'), 
                        task.get('tolerance', 0.1)
                    )
                else:
                    result = {
                        'success': False,
                        'message': f"未知任务类型: {task_type}",
                        'task_type': task_type
                    }
                
                results.append(result)
                
                # 记录任务结果
                if result.get('success'):
                    print(f"任务成功: {task_type}, 能量消耗: {result.get('energy_cost', 0)}")
                else:
                    print(f"任务失败: {task_type}, 原因: {result.get('message')}")
                
                # 如果任务失败且需要停止执行，则终止后续任务
                if not result.get('success') and task.get('stop_on_failure', True):
                    print(f"任务失败，停止执行任务序列: {result.get('message')}")
                    break
                
                # 任务间隔时间
                time.sleep(task.get('interval', 0.5))
                
            except Exception as e:
                error_message = f"执行任务时发生错误: {str(e)}"
                print(error_message)
                result = {
                    'success': False,
                    'message': error_message,
                    'task_type': task_type,
                    'exception': str(e)
                }
                results.append(result)
                self.log_execution(result)
                
                if task.get('stop_on_failure', True):
                    print(f"任务执行出错，停止执行任务序列: {str(e)}")
                    break
        
        # 清除当前任务
        self.current_task = None
        
        # 统计任务执行情况
        stats = self.get_task_statistics()
        print(f"任务序列执行完成: 总任务数={stats['total_tasks_executed']}, "
              f"成功率={stats['success_rates'].get(task_type, 0):.1f}%")
        
        return results
    
    def log_execution(self, result: Dict[str, Any]):
        """
        记录任务执行历史
        
        Args:
            result: 任务执行结果
        """
        # 添加时间戳
        result['timestamp'] = time.time()
        
        # 记录到历史
        self.execution_history.append(result)
        
        # 更新任务成功率统计
        task_type = result.get('task_type', 'unknown')
        if task_type not in self.task_success_rate:
            self.task_success_rate[task_type] = {'total': 0, 'success': 0}
        
        self.task_success_rate[task_type]['total'] += 1
        if result.get('success', False):
            self.task_success_rate[task_type]['success'] += 1
    
    def get_task_statistics(self) -> Dict[str, Any]:
        """
        获取任务执行统计信息
        
        Returns:
            统计信息
        """
        stats = {
            'total_tasks_executed': len(self.execution_history),
            'tasks_by_type': {},
            'success_rates': {}
        }
        
        # 统计各类型任务数量
        for task in self.execution_history:
            task_type = task.get('task_type', 'unknown')
            if task_type not in stats['tasks_by_type']:
                stats['tasks_by_type'][task_type] = 0
            stats['tasks_by_type'][task_type] += 1
        
        # 计算各类型任务的成功率
        for task_type, counts in self.task_success_rate.items():
            if counts['total'] > 0:
                stats['success_rates'][task_type] = counts['success'] / counts['total'] * 100
            else:
                stats['success_rates'][task_type] = 0
        
        return stats
    
    def estimate_task_energy(self, task_type: str, task: Dict[str, Any] = None) -> int:
        """
        估算任务所需的能量
        
        Args:
            task_type: 任务类型
            task: 任务详细信息
            
        Returns:
            预估的能量消耗
        """
        if task_type == 'sow':
            return int(self.energy_consumption_rates.get('sow', 2.0))
        elif task_type == 'water':
            return int(self.energy_consumption_rates.get('water', 1.0))
        elif task_type == 'weed':
            return int(self.energy_consumption_rates.get('weed', 1.5))
        elif task_type == 'harvest':
            return int(self.energy_consumption_rates.get('harvest', 3.0))
        elif task_type == 'scan':
            return int(self.energy_consumption_rates.get('scan', 0.2))
        elif task_type == 'move' and task:
            # 计算移动距离并估算能耗
            current_x = self.robot_state.get('x', 0)
            current_z = self.robot_state.get('z', 0)
            target_x = task.get('target_x', 0)
            target_z = task.get('target_z', 0)
            distance = ((target_x - current_x) **2 + (target_z - current_z)** 2) ** 0.5
            return max(1, int(distance * self.energy_consumption_rates.get('move', 0.5)))
        else:
            return int(self.energy_consumption_rates.get(task_type, 1.0))
