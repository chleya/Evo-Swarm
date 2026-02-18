"""
Collaboration Mechanisms (协作机制)

实现智能体间的协作策略。
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
import sys
sys.path.append('../..')
from base import SwarmBase


class TaskType(Enum):
    """任务类型"""
    INDEPENDENT = "independent"
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    COOPERATIVE = "cooperative"
    COMPETITIVE = "competitive"


@dataclass
class Task:
    """任务"""
    id: str
    type: TaskType
    description: str
    requirements: Dict[str, Any] = field(default_factory=dict)
    reward: float = 1.0
    dependencies: List[str] = field(default_factory=list)
    assigned_agents: List[str] = field(default_factory=list)
    status: str = "pending"
    progress: float = 0.0


class CollaborationMechanism(SwarmBase):
    """
    协作机制
    
    管理智能体间的任务分配和协作执行。
    """
    
    def __init__(self, reward_sharing: str = "equal"):
        super().__init__()
        self.reward_sharing = reward_sharing
        self.tasks: Dict[str, Task] = {}
        self.task_assignments: Dict[str, List[str]] = {}
        self.agent_contributions: Dict[str, Dict[str, float]] = {}
    
    def add_task(self, task: Task):
        """添加任务"""
        self.tasks[task.id] = task
        self.task_assignments[task.id] = []
    
    def assign_tasks(self, agents: Dict[str, Any]) -> Dict[str, List[str]]:
        """分配任务"""
        assignments = {}
        
        for task_id, task in self.tasks.items():
            if task.type == TaskType.INDEPENDENT:
                assignments[task_id] = self._assign_independent(task, agents)
            elif task.type == TaskType.PARALLEL:
                assignments[task_id] = self._assign_parallel(task, agents)
            elif task.type == TaskType.COOPERATIVE:
                assignments[task_id] = self._assign_cooperative(task, agents)
        
        self.task_assignments = assignments
        return assignments
    
    def _assign_independent(self, task: Task, agents: Dict) -> List[str]:
        """独立任务分配"""
        best_agent = max(agents.keys(), 
                        key=lambda aid: agents[aid].fitness)
        return [best_agent]
    
    def _assign_parallel(self, task: Task, agents: Dict) -> List[str]:
        """并行任务分配"""
        available = [aid for aid in agents if agents[aid].state.value == 'idle']
        return available[:min(3, len(available))]
    
    def _assign_cooperative(self, task: Task, agents: Dict) -> List[str]:
        """协作任务分配"""
        skilled = [aid for aid in agents 
                  if any(cap in agents[aid].learned_behaviors 
                        for cap in task.requirements.get('capabilities', []))]
        return skilled[:min(5, len(skilled))]
    
    def distribute_rewards(self, task_results: Dict[str, Dict]) -> Dict[str, float]:
        """分配奖励"""
        rewards = {}
        
        for task_id, result in task_results.items():
            task = self.tasks.get(task_id)
            if not task:
                continue
            
            agents = self.task_assignments.get(task_id, [])
            
            if self.reward_sharing == "equal":
                reward_per_agent = task.reward / max(len(agents), 1)
                for agent_id in agents:
                    rewards[agent_id] = rewards.get(agent_id, 0) + reward_per_agent
            
            elif self.reward_sharing == "contribution":
                total_contribution = sum(
                    result.get('contributions', {}).get(aid, 1) for aid in agents
                )
                for agent_id in agents:
                    contribution = result.get('contributions', {}).get(agent_id, 1)
                    share = contribution / total_contribution * task.reward
                    rewards[agent_id] = rewards.get(agent_id, 0) + share
        
        return rewards
    
    def get_info(self) -> dict:
        return {
            'name': 'CollaborationMechanism',
            'task_count': len(self.tasks),
            'reward_sharing': self.reward_sharing,
            'description': '协作机制，管理任务分配和奖励'
        }


class AuctionCollaboration(CollaborationMechanism):
    """拍卖式协作"""
    
    def __init__(self, reserve_price: float = 0.1):
        super().__init__()
        self.reserve_price = reserve_price
        self.bids: Dict[str, Dict[str, float]] = {}
    
    def submit_bid(self, task_id: str, agent_id: str, bid: float):
        """提交竞标"""
        if task_id not in self.bids:
            self.bids[task_id] = {}
        self.bids[task_id][agent_id] = bid
    
    def assign_tasks(self, agents: Dict) -> Dict:
        """基于拍卖的任务分配"""
        assignments = {}
        
        for task_id in self.tasks:
            if task_id not in self.bids:
                continue
            
            bids = self.bids[task_id]
            valid_bids = {aid: bid for aid, bid in bids.items() 
                         if bid >= self.reserve_price}
            
            if valid_bids:
                winner = min(valid_bids.keys(), key=lambda a: valid_bids[a])
                assignments[task_id] = [winner]
        
        return assignments
    
    def get_info(self) -> dict:
        info = super().get_info()
        info['type'] = 'auction'
        return info


class VoteCollaboration(CollaborationMechanism):
    """投票式协作"""
    
    def __init__(self, voting_threshold: float = 0.6):
        super().__init__()
        self.voting_threshold = voting_threshold
        self.votes: Dict[str, Dict[str, int]] = {}
    
    def vote(self, task_id: str, agent_id: str, candidate: str):
        """投票"""
        if task_id not in self.votes:
            self.votes[task_id] = {}
        self.votes[task_id][candidate] = self.votes[task_id].get(candidate, 0) + 1
    
    def assign_tasks(self, agents: Dict) -> Dict:
        """基于投票的任务分配"""
        assignments = {}
        
        for task_id, votes in self.votes.items():
            if votes:
                winner = max(votes.keys(), key=lambda c: votes[c])
                total_votes = sum(votes.values())
                if votes[winner] / total_votes >= self.voting_threshold:
                    assignments[task_id] = [winner]
        
        return assignments
    
    def get_info(self) -> dict:
        info = super().get_info()
        info['type'] = 'vote'
        return info
