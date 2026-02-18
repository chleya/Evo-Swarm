"""
Test module for Evo-Swarm
"""

import unittest
import numpy as np
import sys
sys.path.append('../..')


class TestEvoSwarm(unittest.TestCase):
    """Test Evo-Swarm module"""
    
    def test_agent_creation(self):
        """Test agent creation"""
        from evo_swarm.agent import EvoAgent, AgentConfig
        
        config = AgentConfig(name="test_agent")
        agent = EvoAgent(config)
        
        self.assertIsNotNone(agent.id)
        self.assertEqual(agent.state.value, "idle")
    
    def test_agent_perceive(self):
        """Test agent perception"""
        from evo_swarm.agent import EvoAgent
        
        agent = EvoAgent()
        environment = {'targets': [{'id': 't1', 'position': np.array([1, 1])}]}
        
        perception = agent.perceive(environment)
        self.assertIn('nearby_agents', perception)
    
    def test_swarm_creation(self):
        """Test swarm creation"""
        from evo_swarm.swarm import Swarm, SwarmConfig
        
        config = SwarmConfig(size=5)
        swarm = Swarm(config)
        
        self.assertEqual(len(swarm.agents), 5)
    
    def test_swarm_step(self):
        """Test swarm step execution"""
        from evo_swarm.swarm import Swarm, SwarmConfig
        
        config = SwarmConfig(size=3)
        swarm = Swarm(config)
        
        result = swarm.step({})
        self.assertEqual(result['num_agents'], 3)
        self.assertIn('generation', result)
    
    def test_communication_protocol(self):
        """Test communication protocol"""
        from evo_swarm.communication import CommunicationProtocol, MessageType
        
        protocol = CommunicationProtocol()
        self.assertIsNotNone(protocol)
        
        # Test message creation
        message = protocol.broadcast(
            from_agent="agent_1",
            content={"test": "data"}
        )
        self.assertIsNotNone(message)


class TestSwarmTopology(unittest.TestCase):
    """Test swarm topology"""
    
    def test_topology_manager(self):
        """Test topology manager"""
        from evo_swarm.topology import TopologyManager, Topology
        
        manager = TopologyManager()
        
        agent_ids = [f"agent_{i}" for i in range(10)]
        adjacency = manager.build_topology(agent_ids, Topology.MESH)
        
        self.assertEqual(len(adjacency), 10)
    
    def test_topology_metrics(self):
        """Test topology metrics"""
        from evo_swarm.topology import TopologyManager, Topology
        
        manager = TopologyManager()
        agent_ids = [f"agent_{i}" for i in range(10)]
        manager.build_topology(agent_ids, Topology.RING)
        
        metrics = manager.get_topology_metrics()
        
        self.assertIn('avg_degree', metrics)
        self.assertIn('clustering_coefficient', metrics)


class TestCollaboration(unittest.TestCase):
    """Test collaboration mechanisms"""
    
    def test_collaboration_mechanism(self):
        """Test collaboration mechanism"""
        from evo_swarm.collaboration import CollaborationMechanism, Task, TaskType
        
        collab = CollaborationMechanism()
        
        task = Task(
            task_id="task_1",
            task_type=TaskType.COOPERATIVE,
            description="Test task",
            reward=1.0
        )
        
        collab.add_task(task)
        self.assertEqual(len(collab.tasks), 1)


class TestEmergence(unittest.TestCase):
    """Test emergence intelligence"""
    
    def test_emergence_detection(self):
        """Test emergence detection"""
        from evo_swarm.emergence import EmergenceIntelligence
        
        emergence = EmergenceIntelligence()
        
        class MockAgent:
            def __init__(self):
                self.position = np.random.rand(2)
                self.velocity = np.random.rand(2) * 0.1
        
        agents = {f"agent_{i}": MockAgent() for i in range(10)}
        
        emergent = emergence.detect_emergence(agents, {})
        self.assertIsInstance(emergent, dict)


if __name__ == '__main__':
    unittest.main()
