"""
Swarm Management (群体管理)

实现多智能体群体的管理和协调。
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
import time
import sys
sys.path.append('../..')
from base import SwarmBase
from agent import EvoAgent, AgentConfig, AgentState


class TopologyType(Enum):
    """网络拓扑类型"""
    FULLY_CONNECTED = "fully_connected"
    MESH = "mesh"
    RING = "ring"
    STAR = "star"
    RANDOM = "random"
    SMALL_WORLD = "small_world"
    SCALE_FREE = "scale_free"


@dataclass
class SwarmConfig:
    """群体配置"""
    size: int = 10
    topology: TopologyType = TopologyType.MESH
    communication: str = "broadcast"
    max_agents: int = 100
    agent_class: type = EvoAgent
    shared_memory: bool = True
    neighborhood_range: float = 10.0


class Swarm(SwarmBase):
    """
    智能体群体
    
    管理多个智能体的交互和协作。
    
    特点：
    - 多种网络拓扑
    - 支持群体通信
    - 自组织协调
    """
    
    def __init__(self,
                 config: Optional[SwarmConfig] = None,
                 agents: Optional[List[EvoAgent]] = None):
        """
        初始化群体
        
        Args:
            config: 群体配置
            agents: 初始智能体列表
        """
        super().__init__()
        self.config = config or SwarmConfig()
        self.agents: Dict[str, EvoAgent] = {}
        self.topology = self.config.topology
        self.communication_mode = self.config.communication
        self.neighbors: Dict[str, List[str]] = {}
        self.shared_memory: Dict[str, Any] = {}
        self.position_index: Dict[tuple, List[str]] = {}
        self.generation = 0
        self.global_best_fitness = -float('inf')
        self.global_best_agent = None
        
        # 添加初始智能体
        if agents:
            for agent in agents:
                self.add_agent(agent)
        else:
            # 创建新智能体
            for _ in range(self.config.size):
                agent = self.config.agent_class()
                self.add_agent(agent)
    
    def add_agent(self, agent: EvoAgent):
        """添加智能体"""
        self.agents[agent.id] = agent
        self._update_topology(agent.id)
    
    def remove_agent(self, agent_id: str):
        """移除智能体"""
        if agent_id in self.agents:
            del self.agents[agent_id]
            if agent_id in self.neighbors:
                del self.neighbors[agent_id]
            
            # 从邻居列表中移除
            for neighbors in self.neighbors.values():
                if agent_id in neighbors:
                    neighbors.remove(agent_id)
    
    def step(self, environment: Dict) -> Dict:
        """
        执行一步演化
        
        Args:
            environment: 环境信息
            
        Returns:
            一步的结果
        """
        self.generation += 1
        
        # 准备环境信息
        env_with_positions = environment.copy()
        env_with_positions['agent_positions'] = {
            aid: agent.position 
            for aid, agent in self.agents.items()
        }
        
        # 更新全局最佳
        for agent in self.agents.values():
            if agent.fitness > self.global_best_fitness:
                self.global_best_fitness = agent.fitness
                self.global_best_agent = agent
        
        # 并行执行每个智能体的感知-决策-行动循环
        results = {}
        for agent_id, agent in self.agents.items():
            try:
                perception = agent.perceive(env_with_positions)
                decision = agent.decide(perception)
                result = agent.act(decision, env_with_positions)
                results[agent_id] = result
            except Exception as e:
                results[agent_id] = {'error': str(e)}
        
        # 群体通信
        self._group_communication()
        
        # 更新共享记忆
        if self.config.shared_memory:
            self._update_shared_memory(results)
        
        return {
            'generation': self.generation,
            'num_agents': len(self.agents),
            'global_best_fitness': self.global_best_fitness,
            'results': results
        }
    
    def run(self, 
            num_steps: int, 
            environment: Optional[Dict] = None,
            callback: Optional[Callable] = None):
        """
        运行群体演化
        
        Args:
            num_steps: 演化步数
            environment: 环境信息
            callback: 回调函数
        """
        env = environment or {}
        
        for step in range(num_steps):
            result = self.step(env)
            
            if callback:
                callback(result)
    
    def get_results(self) -> Dict:
        """获取群体结果"""
        agent_results = {}
        for agent_id, agent in self.agents.items():
            agent_results[agent_id] = {
                'fitness': agent.fitness,
                'age': agent.age,
                'position': agent.position.tolist(),
                'state': agent.state.value
            }
        
        return {
            'generation': self.generation,
            'num_agents': len(self.agents),
            'global_best_fitness': self.global_best_fitness,
            'agents': agent_results
        }
    
    def _update_topology(self, agent_id: str):
        """更新网络拓扑"""
        self.neighbors[agent_id] = []
        
        if self.topology == TopologyType.FULLY_CONNECTED:
            for other_id in self.agents:
                if other_id != agent_id:
                    self.neighbors[agent_id].append(other_id)
        
        elif self.topology == TopologyType.MESH:
            for other_id, other_agent in self.agents.items():
                if other_id != agent_id:
                    dist = np.linalg.norm(
                        self.agents[agent_id].position - other_agent.position
                    )
                    if dist < self.config.neighborhood_range:
                        self.neighbors[agent_id].append(other_id)
        
        elif self.topology == TopologyType.RING:
            agent_ids = list(self.agents.keys())
            idx = agent_ids.index(agent_id)
            # 连接到相邻的两个智能体
            prev_idx = (idx - 1) % len(agent_ids)
            next_idx = (idx + 1) % len(agent_ids)
            self.neighbors[agent_id] = [
                agent_ids[prev_idx],
                agent_ids[next_idx]
            ]
    
    def _group_communication(self):
        """群体通信"""
        for agent_id, agent in self.agents.items():
            neighbors = self.neighbors.get(agent_id, [])
            
            for neighbor_id in neighbors:
                neighbor = self.agents.get(neighbor_id)
                if neighbor:
                    message = {
                        'from': agent_id,
                        'content': {
                            'fitness': agent.fitness,
                            'position': agent.position.tolist()
                        }
                    }
                    neighbor.communicate(message)
    
    def _update_shared_memory(self, results: Dict):
        """更新共享记忆"""
        # 记录最佳实践
        best_agent_id = max(results.keys(), 
                           key=lambda aid: self.agents[aid].fitness)
        
        self.shared_memory['best_practice'] = {
            'agent_id': best_agent_id,
            'actions': results[best_agent_id].get('action'),
            'timestamp': time.time()
        }
        
        # 记录群体统计
        fitnesses = [agent.fitness for agent in self.agents.values()]
        self.shared_memory['statistics'] = {
            'mean_fitness': np.mean(fitnesses),
            'std_fitness': np.std(fitnesses),
            'diversity': np.std(fitnesses),
            'timestamp': time.time()
        }
    
    def get_neighborhood(self, agent_id: str) -> List[EvoAgent]:
        """获取邻居智能体"""
        neighbor_ids = self.neighbors.get(agent_id, [])
        return [self.agents[nid] for nid in neighbor_ids if nid in self.agents]
    
    def broadcast(self, message: Dict):
        """广播消息到所有智能体"""
        for agent in self.agents.values():
            agent.communicate(message)
    
    def get_info(self) -> dict:
        return {
            'name': 'Swarm',
            'size': len(self.agents),
            'topology': self.topology.value,
            'communication': self.communication_mode,
            'generation': self.generation,
            'global_best_fitness': self.global_best_fitness,
            'description': '智能体群体'
        }


class HierarchicalSwarm(Swarm):
    """
    层级群体
    
    具有层级结构的智能体群体。
    """
    
    def __init__(self,
                 config: Optional[SwarmConfig] = None,
                 agents: Optional[List[EvoAgent]] = None,
                 num_leaders: int = 3):
        super().__init__(config, agents)
        self.num_leaders = num_leaders
        self.leaders: List[str] = []
        self.followers: Dict[str, str] = {}
    
    def elect_leaders(self):
        """选举领导"""
        # 基于适应度选择领导
        sorted_agents = sorted(
            self.agents.items(),
            key=lambda x: x[1].fitness,
            reverse=True
        )
        
        self.leaders = [aid for aid, _ in sorted_agents[:self.num_leaders]]
        
        # 分配跟随者
        for agent_id in self.agents:
            if agent_id not in self.leaders:
                nearest_leader = min(
                    self.leaders,
                    key=lambda lid: np.linalg.norm(
                        self.agents[agent_id].position - 
                        self.agents[lid].position
                    )
                )
                self.followers[agent_id] = nearest_leader
    
    def step(self, environment: Dict) -> Dict:
        """层级步进"""
        # 先更新领导
        for leader_id in self.leaders:
            leader = self.agents[leader_id]
            env = environment.copy()
            env['subordinates'] = [
                self.agents[follower_id]
                for follower_id, leader in self.followers.items()
                if leader == leader_id and follower_id in self.agents
            ]
            
            perception = leader.perceive(env)
            decision = leader.decide(perception)
            leader.act(decision, env)
        
        # 跟随者跟随领导
        for follower_id, leader_id in self.followers.items():
            follower = self.agents[follower_id]
            leader = self.agents.get(leader_id)
            
            if leader:
                # 移动向领导
                direction = leader.position - follower.position
                direction = direction / (np.linalg.norm(direction) + 1e-10)
                follower.position += direction * 0.3
        
        return super().step(environment)
    
    def get_info(self) -> dict:
        info = super().get_info()
        info['type'] = 'hierarchical'
        info['num_leaders'] = len(self.leaders)
        return info
