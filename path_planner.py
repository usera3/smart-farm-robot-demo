#!/usr/bin/env python3
"""
智能农场路径规划模块
负责计算机器人在农田中的最优移动路径
"""
import heapq
import math
from typing import List, Dict, Tuple, Optional, Set

class PathPlanner:
    """
    路径规划器
    使用A*算法计算最优路径
    """
    def __init__(self, grid_size: int = 8, cell_size: float = 0.5):
        self.grid_size = grid_size  # 网格大小
        self.cell_size = cell_size  # 每个单元格的实际大小（米）
        self.obstacles = set()  # 障碍物集合，存储(行,列)坐标
        
    def add_obstacle(self, row: int, col: int):
        """添加障碍物
        
        Args:
            row: 行坐标
            col: 列坐标
        """
        if 0 <= row < self.grid_size and 0 <= col < self.grid_size:
            self.obstacles.add((row, col))
    
    def remove_obstacle(self, row: int, col: int):
        """移除障碍物
        
        Args:
            row: 行坐标
            col: 列坐标
        """
        obstacle = (row, col)
        if obstacle in self.obstacles:
            self.obstacles.remove(obstacle)
    
    def is_valid_position(self, row: int, col: int) -> bool:
        """检查位置是否有效（在网格范围内且不是障碍物）
        
        Args:
            row: 行坐标
            col: 列坐标
            
        Returns:
            位置是否有效
        """
        return (0 <= row < self.grid_size and 
                0 <= col < self.grid_size and 
                (row, col) not in self.obstacles)
    
    def grid_to_world(self, row: int, col: int) -> Tuple[float, float]:
        """将网格坐标转换为世界坐标
        
        Args:
            row: 行坐标
            col: 列坐标
            
        Returns:
            (x, z) 世界坐标
        """
        # 假设网格中心在世界坐标的(0,0)点
        offset_x = -2.0  # 与server_game.py中的offset_x保持一致
        offset_z = -2.0  # 与server_game.py中的offset_z保持一致
        
        x = offset_x + col * self.cell_size + self.cell_size / 2
        z = offset_z + row * self.cell_size + self.cell_size / 2
        
        return (x, z)
    
    def world_to_grid(self, x: float, z: float) -> Tuple[int, int]:
        """将世界坐标转换为网格坐标
        
        Args:
            x: 世界X坐标
            z: 世界Z坐标
            
        Returns:
            (row, col) 网格坐标
        """
        offset_x = -2.0
        offset_z = -2.0
        
        col = int((x - offset_x) / self.cell_size)
        row = int((z - offset_z) / self.cell_size)
        
        return (row, col)
    
    def calculate_path(self, start_row: int, start_col: int, 
                      goal_row: int, goal_col: int) -> Optional[List[Tuple[int, int]]]:
        """使用A*算法计算从起点到终点的最优路径
        
        Args:
            start_row: 起点行坐标
            start_col: 起点列坐标
            goal_row: 终点行坐标
            goal_col: 终点列坐标
            
        Returns:
            路径坐标列表，每个元素为(row, col)，如果无法到达则返回None
        """
        # 检查起点和终点是否有效
        if not (self.is_valid_position(start_row, start_col) and 
                self.is_valid_position(goal_row, goal_col)):
            return None
        
        # 特殊情况：起点就是终点
        if start_row == goal_row and start_col == goal_col:
            return [(start_row, start_col)]
        
        # 定义启发函数（曼哈顿距离）
        def heuristic(row, col):
            return abs(row - goal_row) + abs(col - goal_col)
        
        # 定义移动方向（上下左右以及对角线）
        directions = [
            (-1, 0), (1, 0), (0, -1), (0, 1),  # 上下左右
            (-1, -1), (-1, 1), (1, -1), (1, 1)  # 对角线
        ]
        
        # 初始化开放列表和闭合列表
        open_set = []  # 优先队列 (f_score, row, col)
        heapq.heappush(open_set, (heuristic(start_row, start_col), start_row, start_col))
        
        came_from = {}  # 记录路径
        
        # 记录g_score（从起点到当前位置的实际代价）和f_score（g_score + 启发值）
        g_score = {}
        f_score = {}
        
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                g_score[(r, c)] = float('inf')
                f_score[(r, c)] = float('inf')
        
        g_score[(start_row, start_col)] = 0
        f_score[(start_row, start_col)] = heuristic(start_row, start_col)
        
        # A*算法主循环
        while open_set:
            _, current_row, current_col = heapq.heappop(open_set)
            
            # 到达目标
            if current_row == goal_row and current_col == goal_col:
                # 重建路径
                path = []
                current = (current_row, current_col)
                
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                
                path.append((start_row, start_col))
                path.reverse()  # 反转路径，使其从起点开始
                return path
            
            # 检查所有相邻位置
            for dr, dc in directions:
                neighbor_row = current_row + dr
                neighbor_col = current_col + dc
                
                # 检查相邻位置是否有效
                if not self.is_valid_position(neighbor_row, neighbor_col):
                    continue
                
                # 计算从起点经过当前位置到相邻位置的代价
                # 对角线移动代价为√2，直线移动代价为1
                if abs(dr) + abs(dc) == 2:  # 对角线移动
                    move_cost = math.sqrt(2)
                else:  # 直线移动
                    move_cost = 1
                
                tentative_g_score = g_score[(current_row, current_col)] + move_cost
                
                # 如果找到更好的路径
                if tentative_g_score < g_score[(neighbor_row, neighbor_col)]:
                    came_from[(neighbor_row, neighbor_col)] = (current_row, current_col)
                    g_score[(neighbor_row, neighbor_col)] = tentative_g_score
                    f_score[(neighbor_row, neighbor_col)] = tentative_g_score + heuristic(neighbor_row, neighbor_col)
                    
                    # 如果相邻位置不在开放列表中，则添加
                    if (f_score[(neighbor_row, neighbor_col)], neighbor_row, neighbor_col) not in open_set:
                        heapq.heappush(open_set, (f_score[(neighbor_row, neighbor_col)], neighbor_row, neighbor_col))
        
        # 无法找到路径
        return None
    
    def plan_coverage_path(self, start_row: int, start_col: int) -> List[Tuple[int, int]]:
        """规划覆盖整个农田的路径（Z字形路径）
        
        Args:
            start_row: 起点行坐标
            start_col: 起点列坐标
            
        Returns:
            覆盖路径坐标列表
        """
        path = []
        visited = set()
        
        # 从起点开始，使用Z字形模式覆盖整个网格
        current_row = start_row
        
        # 先处理起点所在行
        if current_row < self.grid_size:
            # 确定是从左到右还是从右到左
            if start_col < self.grid_size // 2:
                # 从起点向左走到行首
                for col in range(start_col, -1, -1):
                    if (current_row, col) not in self.obstacles:
                        path.append((current_row, col))
                        visited.add((current_row, col))
                # 然后从行首向右走到行尾
                for col in range(start_col + 1, self.grid_size):
                    if (current_row, col) not in self.obstacles:
                        path.append((current_row, col))
                        visited.add((current_row, col))
            else:
                # 从起点向右走到行尾
                for col in range(start_col, self.grid_size):
                    if (current_row, col) not in self.obstacles:
                        path.append((current_row, col))
                        visited.add((current_row, col))
                # 然后从行尾向左走到行首
                for col in range(start_col - 1, -1, -1):
                    if (current_row, col) not in self.obstacles:
                        path.append((current_row, col))
                        visited.add((current_row, col))
        
        # 处理剩余的行，使用Z字形模式
        direction = 1  # 1表示向下，-1表示向上
        rows_to_process = list(range(self.grid_size))
        rows_to_process.remove(current_row)  # 移除已经处理的行
        
        # 先处理起点下方的行，再处理起点上方的行
        lower_rows = [r for r in rows_to_process if r > current_row]
        upper_rows = [r for r in rows_to_process if r < current_row]
        
        for row in lower_rows + list(reversed(upper_rows)):
            if direction == 1:  # 偶数行，从左到右
                for col in range(self.grid_size):
                    if (row, col) not in self.obstacles and (row, col) not in visited:
                        path.append((row, col))
                        visited.add((row, col))
            else:  # 奇数行，从右到左
                for col in range(self.grid_size - 1, -1, -1):
                    if (row, col) not in self.obstacles and (row, col) not in visited:
                        path.append((row, col))
                        visited.add((row, col))
            direction *= -1  # 切换方向
        
        return path
    
    def optimize_task_order(self, start_row: int, start_col: int, 
                          tasks: List[Dict[str, any]]) -> List[Dict[str, any]]:
        """优化任务执行顺序，使用贪心算法找到近似最优解
        
        Args:
            start_row: 起点行坐标
            start_col: 起点列坐标
            tasks: 任务列表，每个任务包含'row'和'col'字段
            
        Returns:
            优化后的任务执行顺序
        """
        if not tasks:
            return []
        
        # 过滤掉无效位置的任务
        valid_tasks = [task for task in tasks if self.is_valid_position(task.get('row', -1), task.get('col', -1))]
        
        # 贪心算法：每次选择最近的任务
        optimized_tasks = []
        current_row, current_col = start_row, start_col
        remaining_tasks = valid_tasks.copy()
        
        while remaining_tasks:
            nearest_task = None
            min_distance = float('inf')
            
            # 找到最近的任务
            for i, task in enumerate(remaining_tasks):
                task_row = task.get('row')
                task_col = task.get('col')
                
                # 计算欧几里得距离
                distance = math.sqrt((task_row - current_row) ** 2 + (task_col - current_col) ** 2)
                
                if distance < min_distance:
                    min_distance = distance
                    nearest_task = i
            
            # 添加最近的任务到优化列表
            if nearest_task is not None:
                optimized_task = remaining_tasks.pop(nearest_task)
                optimized_tasks.append(optimized_task)
                current_row = optimized_task.get('row')
                current_col = optimized_task.get('col')
        
        return optimized_tasks
    
    def find_nearest_task(self, current_row: int, current_col: int, 
                         tasks: List[Dict[str, any]]) -> Optional[Dict[str, any]]:
        """找到离当前位置最近的任务
        
        Args:
            current_row: 当前行坐标
            current_col: 当前列坐标
            tasks: 任务列表，每个任务包含'row'和'col'字段
            
        Returns:
            最近的任务，如果没有有效任务则返回None
        """
        if not tasks:
            return None
        
        # 过滤掉无效位置的任务
        valid_tasks = [task for task in tasks if self.is_valid_position(task.get('row', -1), task.get('col', -1))]
        
        if not valid_tasks:
            return None
        
        nearest_task = None
        min_distance = float('inf')
        
        # 找到最近的任务
        for task in valid_tasks:
            task_row = task.get('row')
            task_col = task.get('col')
            
            # 计算欧几里得距离
            distance = math.sqrt((task_row - current_row) ** 2 + (task_col - current_col) ** 2)
            
            if distance < min_distance:
                min_distance = distance
                nearest_task = task
        
        return nearest_task
    
    def calculate_path_length(self, path: List[Tuple[int, int]]) -> float:
        """计算路径长度
        
        Args:
            path: 路径坐标列表
            
        Returns:
            路径总长度（米）
        """
        if not path or len(path) < 2:
            return 0.0
        
        total_length = 0.0
        
        for i in range(1, len(path)):
            prev_row, prev_col = path[i-1]
            curr_row, curr_col = path[i]
            
            # 计算网格距离
            grid_distance = math.sqrt((curr_row - prev_row) ** 2 + (curr_col - prev_col) ** 2)
            
            # 转换为实际距离（米）
            total_length += grid_distance * self.cell_size
        
        return total_length
    
    def visualize_path(self, path: List[Tuple[int, int]]) -> str:
        """可视化路径（用于调试）
        
        Args:
            path: 路径坐标列表
            
        Returns:
            可视化路径的字符串
        """
        # 创建网格表示
        grid = [[' . ' for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        
        # 标记障碍物
        for row, col in self.obstacles:
            grid[row][col] = ' X '
        
        # 标记路径
        for i, (row, col) in enumerate(path):
            if i == 0:
                grid[row][col] = ' S '
            elif i == len(path) - 1:
                grid[row][col] = ' G '
            else:
                grid[row][col] = ' * '
        
        # 生成字符串表示
        result = "\n".join([''.join(row) for row in grid])
        return result
