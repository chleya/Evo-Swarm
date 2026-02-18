"""
Evo-Swarm Base Module

This module defines the base class for multi-agent swarm systems.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import uuid


class SwarmBase(ABC):
    """
    Abstract base class for multi-agent swarm systems.
    
    The swarm system manages multiple agents that can communicate,
    collaborate, and exhibit emergent collective behavior.
    """
    
    def __init__(
        self,
        agent_count: int = 10,
        topology: str = "mesh",
        communication: str = "broadcast",
        name: str = "SwarmBase"
    ):
        self.agent_count = agent_count
        self.topology = topology
        self.communication = communication
        self.name = name
        self.agents = []
        self.step_count = 0
        self.messages_sent = 0
        self.collaboration_count = 0
        
    @abstractmethod
    def create_agent(self, agent_id: str) -> Any:
        """
        Create a new agent for the swarm.
        
        Args:
            agent_id: Unique identifier for the agent
            
        Returns:
            New agent instance
        """
        pass
    
    @abstractmethod
    def send_message(self, from_agent: Any, to_agent: Any, message: Dict):
        """
        Send a message between agents.
        
        Args:
            from_agent: Sending agent
            to_agent: Receiving agent
            message: Message content
        """
        pass
    
    @abstractmethod
    def broadcast(self, agent: Any, message: Dict):
        """
        Broadcast a message to all agents.
        
        Args:
            agent: Broadcasting agent
            message: Message content
        """
        pass
    
    @abstractmethod
    def step(self) -> Dict:
        """
        Execute one step of the swarm.
        
        Returns:
            Step results and statistics
        """
        pass
    
    @abstractmethod
    def get_collaborative_results(self) -> Dict:
        """
        Get results from collaborative efforts.
        
        Returns:
            Collaborative results
        """
        pass
    
    def initialize(self, agents: List[Any] = None):
        """
        Initialize the swarm with agents.
        
        Args:
            agents: Optional list of pre-created agents
        """
        if agents:
            self.agents = agents
        else:
            for i in range(self.agent_count):
                agent_id = str(uuid.uuid4())[:8]
                self.agents.append(self.create_agent(agent_id))
    
    def get_statistics(self) -> Dict:
        """Get swarm statistics."""
        return {
            'agent_count': len(self.agents),
            'steps': self.step_count,
            'messages': self.messages_sent,
            'collaborations': self.collaboration_count
        }
    
    def reset(self):
        """Reset swarm state."""
        self.agents = []
        self.step_count = 0
        self.messages_sent = 0
        self.collaboration_count = 0


class Agent(ABC):
    """
    Abstract base class for individual agents in the swarm.
    """
    
    def __init__(self, agent_id: str, behavior_rules: Dict = None):
        self.agent_id = agent_id
        self.behavior_rules = behavior_rules or {}
        self.state = {}
        self.messages_received = []
        
    @abstractmethod
    def perceive(self, environment: Dict) -> Dict:
        """
        Perceive the environment.
        
        Args:
            environment: Current environment state
            
        Returns:
            Perceived information
        """
        pass
    
    @abstractmethod
    def decide(self, perception: Dict) -> Any:
        """
        Make a decision based on perception.
        
        Args:
            perception: Perceived information
            
        Returns:
            Decision or action
        """
        pass
    
    @abstractmethod
    def act(self, decision: Any) -> Dict:
        """
        Execute an action.
        
        Args:
            decision: Decision to execute
            
        Returns:
            Action results
        """
        pass
    
    def receive_message(self, message: Dict):
        """
        Receive a message from another agent.
        
        Args:
            message: Received message
        """
        self.messages_received.append(message)
    
    def reset(self):
        """Reset agent state."""
        self.state = {}
        self.messages_received = []
