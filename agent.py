"""
Agent Implementation (智能体实现)

实现演化智能体的核心功能。
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import uuid
import numpy as np
import sys
sys.path.append('../..')
from base import SwarmBase


class AgentState(Enum):
    """智能体状态"""
    IDLE = "idle"
    ACTIVE = "active"
    COMMUNICATING = "communicating"
    LEARNING = "learning"
    RESTING = "resting"
    ERROR = "error"


@dataclass
class AgentConfig:
    """智能体配置"""
    id: str = ""
    name: str = ""
    state: AgentState = AgentState.IDLE
    behavior_rules: Dict = field(default_factory=dict)
    learning_rate: float = 0.01
    memory_size: int = 100
    communication_range: float = 10.0
    position: np.ndarray = None
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())[:8]


class EvoAgent(SwarmBase):
    """
    演化智能体
    
    具有学习、适应和通信能力的自主智能体。
    
    特点：
    - 基于规则的行为
    - 在线学习能力
    - 通信和协作
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        """
        初始化智能体
        
        Args:
            config: 智能体配置
        """
        super().__init__()
        self.config = config or AgentConfig()
        self.id = self.config.id
        self.state = self.config.state
        self.behavior_rules = self.config.behavior_rules
        self.learning_rate = self.config.learning_rate
        self.memory: List[Dict] = []
        self.max_memory = self.config.memory_size
        self.position = self.config.position or np.zeros(2)
        self.velocity = np.zeros(2)
        self.fitness = 0.0
        self.age = 0
        self.interactions = 0
        self.learned_behaviors: Dict[str, Any] = {}
    
    def perceive(self, environment: Dict) -> Dict:
        """
        感知环境
        
        Args:
            environment: 环境信息
            
        Returns:
            感知结果
        """
        perception = {
            'nearby_agents': [],
            'environment_state': environment,
            'local_objectives': self._extract_objectives(environment),
            'threats': self._detect_threats(environment),
            'opportunities': self._identify_opportunities(environment)
        }
        
        # 检测附近智能体
        if 'agent_positions' in environment:
            for agent_id, pos in environment['agent_positions'].items():
                if agent_id != self.id:
                    dist = np.linalg.norm(self.position - pos)
                    if dist < self.config.communication_range:
                        perception['nearby_agents'].append({
                            'id': agent_id,
                            'distance': dist,
                            'direction': (pos - self.position) / (dist + 1e-10)
                        })
        
        return perception
    
    def decide(self, perception: Dict) -> Dict:
        """
        决策
        
        Args:
            perception: 感知结果
            
        Returns:
            决策结果
        """
        decision = {
            'action': 'explore',
            'target': None,
            'parameters': {},
            'confidence': 0.0
        }
        
        # 基于规则决策
        if 'threats' in perception and perception['threats']:
            decision['action'] = 'avoid'
            decision['target'] = perception['threats'][0]
            decision['confidence'] = 0.9
        elif 'opportunities' in perception and perception['opportunities']:
            decision['action'] = 'exploit'
            decision['target'] = perception['opportunities'][0]
            decision['confidence'] = 0.7
        elif self.state == AgentState.IDLE:
            decision['action'] = 'explore'
            decision['target'] = self._select_exploration_target()
            decision['confidence'] = 0.5
        else:
            decision['action'] = 'continue'
            decision['confidence'] = 0.8
        
        # 应用学习到的行为
        if decision['action'] in self.learned_behaviors:
            learned = self.learned_behaviors[decision['action']]
            decision['parameters'].update(learned)
        
        return decision
    
    def act(self, decision: Dict, environment: Dict) -> Dict:
        """
        执行动作
        
        Args:
            decision: 决策结果
            environment: 环境信息
            
        Returns:
            执行结果
        """
        action = decision['action']
        result = {
            'action': action,
            'success': False,
            'reward': 0.0,
            'new_state': self.state,
            'info': {}
        }
        
        if action == 'explore':
            result = self._explore(decision, environment)
        elif action == 'exploit':
            result = self._exploit(decision, environment)
        elif action == 'avoid':
            result = self._avoid(decision, environment)
        elif action == 'communicate':
            result = self._communicate(decision, environment)
        elif action == 'learn':
            result = self._learn(decision, environment)
        
        # 更新状态
        self.state = result['new_state']
        self.age += 1
        
        # 记录到记忆
        self._add_to_memory({
            'perception': decision,
            'action': action,
            'result': result,
            'fitness': result.get('reward', 0)
        })
        
        return result
    
    def _explore(self, decision: Dict, environment: Dict) -> Dict:
        """探索动作"""
        target = decision.get('target')
        
        if target is not None:
            direction = target.get('direction', np.random.randn(2))
            self.velocity = direction * 0.5
            self.position += self.velocity
        
        return {
            'action': 'explore',
            'success': True,
            'reward': 0.1,
            'new_state': AgentState.ACTIVE,
            'info': {'position': self.position.tolist()}
        }
    
    def _exploit(self, decision: Dict, environment: Dict) -> Dict:
        """利用动作"""
        target = decision.get('target')
        
        if target and 'position' in target:
            direction = target['position'] - self.position
            direction = direction / (np.linalg.norm(direction) + 1e-10)
            self.velocity = direction * 0.3
            self.position += self.velocity
        
        return {
            'action': 'exploit',
            'success': True,
            'reward': 0.5,
            'new_state': AgentState.ACTIVE,
            'info': {'position': self.position.tolist()}
        }
    
    def _avoid(self, decision: Dict, environment: Dict) -> Dict:
        """躲避动作"""
        threat = decision.get('target')
        
        if threat and 'position' in threat:
            direction = self.position - threat['position']
            direction = direction / (np.linalg.norm(direction) + 1e-10)
            self.velocity = direction * 0.8
            self.position += self.velocity
        
        return {
            'action': 'avoid',
            'success': True,
            'reward': 0.3,
            'new_state': AgentState.ACTIVE,
            'info': {'evaded': True}
        }
    
    def _communicate(self, decision: Dict, environment: Dict) -> Dict:
        """通信动作"""
        nearby = perception.get('nearby_agents', []) if 'perception' in dir() else []
        
        messages = []
        for agent in nearby:
            messages.append({
                'to': agent['id'],
                'content': self._generate_message()
            })
        
        return {
            'action': 'communicate',
            'success': len(messages) > 0,
            'reward': 0.2,
            'new_state': AgentState.COMMUNICATING,
            'info': {'messages_sent': len(messages)}
        }
    
    def _learn(self, decision: Dict, environment: Dict) -> Dict:
        """学习动作"""
        # 基于经验更新行为
        recent_exp = self.memory[-10:]
        
        for exp in recent_exp:
            if exp['result']['success']:
                action = exp['action']
                if action not in self.learned_behaviors:
                    self.learned_behaviors[action] = {}
                
                # 简单更新
                self.learned_behaviors[action].update({
                    'success_rate': self.learned_behaviors[action].get('success_rate', 0) + 0.1
                })
        
        return {
            'action': 'learn',
            'success': True,
            'reward': 0.1,
            'new_state': AgentState.LEARNING,
            'info': {'learned_behaviors': len(self.learned_behaviors)}
        }
    
    def _extract_objectives(self, environment: Dict) -> List[Dict]:
        """提取目标"""
        objectives = []
        if 'targets' in environment:
            for target in environment['targets']:
                objectives.append({
                    'id': target.get('id'),
                    'value': target.get('value', 1.0),
                    'distance': np.linalg.norm(self.position - target.get('position', np.zeros(2)))
                })
        return objectives
    
    def _detect_threats(self, environment: Dict) -> List[Dict]:
        """检测威胁"""
        threats = []
        if 'hazards' in environment:
            for hazard in environment['hazards']:
                dist = np.linalg.norm(self.position - hazard.get('position', np.zeros(2)))
                if dist < hazard.get('range', 5.0):
                    threats.append({
                        'id': hazard.get('id'),
                        'position': hazard.get('position'),
                        'severity': hazard.get('severity', 1.0),
                        'distance': dist
                    })
        return threats
    
    def _identify_opportunities(self, environment: Dict) -> List[Dict]:
        """识别机会"""
        opportunities = []
        if 'resources' in environment:
            for resource in environment['resources']:
                dist = np.linalg.norm(self.position - resource.get('position', np.zeros(2)))
                opportunities.append({
                    'id': resource.get('id'),
                    'value': resource.get('value', 1.0),
                    'distance': dist
                })
        return opportunities
    
    def _select_exploration_target(self) -> Dict:
        """选择探索目标"""
        angle = np.random.uniform(0, 2 * np.pi)
        distance = np.random.uniform(1, 5)
        
        return {
            'direction': np.array([np.cos(angle), np.sin(angle)]) * distance
        }
    
    def _generate_message(self) -> Dict:
        """生成消息"""
        return {
            'type': 'status',
            'fitness': self.fitness,
            'position': self.position.tolist(),
            'capabilities': list(self.learned_behaviors.keys())
        }
    
    def _add_to_memory(self, experience: Dict):
        """添加到记忆"""
        self.memory.append(experience)
        if len(self.memory) > self.max_memory:
            self.memory.pop(0)
    
    def communicate(self, message: Dict) -> Dict:
        """接收通信"""
        self.interactions += 1
        
        response = {
            'from': self.id,
            'acknowledged': True,
            'message': message
        }
        
        return response
    
    def get_info(self) -> dict:
        return {
            'name': 'EvoAgent',
            'id': self.id,
            'state': self.state.value,
            'fitness': self.fitness,
            'age': self.age,
            'interactions': self.interactions,
            'learned_behaviors': len(self.learned_behaviors),
            'description': '演化智能体'
        }


class SpecializedAgent(EvoAgent):
    """
    专业智能体
    
    针对特定任务优化的智能体。
    """
    
    def __init__(self,
                 specialization: str,
                 config: Optional[AgentConfig] = None):
        super().__init__(config)
        self.specialization = specialization
        self.expertise = {}
    
    def decide(self, perception: Dict) -> Dict:
        """专业决策"""
        decision = super().decide(perception)
        
        # 应用专业知识
        if self.specialization in self.expertise:
            expertise_decision = self.expertise[self.specialization](perception)
            decision.update(expertise_decision)
        
        return decision
    
    def add_expertise(self, task: str, expertise_fn: callable):
        """添加专业知识"""
        self.expertise[task] = expertise_fn
    
    def get_info(self) -> dict:
        info = super().get_info()
        info['specialization'] = self.specialization
        return info
