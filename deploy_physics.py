"""
物理引擎部署到 Evo-Swarm 项目
简化版本
"""

import sys
import os
from typing import Dict, List, Any
import numpy as np
import time

# 添加物理引擎路径
physics_core_path = os.path.join(os.path.dirname(__file__), '..', 'physical-agi', 'core')
if physics_core_path not in sys.path:
    sys.path.insert(0, physics_core_path)

from physics_engine_edge import (
    Vec2, Vector3D, PhysicsObject, PhysicsObjectType, 
    PhysicsEngine, PhysicsConfig,
    create_mobile_robot
)


class SimpleAgent:
    """简单智能体"""
    
    def __init__(self, agent_id: str, physics: PhysicsEngine):
        self.id = agent_id
        self.physics = physics
        self.position = np.array([0.0, 0.0])
        self.velocity = np.array([0.0, 0.0])
        self.fitness = 0.0
        self.age = 0
        
        # 创建物理身体
        self.body = create_mobile_robot(f"body_{self.id}", (0, 0, 0))
        self.body.mass = 1.0
        self.physics.add_object(self.body)
    
    def perceive(self, environment: Dict) -> Dict:
        return {
            'nearby': self.physics.get_proximity(self.body.object_id, 5.0),
            'contact': self.physics.get_contact_state(self.body.object_id)
        }
    
    def decide(self, perception: Dict) -> Dict:
        # 简单规则：朝中心移动
        return {'action': 'move_toward', 'target': {'position': (0, 0)}}
    
    def act(self, decision: Dict, environment: Dict) -> Dict:
        action = decision.get('action', 'explore')
        
        if action == 'move_toward':
            target = decision.get('target', {})
            if 'position' in target:
                dx = target['position'][0] - self.body.position.x
                dy = target['position'][1] - self.body.position.y
                force = Vector3D(dx * 2, dy * 2, 0)
                self.physics.apply_force(self.body.object_id, force)
                return {'success': True, 'force': (dx, dy)}
        
        elif action == 'explore':
            angle = np.random.uniform(0, 2 * np.pi)
            force = Vector3D(np.cos(angle) * 3, np.sin(angle) * 3, 0)
            self.physics.apply_force(self.body.object_id, force)
            return {'success': True}
        
        return {'success': False}
    
    def update(self):
        # 同步位置
        self.position = np.array([self.body.position.x, self.body.position.y])
        self.age += 1


class SimpleSwarm:
    """简单群体"""
    
    def __init__(self, physics: PhysicsEngine, num_agents: int = 10):
        self.physics = physics
        self.agents: Dict[str, SimpleAgent] = {}
        
        for i in range(num_agents):
            agent = SimpleAgent(f"agent_{i}", physics)
            # 随机放置
            angle = 2 * np.pi * i / num_agents
            dist = np.random.uniform(5, 8)
            agent.body.position = Vector3D(
                np.cos(angle) * dist,
                np.sin(angle) * dist,
                0
            )
            agent.update()
            self.agents[agent.id] = agent
    
    def step(self, environment: Dict = None) -> Dict:
        # 物理模拟
        physics_result = self.physics.simulate_step()
        
        # 更新智能体
        for agent in self.agents.values():
            perception = agent.perceive(environment or {})
            decision = agent.decide(perception)
            agent.act(decision, environment or {})
            agent.update()
        
        return {
            'num_agents': len(self.agents),
            'physics': physics_result
        }
    
    def get_fitness_metrics(self) -> Dict:
        """获取适应度指标"""
        total_ke = self.physics.get_fitness_metrics().get('total_kinetic_energy', 0)
        
        return {
            'total_kinetic_energy': total_ke,
            'agent_count': len(self.agents),
            'avg_fitness': np.mean([a.fitness for a in self.agents.values()])
        }


def test_deployment():
    """测试部署"""
    print("=" * 60)
    print("Evo-Swarm + 物理引擎 部署测试")
    print("=" * 60)
    
    # 1. 创建物理引擎
    physics_config = PhysicsConfig()
    physics_config.LOW_POWER_MODE = False
    physics = PhysicsEngine(config=physics_config)
    
    print(f"\n创建物理引擎")
    
    # 2. 创建群体
    swarm = SimpleSwarm(physics, num_agents=10)
    print(f"创建10个具身智能体")
    
    # 3. 运行模拟
    print(f"\n运行模拟...")
    start = time.time()
    
    for step in range(100):
        swarm.step()
        
        if step % 20 == 0:
            metrics = swarm.get_fitness_metrics()
            print(f"Step {step}: 总动能={metrics['total_kinetic_energy']:.2f}, "
                  f"智能体={metrics['agent_count']}")
    
    elapsed = time.time() - start
    fps = 100 / elapsed
    
    print(f"\n模拟完成: {elapsed:.2f}s, {fps:.1f} FPS")
    
    # 4. 性能指标
    final_metrics = swarm.get_fitness_metrics()
    print(f"\n最终指标:")
    print(f"  总动能: {final_metrics['total_kinetic_energy']:.2f}")
    print(f"  智能体数: {final_metrics['agent_count']}")
    
    return swarm


def test_collaboration():
    """测试协作搬运"""
    print("\n" + "=" * 60)
    print("协作测试：群体搬运")
    print("=" * 60)
    
    physics = PhysicsEngine()
    
    # 创建目标物体
    target = PhysicsObject(
        object_id="target",
        object_type=PhysicsObjectType.DYNAMIC,
        position=Vector3D(0, 1, 0),
        velocity=Vector3D(0, 0, 0),
        acceleration=Vector3D(0, 0, 0),
        mass=3.0,
        size=Vector3D(1.5, 1.5, 1.5),
        friction=0.8,
        restitution=0.1
    )
    physics.add_object(target)
    
    # 创建搬运智能体
    for i in range(5):
        angle = 2 * np.pi * i / 5
        dist = 3.0
        pos = Vector3D(np.cos(angle) * dist, np.sin(angle) * dist, 0)
        
        agent = SimpleAgent(f"lifter_{i}", physics)
        agent.body.position = pos
        physics.add_object(agent.body)
    
    print(f"创建5个智能体协作搬运")
    
    # 协作搬运
    for step in range(100):
        for agent in physics.objects.values():
            if agent.object_id.startswith("lifter_"):
                # 朝目标施力
                dx = target.position.x - agent.position.x
                dy = target.position.y - agent.position.y
                force = Vector3D(dx * 1.5, dy * 1.5, 0)
                physics.apply_force(agent.object_id, force)
        
        physics.simulate_step()
        
        if step % 25 == 0:
            print(f"Step {step}: 目标=({target.position.x:.2f}, {target.position.y:.2f})")
    
    final_dist = np.sqrt(target.position.x**2 + target.position.y**2)
    print(f"\n最终目标位置: ({target.position.x:.2f}, {target.position.y:.2f})")
    print(f"距中心距离: {final_dist:.2f}")
    
    return True


def test_emergence():
    """测试涌现行为"""
    print("\n" + "=" * 60)
    print("涌现测试：群体聚集")
    print("=" * 60)
    
    physics = PhysicsEngine()
    
    # 创建分散的智能体
    for i in range(20):
        angle = np.random.uniform(0, 2 * np.pi)
        dist = np.random.uniform(8, 12)
        pos = Vector3D(np.cos(angle) * dist, np.sin(angle) * dist, 0)
        
        agent = SimpleAgent(f"agent_{i}", physics)
        agent.body.position = pos
        agent.body.velocity = Vector3D(0, 0, 0)
        physics.add_object(agent.body)
    
    print(f"创建20个分散的智能体")
    
    # 聚集行为
    for step in range(200):
        # 计算中心
        positions = [obj.position for obj in physics.objects.values() 
                    if obj.object_id.startswith('body_')]
        if not positions:
            break
            
        center_x = sum(p.x for p in positions) / len(positions)
        center_y = sum(p.y for p in positions) / len(positions)
        
        # 朝中心移动
        for obj in physics.objects.values():
            if obj.object_id.startswith('body_'):
                dx = center_x - obj.position.x
                dy = center_y - obj.position.y
                force = Vector3D(dx * 0.5, dy * 0.5, 0)
                physics.apply_force(obj.object_id, force)
        
        physics.simulate_step()
        
        if step % 50 == 0:
            xs = [p.x for p in positions]
            spread = max(xs) - min(xs)
            print(f"Step {step}: 分布范围={spread:.2f}")
    
    # 最终分布
    positions = [obj.position for obj in physics.objects.values()]
    xs = [p.x for p in positions]
    spread = max(xs) - min(xs)
    
    print(f"\n最终分布范围: {spread:.2f}")
    
    if spread < 5.0:
        print("[PASS] 群体成功聚集")
        return True
    else:
        print("[NOTE] 聚集效果有限")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Evo-Swarm 物理引擎部署测试")
    print("=" * 60 + "\n")
    
    # 运行测试
    test_deployment()
    test_collaboration()
    test_emergence()
    
    print("\n" + "=" * 60)
    print("部署测试完成")
    print("=" * 60)
