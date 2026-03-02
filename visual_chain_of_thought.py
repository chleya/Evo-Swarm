# -*- coding: utf-8 -*-
"""
视觉思维链 (Visual Chain of Thought)
让AI"看见"然后思考

核心思路：
截图 -> 视觉理解 -> 思维链推理 -> 行动
"""

import os
import json
import base64
from datetime import datetime
from typing import List, Dict, Optional


class VisualThought:
    """一次视觉思考"""
    def __init__(self, image_path: str, vision理解: str, llm推理: str, 行动: str = ""):
        self.timestamp = datetime.now().isoformat()
        self.image_path = image_path
        self.vision理解 = vision理解
        self.llm推理 = llm推理
        self.行动 = 行动


class VisualChainOfThought:
    """视觉思维链"""
    
    def __init__(self, storage_path: str = "data/visual_thoughts"):
        self.storage_path = storage_path
        os.makedirs(storage_path, exist_ok=True)
        self.history: List[VisualThought] = []
        self._load_history()
    
    def _load_history(self):
        """加载历史"""
        history_file = os.path.join(self.storage_path, "history.json")
        if os.path.exists(history_file):
            with open(history_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item in data:
                    vt = VisualThought(
                        item['image_path'],
                        item['vision理解'],
                        item['llm推理'],
                        item.get('行动', '')
                    )
                    self.history.append(vt)
    
    def _save_history(self):
        """保存历史"""
        history_file = os.path.join(self.storage_path, "history.json")
        data = [
            {
                'timestamp': vt.timestamp,
                'image_path': vt.image_path,
                'vision理解': vt.vision理解,
                'llm推理': vt.llm推理,
                '行动': vt.行动
            }
            for vt in self.history
        ]
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def 看(self, image_path: str) -> str:
        """
        第一步：看见 - 获取截图
        """
        if not os.path.exists(image_path):
            return f"[错误] 图片不存在: {image_path}"
        
        # 返回图片路径，等待视觉理解
        return f"[看] 已获取图片: {image_path}"
    
    def 理解(self, image_path: str, vision_model: str = "qwen") -> str:
        """
        第二步：理解 - 用视觉模型理解图片
        """
        # TODO: 集成Qwen-VL或GPT-4V
        # 这里先返回模拟结果
        return f"""
[视觉理解 - {vision_model}]
检测到内容：
- 页面/场景元素
- 文字信息
- 结构布局
"""
    
    def 推理(self, vision理解: str, question: str, llm_model: str = "minimax") -> str:
        """
        第三步：推理 - 基于视觉理解进行思维链推理
        """
        # TODO: 集成LLM进行推理
        return f"""
[思维链推理 - {llm_model}]
问题: {question}

思考过程：
1. 理解视觉信息
2. 结合历史上下文
3. 生成推理结论

结论: (待LLM生成)
"""
    
    def 行动(self, action: str) -> str:
        """
        第四步：行动 - 执行动作
        """
        return f"[行动] 将执行: {action}"
    
    def think(self, image_path: str, question: str) -> Dict:
        """
        完整的视觉思维链
        """
        # 1. 看
        看_result = self.看(image_path)
        
        # 2. 理解
        理解_result = self.理解(image_path)
        
        # 3. 推理
        推理_result = self.推理(理解_result, question)
        
        # 4. 记录到历史
        vt = VisualThought(image_path, 理解_result, 推理_result)
        self.history.append(vt)
        self._save_history()
        
        return {
            "看": 看_result,
            "理解": 理解_result,
            "推理": 推理_result,
            "思维链长度": len(self.history)
        }
    
    def get_context(self, n: int = 3) -> str:
        """获取最近N次思维链作为上下文"""
        recent = self.history[-n:] if len(self.history) >= n else self.history
        context = "=== 视觉思维链历史 ===\n"
        for i, vt in enumerate(recent):
            context += f"\n[第{i+1}次]\n"
            context += f"图片: {vt.image_path}\n"
            context += f"理解: {vt.vision理解[:100]}...\n"
            context += f"推理: {vt.llm推理[:100]}...\n"
        return context


# ========== 测试 ==========

if __name__ == "__main__":
    vc = VisualChainOfThought()
    
    print("=== 视觉思维链测试 ===\n")
    
    # 测试完整思维链
    # result = vc.think("test.png", "这个页面是什么？")
    # print(result)
    
    print("[OK] VisualChainOfThought 已就绪")
    print(f"历史记录: {len(vc.history)} 条")
    print("\n方法:")
    print("  vc.think(image_path, question) - 完整思维链")
    print("  vc.get_context(n) - 获取历史上下文")
