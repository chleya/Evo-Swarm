"""
Emergence Intelligence (涌现智能)

实现群体智能的涌现机制。
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import numpy as np
import sys
sys.path.append('../..')
from base import SwarmBase


@dataclass
class EmergenceRule:
    """涌现规则"""
    name: str
    local_condition: callable
    global_effect: callable
    activation_threshold: float = 0.5
    priority: int = 0


class EmergenceIntelligence(SwarmBase):
    """
    涌现智能
    
    管理群体行为的涌现过程。
    
    特点：
    - 基于局部规则
    - 自组织行为
    - 全局模式形成
    """
    
    def __init__(self):
        super().__init__()
        self.rules: List[EmergenceRule] = []
        self.emergent_behaviors: Dict[str, Any] = {}
        self.global_patterns: Dict[str, Any] = {}
        self.emergence_history: List[Dict] = []
    
    def add_rule(self, rule: EmergenceRule):
        """添加涌现规则"""
        self.rules.append(rule)
        self.rules.sort(key=lambda r: r.priority)
    
    def detect_emergence(self, 
                         agents: Dict[str, Any],
                         environment: Dict) -> Dict:
        """
        检测涌现行为
        
        Args:
            agents: 智能体字典
            environment: 环境信息
            
        Returns:
            检测到的涌现行为
        """
        emergent = {}
        
        for rule in self.rules:
            # 检查局部条件
            local_states = [
                rule.local_condition(agent, agents, environment)
                for agent in agents.values()
            ]
            
            # 计算激活程度
            activation = np.mean(local_states)
            
            if activation >= rule.activation_threshold:
                # 应用全局效应
                effect = rule.global_effect(agents, environment, local_states)
                emergent[rule.name] = {
                    'activation': activation,
                    'effect': effect
                }
                
                self.emergence_history.append({
                    'rule': rule.name,
                    'activation': activation,
                    'timestamp': len(self.emergence_history)
                })
        
        self.emergent_behaviors = emergent
        return emergent
    
    def get_global_pattern(self, 
                           agents: Dict[str, Any],
                           pattern_type: str) -> Dict:
        """
        获取全局模式
        
        Args:
            agents: 智能体字典
            pattern_type: 模式类型
            
        Returns:
            全局模式信息
        """
        if pattern_type == "flocking":
            return self._analyze_flocking(agents)
        elif pattern_type == "clustering":
            return self._analyze_clustering(agents)
        elif pattern_type == "coordination":
            return self._analyze_coordination(agents)
        else:
            return {}
    
    def _analyze_flocking(self, agents: Dict) -> Dict:
        """分析群集模式"""
        positions = np.array([agent.position for agent in agents.values()])
        
        # 计算中心
        center = np.mean(positions, axis=0)
        
        # 计算分散度
        dispersion = np.std(positions, axis=0)
        
        # 计算平均速度
        velocities = np.array([agent.velocity for agent in agents.values()])
        avg_velocity = np.mean(velocities, axis=0)
        
        # 检查是否形成群集
        is_flocking = np.linalg.norm(avg_velocity) > 0.1 and np.all(dispersion < 20)
        
        return {
            'type': 'flocking',
            'center': center.tolist(),
            'dispersion': dispersion.tolist(),
            'avg_velocity': avg_velocity.tolist(),
            'is_flocking': is_flocking
        }
    
    def _analyze_clustering(self, agents: Dict) -> Dict:
        """分析聚类模式"""
        positions = np.array([agent.position for agent in agents.values()])
        
        # 简化的聚类检测
        n = len(positions)
        if n < 2:
            return {'type': 'clustering', 'clusters': 1}
        
        # 计算距离矩阵
        distances = np.zeros((n, n))
        for i in range(n):
            for j in range(i + 1, n):
                d = np.linalg.norm(positions[i] - positions[j])
                distances[i, j] = d
                distances[j, i] = d
        
        # 简单聚类（基于阈值）
        threshold = 5.0
        clusters = []
        assigned = set()
        
        for i in range(n):
            if i in assigned:
                continue
            
            cluster = [i]
            assigned.add(i)
            
            for j in range(n):
                if j not in assigned and distances[i, j] < threshold:
                    cluster.append(j)
                    assigned.add(j)
            
            clusters.append(cluster)
        
        return {
            'type': 'clustering',
            'num_clusters': len(clusters),
            'cluster_sizes': [len(c) for c in clusters]
        }
    
    def _analyze_coordination(self, agents: Dict) -> Dict:
        """分析协调模式"""
        states = [agent.state.value for agent in agents.values()]
        
        # 计算状态一致性
        state_counts = {}
        for state in states:
            state_counts[state] = state_counts.get(state, 0) + 1
        
        consistency = max(state_counts.values()) / len(states) if states else 0
        
        return {
            'type': 'coordination',
            'state_distribution': state_counts,
            'consistency': consistency,
            'is_coordinated': consistency > 0.7
        }
    
    def apply_emergent_behavior(self,
                                emergent: Dict,
                                agents: Dict[str, Any]):
        """应用涌现行为"""
        for behavior, info in emergent.items():
            effect = info.get('effect')
            
            if effect and isinstance(effect, dict):
                # 修改智能体行为
                if 'velocity_change' in effect:
                    change = np.array(effect['velocity_change'])
                    for agent in agents.values():
                        agent.velocity += change * 0.1
    
    def get_info(self) -> dict:
        return {
            'name': 'EmergenceIntelligence',
            'num_rules': len(self.rules),
            'num_emergent_behaviors': len(self.emergent_behaviors),
            'emergence_history_length': len(self.emergence_history),
            'description': '涌现智能，管理群体行为的涌现'
        }


class FlockingBehavior(EmergenceIntelligence):
    """群集行为"""
    
    def __init__(self,
                 separation_weight: float = 1.5,
                 alignment_weight: float = 1.0,
                 cohesion_weight: float = 1.0,
                 neighbor_radius: float = 5.0):
        super().__init__()
        self.separation_weight = separation_weight
        self.alignment_weight = alignment_weight
        self.cohesion_weight = cohesion_weight
        self.neighbor_radius = neighbor_radius
    
    def apply_flocking(self, agent_id: str, agents: Dict) -> np.ndarray:
        """
        应用群集规则
        
        Args:
            agent_id: 智能体ID
            agents: 智能体字典
            
        Returns:
            速度变化量
        """
        agent = agents.get(agent_id)
        if not agent:
            return np.zeros(2)
        
        # 找到邻居
        neighbors = []
        for other_id, other in agents.items():
            if other_id != agent_id:
                dist = np.linalg.norm(agent.position - other.position)
                if dist < self.neighbor_radius:
                    neighbors.append(other)
        
        if not neighbors:
            return np.zeros(2)
        
        # 分离
        separation = np.zeros(2)
        for neighbor in neighbors:
            diff = agent.position - neighbor.position
            diff = diff / (np.linalg.norm(diff) + 1e-10)
            separation += diff
        separation /= len(neighbors)
        
        # 对齐
        alignment = np.mean([n.velocity for n in neighbors], axis=0)
        
        # 凝聚
        center = np.mean([n.position for n in neighbors], axis=0)
        cohesion = center - agent.position
        
        # 组合
        velocity_change = (
            self.separation_weight * separation +
            self.alignment_weight * alignment +
            self.cohesion_weight * cohesion
        )
        
        return velocity_change
    
    def get_info(self) -> dict:
        info = super().get_info()
        info['type'] = 'flocking'
        info['separation_weight'] = self.separation_weight
        info['alignment_weight'] = self.alignment_weight
        info['cohesion_weight'] = self.cohesion_weight
        return info
