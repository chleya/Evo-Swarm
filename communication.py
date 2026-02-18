"""
Communication Protocols (通信协议)

实现智能体间的通信机制。
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
import time
import hashlib
import sys
sys.path.append('../..')
from base import SwarmBase


class MessageType(Enum):
    """消息类型"""
    INFO = "info"
    REQUEST = "request"
    RESPONSE = "response"
    ALERT = "alert"
    COORDINATION = "coordination"
    BROADCAST = "broadcast"
    DIRECT = "direct"


@dataclass
class Message:
    """消息"""
    id: str
    type: MessageType
    from_agent: str
    to_agents: List[str]
    content: Dict
    timestamp: float
    priority: int = 0
    ttl: int = 10  # 生存时间（跳数）
    signature: Optional[str] = None
    
    def __init__(self,
                 message_type: MessageType,
                 from_agent: str,
                 to_agents: List[str],
                 content: Dict,
                 priority: int = 0,
                 ttl: int = 10):
        self.id = self._generate_id()
        self.type = message_type
        self.from_agent = from_agent
        self.to_agents = to_agents
        self.content = content
        self.timestamp = time.time()
        self.priority = priority
        self.ttl = ttl
    
    def _generate_id(self) -> str:
        """生成消息ID"""
        return hashlib.md5(
            f"{time.time()}_{id(self)}".encode()
        ).hexdigest()[:8]
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'id': self.id,
            'type': self.type.value,
            'from': self.from_agent,
            'to': self.to_agents,
            'content': self.content,
            'timestamp': self.timestamp,
            'priority': self.priority,
            'ttl': self.ttl
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Message':
        """从字典创建"""
        msg = cls(
            message_type=MessageType(data['type']),
            from_agent=data['from'],
            to_agents=data['to'],
            content=data['content'],
            priority=data.get('priority', 0),
            ttl=data.get('ttl', 10)
        )
        msg.id = data['id']
        msg.timestamp = data['timestamp']
        return msg


class CommunicationProtocol(SwarmBase):
    """
    通信协议
    
    管理智能体间的消息传递。
    
    特点：
    - 支持多种消息类型
    - 消息优先级
    - 消息传递确认
    """
    
    def __init__(self,
                 max_queue_size: int = 1000,
                 retry_count: int = 3,
                 timeout: float = 5.0):
        """
        初始化通信协议
        
        Args:
            max_queue_size: 最大队列大小
            retry_count: 重试次数
            timeout: 超时时间
        """
        super().__init__()
        self.max_queue_size = max_queue_size
        self.retry_count = retry_count
        self.timeout = timeout
        
        self.message_queue: List[Message] = []
        self.delivery_status: Dict[str, Dict] = {}
        self.message_handlers: Dict[MessageType, List[Callable]] = {
            msg_type: [] for msg_type in MessageType
        }
    
    def send(self, message: Message) -> bool:
        """
        发送消息
        
        Args:
            message: 消息对象
            
        Returns:
            是否成功加入队列
        """
        if len(self.message_queue) >= self.max_queue_size:
            return False
        
        self.message_queue.append(message)
        self.delivery_status[message.id] = {
            'status': 'pending',
            'retries': 0,
            'delivered_to': []
        }
        
        return True
    
    def broadcast(self,
                  from_agent: str,
                  content: Dict,
                  priority: int = 0) -> Message:
        """
        广播消息
        
        Args:
            from_agent: 发送者ID
            content: 消息内容
            priority: 优先级
            
        Returns:
            发送的消息
        """
        message = Message(
            message_type=MessageType.BROADCAST,
            from_agent=from_agent,
            to_agents=['*'],  # 通配符表示所有智能体
            content=content,
            priority=priority
        )
        
        self.send(message)
        return message
    
    def send_direct(self,
                   from_agent: str,
                   to_agent: str,
                   content: Dict,
                   priority: int = 0) -> Message:
        """
        发送直接消息
        
        Args:
            from_agent: 发送者ID
            to_agent: 接收者ID
            content: 消息内容
            priority: 优先级
            
        Returns:
            发送的消息
        """
        message = Message(
            message_type=MessageType.DIRECT,
            from_agent=from_agent,
            to_agents=[to_agent],
            content=content,
            priority=priority
        )
        
        self.send(message)
        return message
    
    def request(self,
               from_agent: str,
               to_agents: List[str],
               content: Dict,
               response_handler: Optional[Callable] = None,
               priority: int = 0) -> Message:
        """
        发送请求消息
        
        Args:
            from_agent: 发送者ID
            to_agents: 接收者ID列表
            content: 请求内容
            response_handler: 响应处理函数
            priority: 优先级
            
        Returns:
            发送的消息
        """
        message = Message(
            message_type=MessageType.REQUEST,
            from_agent=from_agent,
            to_agents=to_agents,
            content=content,
            priority=priority
        )
        
        if response_handler:
            self.message_handlers[MessageType.RESPONSE].append(response_handler)
        
        self.send(message)
        return message
    
    def register_handler(self,
                        message_type: MessageType,
                        handler: Callable):
        """注册消息处理器"""
        if message_type in self.message_handlers:
            self.message_handlers[message_type].append(handler)
    
    def process_messages(self, delivered_messages: Dict[str, List[Message]]) -> List[Message]:
        """
        处理消息
        
        Args:
            delivered_messages: 已送达的消息，按智能体分组
            
        Returns:
            发送的消息
        """
        responses = []
        
        for agent_id, messages in delivered_messages.items():
            for message in messages:
                # 更新传递状态
                if message.id in self.delivery_status:
                    self.delivery_status[message.id]['delivered_to'].append(agent_id)
                
                # 调用处理器
                for handler in self.message_handlers.get(message.type, []):
                    try:
                        response = handler(agent_id, message)
                        if response:
                            responses.append(response)
                    except Exception:
                        pass
        
        # 清理已传递完成的消息
        self._cleanup_delivered()
        
        return responses
    
    def _cleanup_delivered(self):
        """清理已传递完成的消息"""
        delivered_ids = [
            msg_id for msg_id, status in self.delivery_status.items()
            if status['status'] == 'delivered'
        ]
        
        self.message_queue = [
            msg for msg in self.message_queue
            if msg.id not in delivered_ids
        ]
        
        for msg_id in delivered_ids:
            del self.delivery_status[msg_id]
    
    def get_queue_status(self) -> Dict:
        """获取队列状态"""
        return {
            'queue_size': len(self.message_queue),
            'max_queue_size': self.max_queue_size,
            'pending_delivery': len([
                s for s in self.delivery_status.values()
                if s['status'] == 'pending'
            ]),
            'handlers_registered': sum(
                len(handlers) for handlers in self.message_handlers.values()
            )
        }
    
    def get_info(self) -> dict:
        return {
            'name': 'CommunicationProtocol',
            'queue_size': len(self.message_queue),
            'max_queue_size': self.max_queue_size,
            'description': '通信协议，管理智能体间消息传递'
        }


class GossipProtocol(CommunicationProtocol):
    """
    Gossip协议
    
    分布式消息传播协议。
    
    特点：
    - 去中心化
    - 容错性强
    - 最终一致性
    """
    
    def __init__(self,
                 fanout: int = 3,
                 interval: float = 1.0):
        super().__init__()
        self.fanout = fanout
        self.interval = interval
        self.gossip_history: Dict[str, float] = {}
    
    def gossip(self, agent_id: str, message: Message, neighbors: List[str]):
        """
        Gossip传播
        
        Args:
            agent_id: 智能体ID
            message: 消息
            neighbors: 邻居列表
        """
        if message.id in self.gossip_history:
            return
        
        self.gossip_history[message.id] = time.time()
        
        # 选择fanout个邻居传播
        selected = np.random.choice(
            neighbors,
            size=min(self.fanout, len(neighbors)),
            replace=False
        ) if len(neighbors) > 0 else []
        
        for neighbor_id in selected:
            self.send_direct(agent_id, neighbor_id, {
                'gossip_id': message.id,
                'content': message.content
            })
    
    def get_info(self) -> dict:
        info = super().get_info()
        info['type'] = 'gossip'
        info['fanout'] = self.fanout
        info['gossip_count'] = len(self.gossip_history)
        return info
