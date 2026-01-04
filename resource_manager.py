#!/usr/bin/env python3
"""
智能农场资源管理模块
负责管理机器人的能量、金币等资源
"""
import time
from typing import Dict, List, Tuple, Optional, Any
import random

class ResourceManager:
    """
    资源管理器
    负责管理农场和机器人的资源
    """
    def __init__(self, initial_energy: float = 100.0, 
                 initial_coins: int = 0, 
                 initial_seeds: Dict[str, int] = None):
        """
        初始化资源管理器
        
        Args:
            initial_energy: 初始能量值
            initial_coins: 初始金币数量
            initial_seeds: 初始种子库存
        """
        self.energy = max(0, min(100, initial_energy))  # 能量值，范围0-100
        self.max_energy = 100.0
        self.energy_regen_rate = 0.02  # 每秒自动恢复的能量
        self.last_regen_time = time.time()
        
        self.coins = initial_coins  # 金币数量
        
        # 种子库存
        self.seeds = initial_seeds or {
            "wheat": 10,
            "corn": 5,
            "carrot": 5,
            "tomato": 3
        }
        
        # 收获的农产品库存
        self.harvested_crops = {
            "wheat": 0,
            "corn": 0,
            "carrot": 0,
            "tomato": 0
        }
        
        # 工具和设备
        self.tools = {
            "watering_can": {
                "level": 1,
                "efficiency": 1.0,
                "durability": 100
            },
            "weeder": {
                "level": 1,
                "efficiency": 1.0,
                "durability": 100
            },
            "scanner": {
                "level": 1,
                "efficiency": 1.0,
                "durability": 100
            },
            "harvester": {
                "level": 1,
                "efficiency": 1.0,
                "durability": 100
            }
        }
        
        # 资源消耗记录
        self.resource_log = []
        
        # 资源阈值设置
        self.thresholds = {
            "low_energy": 20,
            "critical_energy": 10,
            "low_coins": 10,
            "low_seeds": 2
        }
    
    def update(self):
        """
        更新资源状态
        应该定期调用此方法以更新自动恢复的资源
        """
        current_time = time.time()
        delta_time = current_time - self.last_regen_time
        self.last_regen_time = current_time
        
        # 自动恢复能量
        self._regenerate_energy(delta_time)
    
    def _regenerate_energy(self, delta_time: float):
        """
        自动恢复能量
        
        Args:
            delta_time: 时间间隔
        """
        energy_to_regen = self.energy_regen_rate * delta_time
        self.energy = min(self.max_energy, self.energy + energy_to_regen)
    
    def consume_energy(self, amount: float) -> bool:
        """
        消耗能量
        
        Args:
            amount: 消耗的能量数量
            
        Returns:
            是否成功消耗（能量是否足够）
        """
        if self.energy >= amount:
            self.energy -= amount
            self._log_resource_change("energy", -amount, "consumption")
            return True
        return False
    
    def add_energy(self, amount: float) -> float:
        """
        增加能量
        
        Args:
            amount: 增加的能量数量
            
        Returns:
            实际增加的能量数量（可能因能量上限而小于请求的数量）
        """
        old_energy = self.energy
        self.energy = min(self.max_energy, self.energy + amount)
        actual_amount = self.energy - old_energy
        
        if actual_amount > 0:
            self._log_resource_change("energy", actual_amount, "addition")
        
        return actual_amount
    
    def add_coins(self, amount: int):
        """
        增加金币
        
        Args:
            amount: 增加的金币数量
        """
        if amount > 0:
            self.coins += amount
            self._log_resource_change("coins", amount, "addition")
    
    def spend_coins(self, amount: int) -> bool:
        """
        花费金币
        
        Args:
            amount: 花费的金币数量
            
        Returns:
            是否成功花费（金币是否足够）
        """
        if self.coins >= amount:
            self.coins -= amount
            self._log_resource_change("coins", -amount, "consumption")
            return True
        return False
    
    def add_seed(self, plant_type: str, amount: int = 1):
        """
        增加种子
        
        Args:
            plant_type: 植物类型
            amount: 增加的种子数量
        """
        if plant_type not in self.seeds:
            self.seeds[plant_type] = 0
        
        self.seeds[plant_type] += amount
        self._log_resource_change(f"seed_{plant_type}", amount, "addition")
    
    def use_seed(self, plant_type: str, amount: int = 1) -> bool:
        """
        使用种子
        
        Args:
            plant_type: 植物类型
            amount: 使用的种子数量
            
        Returns:
            是否成功使用（种子是否足够）
        """
        if plant_type in self.seeds and self.seeds[plant_type] >= amount:
            self.seeds[plant_type] -= amount
            self._log_resource_change(f"seed_{plant_type}", -amount, "consumption")
            return True
        return False
    
    def add_harvested_crop(self, plant_type: str, amount: int):
        """
        增加收获的农产品
        
        Args:
            plant_type: 植物类型
            amount: 增加的农产品数量
        """
        if plant_type not in self.harvested_crops:
            self.harvested_crops[plant_type] = 0
        
        self.harvested_crops[plant_type] += amount
        self._log_resource_change(f"crop_{plant_type}", amount, "harvest")
    
    def sell_harvested_crop(self, plant_type: str, amount: int = None) -> int:
        """
        出售收获的农产品
        
        Args:
            plant_type: 植物类型
            amount: 出售的数量，如果为None则出售全部
            
        Returns:
            获得的金币数量
        """
        if plant_type not in self.harvested_crops or self.harvested_crops[plant_type] <= 0:
            return 0
        
        # 确定出售数量
        if amount is None or amount > self.harvested_crops[plant_type]:
            amount = self.harvested_crops[plant_type]
        
        # 不同作物的单价
        crop_prices = {
            "wheat": 1,
            "corn": 2,
            "carrot": 1,
            "tomato": 3
        }
        
        price_per_unit = crop_prices.get(plant_type, 1)
        coins_earned = amount * price_per_unit
        
        # 更新库存
        self.harvested_crops[plant_type] -= amount
        
        # 增加金币
        self.add_coins(coins_earned)
        
        self._log_resource_change(f"crop_{plant_type}", -amount, "sale")
        
        return coins_earned
    
    def upgrade_tool(self, tool_name: str) -> bool:
        """
        升级工具
        
        Args:
            tool_name: 工具名称
            
        Returns:
            是否成功升级
        """
        if tool_name not in self.tools:
            return False
        
        tool = self.tools[tool_name]
        current_level = tool["level"]
        
        # 计算升级所需金币
        upgrade_cost = 50 * (current_level ** 2)  # 升级成本随等级增加而增加
        
        if not self.spend_coins(upgrade_cost):
            return False
        
        # 升级工具
        tool["level"] += 1
        tool["efficiency"] *= 1.1  # 效率每次提升10%
        tool["durability"] = 100  # 重置耐久度
        
        self._log_resource_change(f"tool_{tool_name}", 1, "upgrade")
        
        return True
    
    def repair_tool(self, tool_name: str) -> bool:
        """
        修理工具
        
        Args:
            tool_name: 工具名称
            
        Returns:
            是否成功修理
        """
        if tool_name not in self.tools:
            return False
        
        tool = self.tools[tool_name]
        
        # 工具不需要修理
        if tool["durability"] >= 100:
            return False
        
        # 计算修理所需金币
        repair_cost = 10 * tool["level"]
        
        if not self.spend_coins(repair_cost):
            return False
        
        # 修理工具
        tool["durability"] = 100
        
        self._log_resource_change(f"tool_{tool_name}", 0, "repair")
        
        return True
    
    def use_tool(self, tool_name: str) -> bool:
        """
        使用工具，降低耐久度
        
        Args:
            tool_name: 工具名称
            
        Returns:
            是否可以使用（工具是否可用）
        """
        if tool_name not in self.tools:
            return False
        
        tool = self.tools[tool_name]
        
        # 检查工具是否损坏
        if tool["durability"] <= 0:
            return False
        
        # 降低耐久度
        tool["durability"] -= 1
        
        return True
    
    def _log_resource_change(self, resource_type: str, amount: float, change_type: str):
        """
        记录资源变化
        
        Args:
            resource_type: 资源类型
            amount: 变化数量
            change_type: 变化类型（addition, consumption, harvest, sale, upgrade, repair）
        """
        log_entry = {
            "timestamp": time.time(),
            "resource_type": resource_type,
            "amount": amount,
            "change_type": change_type
        }
        
        # 限制日志大小
        self.resource_log.append(log_entry)
        if len(self.resource_log) > 1000:
            self.resource_log.pop(0)
    
    def get_resource_status(self) -> Dict[str, Any]:
        """
        获取资源状态摘要
        
        Returns:
            资源状态摘要
        """
        # 检查资源是否低于阈值
        warnings = []
        
        if self.energy <= self.thresholds["critical_energy"]:
            warnings.append(f"能量严重不足: {self.energy:.1f}/{self.max_energy}")
        elif self.energy <= self.thresholds["low_energy"]:
            warnings.append(f"能量偏低: {self.energy:.1f}/{self.max_energy}")
        
        if self.coins <= self.thresholds["low_coins"]:
            warnings.append(f"金币偏少: {self.coins}")
        
        for plant_type, count in self.seeds.items():
            if count <= self.thresholds["low_seeds"]:
                warnings.append(f"{plant_type} 种子不足: {count}")
        
        # 检查工具耐久度
        for tool_name, tool in self.tools.items():
            if tool["durability"] <= 20:
                warnings.append(f"{tool_name} 耐久度低: {tool['durability']}")
            elif tool["durability"] <= 0:
                warnings.append(f"{tool_name} 已损坏，需要修理")
        
        return {
            "energy": {
                "current": self.energy,
                "max": self.max_energy,
                "percentage": (self.energy / self.max_energy) * 100
            },
            "coins": self.coins,
            "seeds": self.seeds,
            "harvested_crops": self.harvested_crops,
            "tools": self.tools,
            "warnings": warnings,
            "energy_regen_rate": self.energy_regen_rate
        }
    
    def get_recommendations(self) -> List[Dict[str, Any]]:
        """
        获取资源管理建议
        
        Returns:
            建议列表
        """
        recommendations = []
        resource_status = self.get_resource_status()
        
        # 能量相关建议
        if resource_status["energy"]["percentage"] <= 10:
            recommendations.append({
                "priority": "high",
                "action": "休息",
                "message": "能量几乎耗尽，建议停止工作并休息恢复能量"
            })
        elif resource_status["energy"]["percentage"] <= 30:
            recommendations.append({
                "priority": "medium",
                "action": "节约能量",
                "message": "能量偏低，建议优先执行重要任务"
            })
        
        # 金币相关建议
        if self.coins >= 100 and self._can_upgrade_tools():
            recommendations.append({
                "priority": "medium",
                "action": "升级工具",
                "message": "金币充足，可以考虑升级工具以提高工作效率"
            })
        
        # 检查是否有可出售的农产品
        total_crops = sum(self.harvested_crops.values())
        if total_crops >= 20 and self.coins <= 50:
            recommendations.append({
                "priority": "medium",
                "action": "出售农产品",
                "message": f"库存有 {total_crops} 个农产品，可以出售换取金币"
            })
        
        # 种子相关建议
        empty_seed_types = [plant_type for plant_type, count in self.seeds.items() if count <= 0]
        if empty_seed_types and self.coins >= 10:
            recommendations.append({
                "priority": "medium",
                "action": "购买种子",
                "message": f"{', '.join(empty_seed_types)} 种子已耗尽，可以考虑购买"
            })
        
        # 工具相关建议
        for tool_name, tool in self.tools.items():
            if tool["durability"] <= 0:
                recommendations.append({
                    "priority": "high",
                    "action": f"修理 {tool_name}",
                    "message": f"{tool_name} 已损坏，无法使用，请及时修理"
                })
            elif tool["durability"] <= 20:
                recommendations.append({
                    "priority": "low",
                    "action": f"修理 {tool_name}",
                    "message": f"{tool_name} 耐久度低，建议修理"
                })
        
        return recommendations
    
    def _can_upgrade_tools(self) -> bool:
        """
        检查是否有工具可以升级
        
        Returns:
            是否有可升级的工具
        """
        for tool_name, tool in self.tools.items():
            upgrade_cost = 50 * (tool["level"] ** 2)
            if self.coins >= upgrade_cost and tool["level"] < 5:  # 假设最高5级
                return True
        return False
    
    def calculate_task_cost(self, task_type: str, **kwargs) -> Dict[str, Any]:
        """
        计算任务的资源消耗
        
        Args:
            task_type: 任务类型
            **kwargs: 任务参数
            
        Returns:
            资源消耗估算
        """
        # 基础消耗
        base_costs = {
            "sow": {"energy": 2.0, "seeds": 1},
            "water": {"energy": 1.0},
            "weed": {"energy": 1.5},
            "harvest": {"energy": 3.0},
            "scan": {"energy": 0.2},
            "move": {"energy": 0.5}
        }
        
        if task_type not in base_costs:
            return {"energy": 0, "coins": 0, "seeds": 0}
        
        cost = base_costs[task_type].copy()
        
        # 应用工具效率修正
        if task_type in ["water", "weed", "harvest", "scan"]:
            # 确定对应的工具
            tool_mapping = {
                "water": "watering_can",
                "weed": "weeder",
                "harvest": "harvester",
                "scan": "scanner"
            }
            
            tool_name = tool_mapping[task_type]
            if tool_name in self.tools:
                tool = self.tools[tool_name]
                # 工具效率提高，降低能量消耗
                efficiency = tool["efficiency"]
                cost["energy"] /= efficiency
                
                # 工具耐久度降低
                # 注意：这里只是计算，实际使用在执行任务时
        
        # 移动任务的能量消耗与距离相关
        if task_type == "move" and "distance" in kwargs:
            cost["energy"] *= kwargs["distance"]
        
        # 确保能量消耗为正数
        cost["energy"] = max(0.1, cost["energy"])
        
        return cost
    
    def can_afford_task(self, task_type: str, **kwargs) -> Tuple[bool, Dict[str, str]]:
        """
        检查是否有足够资源执行任务
        
        Args:
            task_type: 任务类型
            **kwargs: 任务参数
            
        Returns:
            (是否可以执行, 错误消息)
        """
        can_afford = True
        errors = {}
        
        # 计算任务成本
        cost = self.calculate_task_cost(task_type, **kwargs)
        
        # 检查能量
        if "energy" in cost and self.energy < cost["energy"]:
            can_afford = False
            errors["energy"] = f"能量不足，需要 {cost['energy']:.1f}，当前 {self.energy:.1f}"
        
        # 检查种子
        if "seeds" in cost and task_type == "sow":
            plant_type = kwargs.get("plant_type", "wheat")
            if plant_type not in self.seeds or self.seeds[plant_type] < cost["seeds"]:
                can_afford = False
                current_seeds = self.seeds.get(plant_type, 0)
                errors["seeds"] = f"{plant_type} 种子不足，需要 {cost['seeds']}，当前 {current_seeds}"
        
        # 检查工具
        if task_type in ["water", "weed", "harvest", "scan"]:
            tool_mapping = {
                "water": "watering_can",
                "weed": "weeder",
                "harvest": "harvester",
                "scan": "scanner"
            }
            
            tool_name = tool_mapping[task_type]
            if tool_name in self.tools and self.tools[tool_name]["durability"] <= 0:
                can_afford = False
                errors["tool"] = f"{tool_name} 已损坏，无法执行此任务"
        
        return (can_afford, errors)
    
    def simulate_resource_usage(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        模拟执行一系列任务的资源使用情况
        
        Args:
            tasks: 任务列表
            
        Returns:
            资源使用模拟结果
        """
        # 复制当前资源状态
        sim_energy = self.energy
        sim_coins = self.coins
        sim_seeds = self.seeds.copy()
        sim_harvested = self.harvested_crops.copy()
        
        # 执行模拟
        completed_tasks = 0
        failed_tasks = 0
        total_energy_used = 0
        total_coins_earned = 0
        
        for task in tasks:
            task_type = task.get("task_type")
            
            # 计算任务成本
            cost = self.calculate_task_cost(task_type, **task)
            
            # 检查资源是否足够
            task_possible = True
            
            if sim_energy < cost.get("energy", 0):
                task_possible = False
            
            if task_type == "sow":
                plant_type = task.get("plant_type", "wheat")
                if sim_seeds.get(plant_type, 0) < cost.get("seeds", 0):
                    task_possible = False
            
            # 执行任务
            if task_possible:
                # 消耗资源
                sim_energy -= cost.get("energy", 0)
                total_energy_used += cost.get("energy", 0)
                
                if task_type == "sow":
                    plant_type = task.get("plant_type", "wheat")
                    sim_seeds[plant_type] -= cost.get("seeds", 0)
                
                # 收获任务获得产品
                if task_type == "harvest":
                    plant_type = task.get("plant_type", "wheat")
                    # 模拟产量
                    base_yield = {
                        "wheat": 10,
                        "corn": 8,
                        "carrot": 12,
                        "tomato": 6
                    }
                    yield_amount = base_yield.get(plant_type, 10)
                    
                    if plant_type not in sim_harvested:
                        sim_harvested[plant_type] = 0
                    
                    sim_harvested[plant_type] += yield_amount
                    
                    # 模拟金币收入（如果直接出售）
                    crop_prices = {
                        "wheat": 1,
                        "corn": 2,
                        "carrot": 1,
                        "tomato": 3
                    }
                    coins = yield_amount * crop_prices.get(plant_type, 1)
                    sim_coins += coins
                    total_coins_earned += coins
                
                completed_tasks += 1
            else:
                failed_tasks += 1
        
        # 计算收益比（金币收入/能量消耗）
        energy_efficiency = total_coins_earned / total_energy_used if total_energy_used > 0 else 0
        
        return {
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "final_energy": sim_energy,
            "final_coins": sim_coins,
            "final_seeds": sim_seeds,
            "final_harvested": sim_harvested,
            "total_energy_used": total_energy_used,
            "total_coins_earned": total_coins_earned,
            "energy_efficiency": energy_efficiency,
            "recommendation": "继续执行" if sim_energy > 20 else "需要补充能量"
        }
