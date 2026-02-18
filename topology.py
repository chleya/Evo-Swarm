"""
Topology Management (网络拓扑)

管理智能体群体的网络拓扑结构。
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
import random
import sys
sys.path.append('../..')
from base import SwarmBase


class Topology(Enum):
    """网络拓扑类型"""
    FULLY_CONNECTED = "fully_connected"
    MESH = "mesh"
    RING = "ring"
    STAR = "star"
    TREE = "tree"
    RANDOM = "random"
    SMALL_WORLD = "small_world"
    SCALE_FREE = "scale_free"


@dataclass
class Edge:
    """边"""
    source: str
    target: str
    weight: float = 1.0
    directed: bool = False


class TopologyManager(SwarmBase):
    """
    拓扑管理器
    
    管理智能体群体的网络拓扑。
    
    特点：
    - 多种拓扑类型
    - 动态拓扑变化
    - 拓扑度量计算
    """
    
    def __init__(self):
        super().__init__()
        self.edges: List[Edge] = []
        self.adjacency: Dict[str, List[str]] = {}
        self.topology_type: Optional[Topology] = None
    
    def build_topology(self,
                       agent_ids: List[str],
                       topology_type: Topology,
                       params: Optional[Dict] = None) -> Dict[str, List[str]]:
        """
        构建拓扑
        
        Args:
            agent_ids: 智能体ID列表
            topology_type: 拓扑类型
            params: 拓扑参数
            
        Returns:
            邻接表
        """
        params = params or {}
        self.topology_type = topology_type
        self.edges = []
        self.adjacency = {aid: [] for aid in agent_ids}
        
        if topology_type == Topology.FULLY_CONNECTED:
            return self._fully_connected(agent_ids)
        elif topology_type == Topology.MESH:
            return self._mesh(agent_ids, params)
        elif topology_type == Topology.RING:
            return self._ring(agent_ids)
        elif topology_type == Topology.STAR:
            return self._star(agent_ids, params)
        elif topology_type == Topology.RANDOM:
            return self._random(agent_ids, params)
        elif topology_type == Topology.SMALL_WORLD:
            return self._small_world(agent_ids, params)
        elif topology_type == Topology.SCALE_FREE:
            return self._scale_free(agent_ids, params)
        else:
            return self.adjacency
    
    def _fully_connected(self, agent_ids: List[str]) -> Dict:
        """全连接拓扑"""
        n = len(agent_ids)
        for i, source in enumerate(agent_ids):
            for j, target in enumerate(agent_ids):
                if i != j:
                    self.adjacency[source].append(target)
                    self.edges.append(Edge(source, target))
        return self.adjacency
    
    def _mesh(self, agent_ids: List[str], params: Dict) -> Dict:
        """网格拓扑"""
        n = len(agent_ids)
        k = params.get('neighbors', 4)
        k = min(k, n - 1)
        
        for i, source in enumerate(agent_ids):
            # 连接到最近的k个
            others = [(j, abs(i - j)) for j in range(n) if j != i]
            others.sort(key=lambda x: x[1])
            
            for j, _ in others[:k]:
                target = agent_ids[j]
                self.adjacency[source].append(target)
                self.edges.append(Edge(source, target))
        
        return self.adjacency
    
    def _ring(self, agent_ids: List[str]) -> Dict:
        """环状拓扑"""
        n = len(agent_ids)
        for i, source in enumerate(agent_ids):
            left = agent_ids[(i - 1) % n]
            right = agent_ids[(i + 1) % n]
            
            self.adjacency[source].extend([left, right])
            self.edges.extend([Edge(source, left), Edge(source, right)])
        
        return self.adjacency
    
    def _star(self, agent_ids: List[str], params: Dict) -> Dict:
        """星形拓扑"""
        center = params.get('center', agent_ids[0])
        
        for agent_id in agent_ids:
            if agent_id != center:
                self.adjacency[center].append(agent_id)
                self.adjacency[agent_id].append(center)
                self.edges.append(Edge(center, agent_id))
        
        return self.adjacency
    
    def _random(self, agent_ids: List[str], params: Dict) -> Dict:
        """随机拓扑"""
        n = len(agent_ids)
        probability = params.get('probability', 0.3)
        
        for i, source in enumerate(agent_ids):
            for j, target in enumerate(agent_ids):
                if i != j and random.random() < probability:
                    self.adjacency[source].append(target)
                    self.edges.append(Edge(source, target))
        
        return self.adjacency
    
    def _small_world(self, agent_ids: List[str], params: Dict) -> Dict:
        """小世界拓扑（Watts-Strogatz）"""
        n = len(agent_ids)
        k = params.get('k', 4)  # 每个节点的邻居数
        beta = params.get('beta', 0.3)  # 重连概率
        
        # 先构建环状
        self._ring(agent_ids)
        
        # 随机重连
        for i, source in enumerate(agent_ids):
            neighbors = self.adjacency[source][:]
            for neighbor in neighbors:
                if random.random() < beta:
                    # 移除现有边
                    self.adjacency[source].remove(neighbor)
                    self.edges = [e for e in self.edges 
                                 if not (e.source == source and e.target == neighbor)]
                    
                    # 连接到随机节点
                    new_target = random.choice([a for a in agent_ids 
                                               if a != source and a not in self.adjacency[source]])
                    self.adjacency[source].append(new_target)
                    self.edges.append(Edge(source, new_target))
        
        return self.adjacency
    
    def _scale_free(self, agent_ids: List[str], params: Dict) -> Dict:
        """无标度拓扑（Barabási-Albert）"""
        n = len(agent_ids)
        m = params.get('m', 2)  # 新节点连接的边数
        
        # 初始完全连接
        initial = min(m + 1, n)
        initial_nodes = agent_ids[:initial]
        
        for i in range(len(initial_nodes)):
            for j in range(i + 1, len(initial_nodes)):
                source = initial_nodes[i]
                target = initial_nodes[j]
                self.adjacency[source].append(target)
                self.adjacency[target].append(source)
                self.edges.append(Edge(source, target))
        
        # 优先连接
        for i in range(initial, n):
            source = agent_ids[i]
            degrees = {nid: len(self.adjacency[nid]) for nid in agent_ids[:i]}
            total_degree = sum(degrees.values())
            
            targets = set()
            while len(targets) < m and len(targets) < i:
                nodes = list(degrees.keys())
                probs = [degrees[n] / total_degree for n in nodes]
                selected = np.random.choice(nodes, p=probs)
                targets.add(selected)
            
            for target in targets:
                self.adjacency[source].append(target)
                self.adjacency[target].append(source)
                self.edges.append(Edge(source, target))
        
        return self.adjacency
    
    def get_topology_metrics(self) -> Dict:
        """获取拓扑度量"""
        n = len(self.adjacency)
        if n == 0:
            return {}
        
        # 度分布
        degrees = [len(neighbors) for neighbors in self.adjacency.values()]
        
        # 平均度
        avg_degree = np.mean(degrees)
        
        # 聚类系数
        clustering = self._calculate_clustering()
        
        # 平均路径长度
        avg_path = self._calculate_avg_path()
        
        return {
            'num_nodes': n,
            'num_edges': len(self.edges),
            'avg_degree': avg_degree,
            'degree_std': np.std(degrees),
            'clustering_coefficient': clustering,
            'avg_path_length': avg_path,
            'topology_type': self.topology_type.value if self.topology_type else None
        }
    
    def _calculate_clustering(self) -> float:
        """计算聚类系数"""
        n = len(self.adjacency)
        if n == 0:
            return 0.0
        
        total_clustering = 0.0
        
        for node in self.adjacency:
            neighbors = self.adjacency[node]
            k = len(neighbors)
            
            if k < 2:
                continue
            
            # 计算邻居之间的连接数
            edges = 0
            for i, n1 in enumerate(neighbors):
                for n2 in neighbors[i + 1:]:
                    if n2 in self.adjacency[n1]:
                        edges += 1
            
            total_clustering += 2 * edges / (k * (k - 1))
        
        return total_clustering / n if n > 0 else 0.0
    
    def _calculate_avg_path(self) -> float:
        """计算平均路径长度"""
        n = len(self.adjacency)
        if n == 0:
            return float('inf')
        
        # BFS计算所有对最短路径
        total_path = 0.0
        pairs = 0
        
        for source in self.adjacency:
            distances = self._bfs(source)
            
            for target, dist in distances.items():
                if target != source and dist < float('inf'):
                    total_path += dist
                    pairs += 1
        
        return total_path / pairs if pairs > 0 else float('inf')
    
    def _bfs(self, source: str) -> Dict[str, int]:
        """BFS计算最短路径"""
        distances = {source: 0}
        queue = [source]
        
        while queue:
            node = queue.pop(0)
            
            for neighbor in self.adjacency.get(node, []):
                if neighbor not in distances:
                    distances[neighbor] = distances[node] + 1
                    queue.append(neighbor)
        
        return distances
    
    def evolve_topology(self, 
                        performance: Dict[str, float],
                        evolution_rate: float = 0.1):
        """演化拓扑"""
        # 移除低性能连接
        edges_to_remove = []
        
        for edge in self.edges:
            if edge.source in performance and edge.target in performance:
                # 基于性能差移除边
                perf_diff = abs(performance[edge.source] - performance[edge.target])
                if random.random() < evolution_rate * perf_diff:
                    edges_to_remove.append(edge)
        
        for edge in edges_to_remove:
            if edge.target in self.adjacency[edge.source]:
                self.adjacency[edge.source].remove(edge.target)
            self.edges.remove(edge)
        
        return len(edges_to_remove)
    
    def get_info(self) -> dict:
        metrics = self.get_topology_metrics()
        return {
            'name': 'TopologyManager',
            'topology_type': self.topology_type.value if self.topology_type else None,
            'metrics': metrics,
            'description': '拓扑管理器，管理网络拓扑结构'
        }
