"""AI 问答数据模型（Pydantic）— Agent Loop 版。

phase 两阶段（ReAct）：
- 'agent_step' → ReAct 每轮，输出 {thought, action} JSON（前端按 action 执行工具/终止）。
- 'answer'     → agent 决定 answer 后，基于 tool_history 出最终结论（流式 markdown）。
"""
from typing import Optional, List
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """AI 问答请求（provider-agnostic，默认 DeepSeek Pro reasoner）。"""
    messages: List[dict] = Field(..., description="OpenAI 兼容消息数组 [{role,content}]")
    context: Optional[str] = Field(default=None, description="主窗口推送的数据摘要（grounding）")
    model: Optional[str] = Field(default=None, description="模型：留空=默认 Pro(reasoner)")
    context_tokens: Optional[List[dict]] = Field(default=None, description="用户@关联对象")
    phase: str = Field(default='agent_step', description="阶段：agent_step | answer")
    tool_history: Optional[str] = Field(default=None, description="已完成的探索历史（历轮 thought/action/观察，字符串）")
    round_n: Optional[int] = Field(default=1, description="agent_step 用：当前轮次（注入 prompt 让模型知道进度）")
