#!/usr/bin/env python3
"""
智能农场状态监测系统
负责收集、分析和提供农场环境和植物状态信息
"""
import time
import random
from datetime import datetime
from typing import Dict, List, Any, Optional
from enum import Enum

class PlantState(Enum):
    """植物状态枚举"""
    EMPTY = "empty"           # 空地
    GERMINATION = "germination"  # 发芽期
    SEEDLING = "seedling"       # 幼苗期
    GROWING = "growing"        # 生长期
    MATURING = "maturing"       # 成熟期
    HARVESTABLE = "harvestable"  # 可收获
    OVERGROWN = "overgrown"     # 过熟
    WILTING = "wilting"        # 枯萎
    DEAD = "dead"            # 死亡

class StateMonitor:
    """
    状态监测系统
    监控农场环境和植物状态，提供数据分析
    """
    def __init__(self):
        # 环境参数
        self.environment = {
            'temperature': 25.0,     # 温度(°C)
            'humidity': 60.0,        # 湿度(%)
            'light_level': 80.0,     # 光照强度(%)
            'soil_moisture': {},     # 土壤湿度，按植物ID索引
            'soil_nutrients': {},    # 土壤营养，按植物ID索引
        }
        
        # 植物状态缓存
        self.plant_states = {}
        
        # 上次更新时间
        self.last_update_time = None
        
        # 生长速度系数（受环境影响）
        self.growth_rate_factor = 1.0
        
    def update_environment(self, new_environment: Dict[str, Any] = None):
        """更新环境参数
        
        Args:
            new_environment: 新的环境参数
        """
        if new_environment:
            self.environment.update(new_environment)
        else:
            # 如果没有提供新参数，模拟环境变化
            self._simulate_environment_changes()
        
        # 更新生长速度系数
        self._update_growth_rate_factor()
        self.last_update_time = datetime.now()
        
        return self.environment
    
    def _simulate_environment_changes(self):
        """模拟环境参数的自然变化"""
        # 温度小幅波动（±2°C）
        self.environment['temperature'] += random.uniform(-0.5, 0.5)
        self.environment['temperature'] = max(15.0, min(35.0, self.environment['temperature']))
        
        # 湿度小幅波动（±3%）
        self.environment['humidity'] += random.uniform(-1.0, 1.0)
        self.environment['humidity'] = max(30.0, min(90.0, self.environment['humidity']))
        
        # 光照强度变化（模拟日夜周期）
        current_hour = datetime.now().hour
        if 6 <= current_hour < 18:
            # 白天，光照逐渐增强然后减弱
            if current_hour < 12:
                self.environment['light_level'] += random.uniform(2.0, 5.0)
            else:
                self.environment['light_level'] -= random.uniform(2.0, 5.0)
            self.environment['light_level'] = max(60.0, min(100.0, self.environment['light_level']))
        else:
            # 夜晚，光照较低
            self.environment['light_level'] = max(0.0, min(20.0, self.environment['light_level'] - random.uniform(1.0, 3.0)))
    
    def _update_growth_rate_factor(self):
        """根据环境参数计算生长速度系数"""
        # 理想温度范围：20-28°C
        temp = self.environment['temperature']
        if 20 <= temp <= 28:
            temp_factor = 1.0
        elif temp < 20:
            temp_factor = 0.5 + (temp - 15) * 0.1  # 15°C时为0.5，20°C时为1.0
        else:
            temp_factor = 1.0 - (temp - 28) * 0.05  # 超过28°C后每度降低5%
        
        # 理想湿度范围：50-70%
        humidity = self.environment['humidity']
        if 50 <= humidity <= 70:
            humidity_factor = 1.0
        else:
            humidity_factor = max(0.5, 1.0 - abs(humidity - 60) * 0.01)  # 偏离理想湿度越多，系数越低
        
        # 光照对生长的影响
        light = self.environment['light_level']
        if light > 50:
            light_factor = 0.8 + (light - 50) * 0.004  # 最大1.0
        else:
            light_factor = 0.2 + light * 0.012  # 最低0.2
        
        # 综合计算生长速度系数
        self.growth_rate_factor = temp_factor * humidity_factor * light_factor
    
    def update_plant_states(self, plants: List[Dict[str, Any]]):
        """更新所有植物的状态
        
        Args:
            plants: 从服务器获取的植物列表
        """
        for plant in plants:
            plant_id = plant['id']
            
            # 如果是新植物，初始化状态
            if plant_id not in self.plant_states:
                self._initialize_plant_state(plant)
            
            # 更新植物状态
            self._update_single_plant_state(plant)
        
        return self.plant_states
    
    def _initialize_plant_state(self, plant: Dict[str, Any]):
        """初始化新植物的状态"""
        plant_id = plant['id']
        
        # 初始化土壤状态
        self.environment['soil_moisture'][plant_id] = random.uniform(40.0, 60.0)
        self.environment['soil_nutrients'][plant_id] = {
            'nitrogen': random.uniform(30.0, 70.0),
            'phosphorus': random.uniform(30.0, 70.0),
            'potassium': random.uniform(30.0, 70.0)
        }
        
        # 初始化植物状态
        if plant.get('is_empty'):
            state = PlantState.EMPTY
        elif plant.get('is_weed'):
            # 杂草直接进入生长状态
            state = PlantState.GROWING
            growth_stage = 1
            health = random.uniform(70.0, 100.0)
        else:
            # 正常植物从发芽期开始
            state = PlantState.GERMINATION
            growth_stage = 0
            health = random.uniform(80.0, 100.0)
        
        self.plant_states[plant_id] = {
            'state': state,
            'growth_stage': growth_stage,
            'health': health,
            'age': 0,
            'last_watered': time.time(),
            'last_fertilized': time.time(),
            'growth_progress': 0.0,  # 0.0 到 1.0，表示当前阶段的进度
            'water_needed': False,
            'fertilizer_needed': False,
            'weed_competition': False
        }
    
    def _update_single_plant_state(self, plant: Dict[str, Any]):
        """更新单个植物的状态"""
        plant_id = plant['id']
        plant_state = self.plant_states[plant_id]
        
        # 更新植物年龄
        plant_state['age'] += 1
        
        # 如果植物已被移除，跳过更新
        if plant.get('is_removed'):
            plant_state['state'] = PlantState.EMPTY
            return
        
        # 更新土壤湿度（自然蒸发）
        current_moisture = self.environment['soil_moisture'].get(plant_id, 50.0)
        evaporation_rate = 0.5 + (self.environment['temperature'] - 20) * 0.1
        new_moisture = max(0.0, current_moisture - evaporation_rate)
        self.environment['soil_moisture'][plant_id] = new_moisture
        
        # 判断是否需要浇水
        plant_state['water_needed'] = new_moisture < 30.0
        
        # 更新营养消耗
        nutrients = self.environment['soil_nutrients'].get(plant_id, {})
        if not plant.get('is_empty') and not plant.get('is_removed'):
            # 植物生长消耗营养
            for key in nutrients:
                nutrients[key] = max(0.0, nutrients[key] - 0.2 * self.growth_rate_factor)
            
            # 判断是否需要施肥
            avg_nutrient = sum(nutrients.values()) / len(nutrients)
            plant_state['fertilizer_needed'] = avg_nutrient < 30.0
        
        # 更新植物生长状态
        if plant.get('is_empty'):
            plant_state['state'] = PlantState.EMPTY
        elif plant.get('is_weed'):
            self._update_weed_state(plant_id, plant_state)
        else:
            self._update_crop_state(plant_id, plant_state)
        
        # 根据水分和营养状态更新健康度
        if plant_state['water_needed']:
            plant_state['health'] = max(0.0, plant_state['health'] - 2.0)
        elif plant_state['fertilizer_needed']:
            plant_state['health'] = max(0.0, plant_state['health'] - 1.0)
        else:
            plant_state['health'] = min(100.0, plant_state['health'] + 0.5)
        
        # 健康度过低时进入枯萎状态
        if plant_state['health'] < 20.0:
            plant_state['state'] = PlantState.WILTING
        if plant_state['health'] <= 0.0:
            plant_state['state'] = PlantState.DEAD
    
    def _update_weed_state(self, plant_id: str, plant_state: Dict[str, Any]):
        """更新杂草状态"""
        # 杂草生长速度更快
        plant_state['growth_progress'] += 0.05 * self.growth_rate_factor * 1.5  # 杂草生长速度是作物的1.5倍
        
        # 更新生长阶段
        if plant_state['growth_progress'] >= 1.0:
            plant_state['growth_stage'] += 1
            plant_state['growth_progress'] = 0.0
            
            # 杂草只有两个阶段：生长期和成熟期
            if plant_state['growth_stage'] >= 2:
                plant_state['state'] = PlantState.MATURING
                plant_state['growth_stage'] = 2
            else:
                plant_state['state'] = PlantState.GROWING
    
    def _update_crop_state(self, plant_id: str, plant_state: Dict[str, Any]):
        """更新作物状态"""
        # 正常作物生长
        plant_state['growth_progress'] += 0.02 * self.growth_rate_factor
        
        # 如果缺水或缺营养，生长速度减慢
        if plant_state['water_needed'] or plant_state['fertilizer_needed']:
            plant_state['growth_progress'] *= 0.5
        
        # 更新生长阶段和状态
        if plant_state['growth_progress'] >= 1.0:
            plant_state['growth_stage'] += 1
            plant_state['growth_progress'] = 0.0
            
            # 根据生长阶段更新状态
            if plant_state['growth_stage'] == 1:
                plant_state['state'] = PlantState.SEEDLING
            elif plant_state['growth_stage'] == 2:
                plant_state['state'] = PlantState.GROWING
            elif plant_state['growth_stage'] == 3:
                plant_state['state'] = PlantState.MATURING
            elif plant_state['growth_stage'] == 4:
                plant_state['state'] = PlantState.HARVESTABLE
            elif plant_state['growth_stage'] >= 5:
                plant_state['state'] = PlantState.OVERGROWN
                plant_state['growth_stage'] = 5
    
    def water_plant(self, plant_id: str):
        """给植物浇水
        
        Args:
            plant_id: 植物ID
        """
        if plant_id in self.environment['soil_moisture']:
            # 将土壤湿度恢复到70-80%
            self.environment['soil_moisture'][plant_id] = random.uniform(70.0, 80.0)
            
            # 更新植物状态
            if plant_id in self.plant_states:
                self.plant_states[plant_id]['water_needed'] = False
                self.plant_states[plant_id]['last_watered'] = time.time()
                
                # 浇水后健康度小幅提升
                self.plant_states[plant_id]['health'] = min(100.0, self.plant_states[plant_id]['health'] + 5.0)
            
            return True
        return False
    
    def fertilize_plant(self, plant_id: str):
        """给植物施肥
        
        Args:
            plant_id: 植物ID
        """
        if plant_id in self.environment['soil_nutrients']:
            # 将土壤营养恢复到60-80%
            nutrients = self.environment['soil_nutrients'][plant_id]
            for key in nutrients:
                nutrients[key] = random.uniform(60.0, 80.0)
            
            # 更新植物状态
            if plant_id in self.plant_states:
                self.plant_states[plant_id]['fertilizer_needed'] = False
                self.plant_states[plant_id]['last_fertilized'] = time.time()
                
                # 施肥后健康度小幅提升
                self.plant_states[plant_id]['health'] = min(100.0, self.plant_states[plant_id]['health'] + 3.0)
            
            return True
        return False
    
    def get_plant_recommendations(self, plant_id: str) -> Dict[str, Any]:
        """获取植物护理建议
        
        Args:
            plant_id: 植物ID
            
        Returns:
            包含护理建议的字典
        """
        recommendations = {
            'needs_water': False,
            'needs_fertilizer': False,
            'needs_harvest': False,
            'needs_removal': False,
            'health_status': 'good',
            'next_action': None
        }
        
        if plant_id not in self.plant_states:
            return recommendations
        
        plant_state = self.plant_states[plant_id]
        
        # 检查是否需要浇水
        recommendations['needs_water'] = plant_state['water_needed']
        
        # 检查是否需要施肥
        recommendations['needs_fertilizer'] = plant_state['fertilizer_needed']
        
        # 检查是否可以收获
        recommendations['needs_harvest'] = plant_state['state'] == PlantState.HARVESTABLE
        
        # 检查是否需要移除（死亡或过熟）
        recommendations['needs_removal'] = plant_state['state'] in [PlantState.DEAD, PlantState.OVERGROWN]
        
        # 评估健康状态
        health = plant_state['health']
        if health > 80:
            recommendations['health_status'] = 'excellent'
        elif health > 60:
            recommendations['health_status'] = 'good'
        elif health > 40:
            recommendations['health_status'] = 'fair'
        elif health > 20:
            recommendations['health_status'] = 'poor'
        else:
            recommendations['health_status'] = 'critical'
        
        # 确定下一步操作优先级
        if recommendations['needs_water']:
            recommendations['next_action'] = 'water'
        elif recommendations['needs_harvest']:
            recommendations['next_action'] = 'harvest'
        elif recommendations['needs_fertilizer']:
            recommendations['next_action'] = 'fertilize'
        elif recommendations['needs_removal']:
            recommendations['next_action'] = 'remove'
        
        return recommendations
    
    def get_overall_farm_health(self) -> Dict[str, Any]:
        """获取农场整体健康状况
        
        Returns:
            包含农场健康数据的字典
        """
        total_plants = len(self.plant_states)
        if total_plants == 0:
            return {
                'overall_health': 'unknown',
                'plant_count': 0,
                'healthy_plants': 0,
                'water_stressed': 0,
                'nutrient_deficient': 0,
                'ready_for_harvest': 0,
                'weeds': 0,
                'problem_plants': 0
            }
        
        # 统计各种状态的植物数量
        healthy_plants = 0
        water_stressed = 0
        nutrient_deficient = 0
        ready_for_harvest = 0
        weeds = 0
        problem_plants = 0
        
        for plant_id, state in self.plant_states.items():
            if state['health'] > 60:
                healthy_plants += 1
            
            if state['water_needed']:
                water_stressed += 1
            
            if state['fertilizer_needed']:
                nutrient_deficient += 1
            
            if state['state'] == PlantState.HARVESTABLE:
                ready_for_harvest += 1
            
            if state['state'] in [PlantState.WILTING, PlantState.DEAD, PlantState.OVERGROWN]:
                problem_plants += 1
        
        # 计算整体健康评分
        health_score = (healthy_plants / total_plants) * 100
        if health_score >= 80:
            overall_health = 'excellent'
        elif health_score >= 60:
            overall_health = 'good'
        elif health_score >= 40:
            overall_health = 'fair'
        else:
            overall_health = 'poor'
        
        return {
            'overall_health': overall_health,
            'health_score': health_score,
            'plant_count': total_plants,
            'healthy_plants': healthy_plants,
            'water_stressed': water_stressed,
            'nutrient_deficient': nutrient_deficient,
            'ready_for_harvest': ready_for_harvest,
            'problem_plants': problem_plants,
            'environment_factors': {
                'temperature': self.environment['temperature'],
                'humidity': self.environment['humidity'],
                'light_level': self.environment['light_level'],
                'growth_rate_factor': self.growth_rate_factor
            }
        }

# 为了避免导入错误，需要在文件底部添加Enum的导入
from enum import Enum
