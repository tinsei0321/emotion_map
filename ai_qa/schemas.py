"""AI 问答数据模型（Pydantic）— Agent Loop 版。

phase 两阶段（ReAct）：
- 'agent_step' → ReAct 每轮，输出 {thought, action} JSON（前端按 action 执行工具/终止）。
- 'answer'     → agent 决定 answer 后，基于 tool_history 出最终结论（流式 markdown）。
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """AI 问答请求（provider-agnostic，默认 DeepSeek Pro reasoner）。"""
    messages: List[dict] = Field(..., description="OpenAI 兼容消息数组 [{role,content}]")
    context: Optional[str] = Field(default=None, description="主窗口推送的数据摘要（grounding）")
    model: Optional[str] = Field(default=None, description="模型：留空=默认 Pro(reasoner)")
    context_tokens: Optional[List[dict]] = Field(default=None, description="用户@关联对象")
    phase: str = Field(default='agent_step', description="阶段：diagnose | agent_step | answer | optimize")
    tool_history: Optional[str] = Field(default=None, description="已完成的探索历史（历轮 thought/action/观察，字符串）")
    round_n: Optional[int] = Field(default=1, description="agent_step 用：当前轮次（注入 prompt 让模型知道进度）")
    domain_lens: Optional[List[str]] = Field(default=None, description="diagnose 产出的领域聚焦数组；post-diagnose step 据此注入命中领域完整权威语境（前端回传）")
    layer_meta: Optional[Dict[str, Any]] = Field(default=None, description="CB-09 5.242：结构化图层元数据 {has_point, has_polygon}·喂 select_candidates 数据感知过滤（解 context=None 数据盲）")
