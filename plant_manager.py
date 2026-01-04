#!/usr/bin/env python3
"""
智能农场种植管理模块
负责植物的生长周期管理和状态更新
"""
import time
from typing import Dict, List, Tuple, Optional, Any
import random

class PlantManager:
    """
    植物管理器
    负责管理植物的生长、更新状态和提供植物信息
    """
    # 植物类型配置
    PLANT_CONFIGS = {
        "wheat": {
            "name": "小麦",
            "growth_stages": 4,  # 0: 种子, 1: 发芽, 2: 生长中, 3: 成熟
            "growth_time_per_stage": 60,  # 每个阶段的生长时间（秒）
            "water_frequency": 30,  # 浇水频率（秒）
            "optimal_health": 80,  # 最佳健康值
            "max_yield": 15,  # 最大产量
            "base_value": 1  # 基础价值（金币）
        },
        "corn": {
            "name": "玉米",
            "growth_stages": 4,
            "growth_time_per_stage": 90,
            "water_frequency": 45,
            "optimal_health": 85,
            "max_yield": 12,
            "base_value": 2
        },
        "carrot": {
            "name": "胡萝卜",
            "growth_stages": 3,
            "growth_time_per_stage": 45,
            "water_frequency": 25,
            "optimal_health": 75,
            "max_yield": 20,
            "base_value": 1
        },
        "tomato": {
            "name": "番茄",
            "growth_stages": 5,
            "growth_time_per_stage": 120,
            "water_frequency": 40,
            "optimal_health": 90,
            "max_yield": 10,
            "base_value": 3
        }
    }
    
    def __init__(self, grid_size: int = 8):
        """
        初始化植物管理器
        
        Args:
            grid_size: 农场网格大小
        """
        self.grid_size = grid_size
        # 初始化农场网格，每个单元格存储植物信息或None
        self.plants = [[None for _ in range(grid_size)] for _ in range(grid_size)]
        self.last_update_time = time.time()
        self.global_environment = {
            "temperature": 25.0,  # 摄氏度
            "humidity": 60.0,     # 百分比
            "light_level": 80.0,  # 百分比
            "weed_growth_rate": 0.02  # 杂草生长率
        }
    
    def add_plant(self, row: int, col: int, plant_type: str = "wheat") -> Optional[Dict[str, Any]]:
        """
        在指定位置添加植物
        
        Args:
            row: 行坐标
            col: 列坐标
            plant_type: 植物类型
            
        Returns:
            新添加的植物信息，如果失败则返回None
        """
        # 检查坐标是否有效
        if not (0 <= row < self.grid_size and 0 <= col < self.grid_size):
            return None
        
        # 检查该位置是否已有植物
        if self.plants[row][col] is not None and self.plants[row][col].get('state') != 'harvested':
            return None
        
        # 检查植物类型是否支持
        if plant_type not in self.PLANT_CONFIGS:
            plant_type = "wheat"  # 默认使用小麦
        
        # 创建新植物
        plant = {
            "type": plant_type,
            "state": "seed",  # seed, growing, harvested, dead
            "growth_stage": 0,
            "age": 0,
            "health": 100,
            "planted_time": time.time(),
            "last_watered": time.time(),
            "weed_count": 0,
            "position": {"row": row, "col": col}
        }
        
        self.plants[row][col] = plant
        return plant
    
    def remove_plant(self, row: int, col: int) -> bool:
        """
        移除指定位置的植物
        
        Args:
            row: 行坐标
            col: 列坐标
            
        Returns:
            移除是否成功
        """
        # 检查坐标是否有效
        if not (0 <= row < self.grid_size and 0 <= col < self.grid_size):
            return False
        
        self.plants[row][col] = None
        return True
    
    def water_plant(self, row: int, col: int) -> bool:
        """
        给指定位置的植物浇水
        
        Args:
            row: 行坐标
            col: 列坐标
            
        Returns:
            浇水是否成功
        """
        # 检查坐标是否有效
        if not (0 <= row < self.grid_size and 0 <= col < self.grid_size):
            return False
        
        plant = self.plants[row][col]
        if plant is None or plant.get('state') in ['dead', 'harvested']:
            return False
        
        # 更新浇水时间
        plant['last_watered'] = time.time()
        
        # 增加健康值
        plant['health'] = min(100, plant['health'] + 10)
        
        return True
    
    def remove_weeds(self, row: int, col: int) -> bool:
        """
        清除指定位置的杂草
        
        Args:
            row: 行坐标
            col: 列坐标
            
        Returns:
            除草是否成功
        """
        # 检查坐标是否有效
        if not (0 <= row < self.grid_size and 0 <= col < self.grid_size):
            return False
        
        plant = self.plants[row][col]
        if plant is None or plant.get('state') in ['dead', 'harvested']:
            return False
        
        # 清除杂草
        plant['weed_count'] = 0
        
        # 增加健康值
        plant['health'] = min(100, plant['health'] + 5)
        
        return True
    
    def harvest_plant(self, row: int, col: int) -> Optional[Dict[str, Any]]:
        """
        收获指定位置的植物
        
        Args:
            row: 行坐标
            col: 列坐标
            
        Returns:
            收获结果，包含产量和价值信息，如果无法收获则返回None
        """
        # 检查坐标是否有效
        if not (0 <= row < self.grid_size and 0 <= col < self.grid_size):
            return None
        
        plant = self.plants[row][col]
        
        # 检查植物是否可以收获
        if (plant is None or plant.get('state') in ['dead', 'harvested'] or 
            plant.get('growth_stage') < self.PLANT_CONFIGS[plant.get('type', 'wheat')]['growth_stages'] - 1):
            return None
        
        plant_type = plant.get('type', 'wheat')
        config = self.PLANT_CONFIGS[plant_type]
        health = plant.get('health', 100)
        
        # 计算产量
        # 产量与植物健康值、生长阶段和环境因素相关
        base_yield = config['max_yield'] * 0.5  # 基础产量为最大产量的一半
        health_factor = health / 100.0  # 健康因子
        weed_factor = max(0.5, 1.0 - plant.get('weed_count', 0) * 0.1)  # 杂草影响因子
        
        # 计算最终产量
        yield_amount = int(base_yield * health_factor * weed_factor * (0.9 + random.random() * 0.2))
        
        # 计算价值
        value_per_unit = config['base_value']
        total_value = yield_amount * value_per_unit
        
        # 更新植物状态
        plant['state'] = 'harvested'
        plant['harvested_time'] = time.time()
        plant['yield'] = yield_amount
        plant['value'] = total_value
        
        return {
            "success": True,
            "plant_type": plant_type,
            "yield": yield_amount,
            "value": total_value,
            "plant_info": plant
        }
    
    def update_all_plants(self):
        """
        更新所有植物的状态
        应该定期调用此方法以模拟植物生长
        """
        current_time = time.time()
        delta_time = current_time - self.last_update_time
        self.last_update_time = current_time
        
        # 更新每个位置的植物
        for row in range(self.grid_size):
            for col in range(self.grid_size):
                plant = self.plants[row][col]
                if plant is None or plant.get('state') in ['harvested', 'dead']:
                    continue
                
                # 更新植物年龄
                plant['age'] += delta_time
                
                # 获取植物配置
                plant_type = plant.get('type', 'wheat')
                config = self.PLANT_CONFIGS[plant_type]
                
                # 检查是否需要生长
                self._update_growth(plant, config, delta_time)
                
                # 检查水分状态，影响健康值
                self._update_water_status(plant, config)
                
                # 检查并更新杂草生长
                self._update_weeds(plant, delta_time)
                
                # 检查健康状态，如果健康值过低，植物死亡
                self._update_health(plant, config)
    
    def _update_growth(self, plant: Dict[str, Any], config: Dict[str, Any], delta_time: float):
        """
        更新植物生长状态
        
        Args:
            plant: 植物信息
            config: 植物配置
            delta_time: 时间间隔
        """
        # 计算应该达到的生长阶段
        growth_stage_time = plant['age'] / config['growth_time_per_stage']
        target_stage = min(int(growth_stage_time), config['growth_stages'] - 1)
        
        # 更新生长阶段
        if target_stage > plant['growth_stage']:
            plant['growth_stage'] = target_stage
            
            # 更新状态
            if target_stage == 0:
                plant['state'] = 'seed'
            else:
                plant['state'] = 'growing'
                
            # 如果达到成熟阶段，更新状态
            if target_stage == config['growth_stages'] - 1:
                plant['ripe_time'] = time.time()
    
    def _update_water_status(self, plant: Dict[str, Any], config: Dict[str, Any]):
        """
        更新植物水分状态，影响健康值
        
        Args:
            plant: 植物信息
            config: 植物配置
        """
        current_time = time.time()
        time_since_watered = current_time - plant.get('last_watered', current_time)
        
        # 如果长时间没有浇水，降低健康值
        if time_since_watered > config['water_frequency']:
            # 每超过浇水频率一秒，健康值降低一定比例
            health_decrease = (time_since_watered - config['water_frequency']) * 0.1
            plant['health'] = max(0, plant['health'] - health_decrease)
        
        # 环境湿度影响水分蒸发
        humidity_factor = self.global_environment['humidity'] / 100.0
        if humidity_factor < 0.5:  # 低湿度加速水分流失
            plant['health'] = max(0, plant['health'] - 0.5)
    
    def _update_weeds(self, plant: Dict[str, Any], delta_time: float):
        """
        更新杂草生长
        
        Args:
            plant: 植物信息
            delta_time: 时间间隔
        """
        # 杂草生长概率
        weed_growth_chance = self.global_environment['weed_growth_rate'] * delta_time
        
        # 低光照条件下杂草更容易生长
        light_level = self.global_environment['light_level']
        if light_level < 50:
            weed_growth_chance *= 1.5
        
        # 随机决定是否生长杂草
        if random.random() < weed_growth_chance:
            plant['weed_count'] = min(5, plant.get('weed_count', 0) + 1)
            
            # 杂草影响植物健康
            plant['health'] = max(0, plant['health'] - 2)
    
    def _update_health(self, plant: Dict[str, Any], config: Dict[str, Any]):
        """
        更新植物健康状态
        
        Args:
            plant: 植物信息
            config: 植物配置
        """
        health = plant.get('health', 0)
        
        # 如果健康值为0，植物死亡
        if health <= 0:
            plant['state'] = 'dead'
            plant['death_time'] = time.time()
        
        # 环境温度影响
        temperature = self.global_environment['temperature']
        optimal_temp = 25.0  # 假设最适温度为25°C
        temp_diff = abs(temperature - optimal_temp)
        
        if temp_diff > 15:  # 温度差异过大
            plant['health'] = max(0, plant['health'] - 1)
        elif temp_diff > 10:  # 温度差异较大
            plant['health'] = max(0, plant['health'] - 0.5)
    
    def get_plant_info(self, row: int, col: int) -> Optional[Dict[str, Any]]:
        """
        获取指定位置的植物信息
        
        Args:
            row: 行坐标
            col: 列坐标
            
        Returns:
            植物信息，如果没有植物则返回None
        """
        # 检查坐标是否有效
        if not (0 <= row < self.grid_size and 0 <= col < self.grid_size):
            return None
        
        return self.plants[row][col]
    
    def get_field_summary(self) -> Dict[str, Any]:
        """
        获取农田摘要信息
        
        Returns:
            农田摘要信息
        """
        summary = {
            "total_plants": 0,
            "plants_by_type": {},
            "plants_by_stage": {},
            "plants_by_state": {},
            "weedy_plants": 0,
            "dry_plants": 0,
            "unhealthy_plants": 0,
            "ripe_plants": 0
        }
        
        current_time = time.time()
        
        for row in range(self.grid_size):
            for col in range(self.grid_size):
                plant = self.plants[row][col]
                if plant is None:
                    continue
                
                summary["total_plants"] += 1
                
                # 按类型统计
                plant_type = plant.get('type', 'unknown')
                if plant_type not in summary["plants_by_type"]:
                    summary["plants_by_type"][plant_type] = 0
                summary["plants_by_type"][plant_type] += 1
                
                # 按生长阶段统计
                growth_stage = plant.get('growth_stage', 0)
                if growth_stage not in summary["plants_by_stage"]:
                    summary["plants_by_stage"][growth_stage] = 0
                summary["plants_by_stage"][growth_stage] += 1
                
                # 按状态统计
                state = plant.get('state', 'unknown')
                if state not in summary["plants_by_state"]:
                    summary["plants_by_state"][state] = 0
                summary["plants_by_state"][state] += 1
                
                # 统计有杂草的植物
                if plant.get('weed_count', 0) > 0:
                    summary["weedy_plants"] += 1
                
                # 统计缺水的植物
                plant_type = plant.get('type', 'wheat')
                config = self.PLANT_CONFIGS[plant_type]
                time_since_watered = current_time - plant.get('last_watered', 0)
                if time_since_watered > config['water_frequency']:
                    summary["dry_plants"] += 1
                
                # 统计不健康的植物
                if plant.get('health', 100) < 50:
                    summary["unhealthy_plants"] += 1
                
                # 统计成熟可收获的植物
                if (state == 'growing' and 
                    growth_stage >= self.PLANT_CONFIGS[plant_type]['growth_stages'] - 1):
                    summary["ripe_plants"] += 1
        
        return summary
    
    def get_plants_needing_water(self) -> List[Dict[str, Any]]:
        """
        获取需要浇水的植物列表
        
        Returns:
            需要浇水的植物列表，每个元素包含位置和植物信息
        """
        plants_needing_water = []
        current_time = time.time()
        
        for row in range(self.grid_size):
            for col in range(self.grid_size):
                plant = self.plants[row][col]
                if plant is None or plant.get('state') in ['dead', 'harvested']:
                    continue
                
                plant_type = plant.get('type', 'wheat')
                config = self.PLANT_CONFIGS[plant_type]
                time_since_watered = current_time - plant.get('last_watered', 0)
                
                # 如果超过浇水频率，需要浇水
                if time_since_watered > config['water_frequency']:
                    plants_needing_water.append({
                        "row": row,
                        "col": col,
                        "plant": plant,
                        "time_since_watered": time_since_watered
                    })
        
        # 按缺水时间排序，最缺水的排在前面
        plants_needing_water.sort(key=lambda x: x["time_since_watered"], reverse=True)
        
        return plants_needing_water
    
    def get_plants_needing_weeding(self) -> List[Dict[str, Any]]:
        """
        获取需要除草的植物列表
        
        Returns:
            需要除草的植物列表，每个元素包含位置和植物信息
        """
        plants_needing_weeding = []
        
        for row in range(self.grid_size):
            for col in range(self.grid_size):
                plant = self.plants[row][col]
                if plant is None or plant.get('state') in ['dead', 'harvested']:
                    continue
                
                weed_count = plant.get('weed_count', 0)
                if weed_count > 0:
                    plants_needing_weeding.append({
                        "row": row,
                        "col": col,
                        "plant": plant,
                        "weed_count": weed_count
                    })
        
        # 按杂草数量排序，杂草最多的排在前面
        plants_needing_weeding.sort(key=lambda x: x["weed_count"], reverse=True)
        
        return plants_needing_weeding
    
    def get_ripe_plants(self) -> List[Dict[str, Any]]:
        """
        获取成熟可收获的植物列表
        
        Returns:
            成熟可收获的植物列表，每个元素包含位置和植物信息
        """
        ripe_plants = []
        
        for row in range(self.grid_size):
            for col in range(self.grid_size):
                plant = self.plants[row][col]
                if plant is None or plant.get('state') in ['dead', 'harvested']:
                    continue
                
                plant_type = plant.get('type', 'wheat')
                config = self.PLANT_CONFIGS[plant_type]
                growth_stage = plant.get('growth_stage', 0)
                
                # 检查是否成熟
                if (plant.get('state') == 'growing' and 
                    growth_stage >= config['growth_stages'] - 1):
                    ripe_plants.append({
                        "row": row,
                        "col": col,
                        "plant": plant
                    })
        
        return ripe_plants
    
    def get_empty_spots(self) -> List[Tuple[int, int]]:
        """
        获取空的种植位置
        
        Returns:
            空位置的坐标列表
        """
        empty_spots = []
        
        for row in range(self.grid_size):
            for col in range(self.grid_size):
                plant = self.plants[row][col]
                # 空位置或已收获的位置可以重新种植
                if plant is None or plant.get('state') == 'harvested':
                    empty_spots.append((row, col))
        
        return empty_spots
    
    def update_environment(self, temperature: Optional[float] = None,
                          humidity: Optional[float] = None,
                          light_level: Optional[float] = None):
        """
        更新环境参数
        
        Args:
            temperature: 温度（摄氏度）
            humidity: 湿度（百分比）
            light_level: 光照水平（百分比）
        """
        if temperature is not None:
            self.global_environment['temperature'] = max(0, min(50, temperature))  # 限制在0-50°C
        
        if humidity is not None:
            self.global_environment['humidity'] = max(0, min(100, humidity))  # 限制在0-100%
        
        if light_level is not None:
            self.global_environment['light_level'] = max(0, min(100, light_level))  # 限制在0-100%
    
    def get_environment(self) -> Dict[str, float]:
        """
        获取当前环境参数
        
        Returns:
            环境参数
        """
        return self.global_environment.copy()
    
    def get_recommended_actions(self) -> List[Dict[str, Any]]:
        """
        获取推荐的农业操作
        
        Returns:
            推荐操作列表
        """
        recommended_actions = []
        
        # 优先处理需要浇水的植物
        water_plants = self.get_plants_needing_water()[:3]  # 最多推荐3个
        for plant_info in water_plants:
            recommended_actions.append({
                "action": "water",
                "row": plant_info["row"],
                "col": plant_info["col"],
                "priority": 3,  # 优先级：1最低，5最高
                "reason": f"植物已 {plant_info['time_since_watered']:.1f} 秒未浇水"
            })
        
        # 处理需要除草的植物
        weed_plants = self.get_plants_needing_weeding()[:2]  # 最多推荐2个
        for plant_info in weed_plants:
            recommended_actions.append({
                "action": "weed",
                "row": plant_info["row"],
                "col": plant_info["col"],
                "priority": 4,
                "reason": f"植物有 {plant_info['weed_count']} 株杂草"
            })
        
        # 收获成熟的植物
        ripe_plants = self.get_ripe_plants()[:3]  # 最多推荐3个
        for plant_info in ripe_plants:
            recommended_actions.append({
                "action": "harvest",
                "row": plant_info["row"],
                "col": plant_info["col"],
                "priority": 5,
                "reason": "植物已成熟，可以收获"
            })
        
        # 播种新植物
        empty_spots = self.get_empty_spots()[:2]  # 最多推荐2个
        for row, col in empty_spots:
            recommended_actions.append({
                "action": "sow",
                "row": row,
                "col": col,
                "priority": 2,
                "reason": "空位置可以种植新植物"
            })
        
        # 按优先级排序
        recommended_actions.sort(key=lambda x: x["priority"], reverse=True)
        
        return recommended_actions
