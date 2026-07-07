"""AI 问答数据模型（Pydantic）— ChatRequest 三阶段 + 审查字段。

phase 三阶段（ Harness 管线）：
- 'think'  → 输出 {framing, mapping, steps[]} JSON（前端编排器据此自动执行；走 JSON mode）。
- 'answer' → 基于执行观察出结论（流式 markdown + [ref:]）；可带 review_feedback 按审查意见修订。
- 'review' → 审查 draft_answer（Flash json_mode → {pass, checks[], revise_hints}）。
"""
from typing import Optional, List
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """AI 问答请求（provider-agnostic，默认 DeepSeek Pro）。"""
    messages: List[dict] = Field(..., description="OpenAI 兼容消息数组 [{role,content}]")
    context: Optional[str] = Field(default=None, description="主窗口推送的数据摘要（grounding）")
    model: Optional[str] = Field(default=None, description="模型：留空=默认 Pro(think/answer)；审查员由后端用 REVIEWER_MODEL")
    context_tokens: Optional[List[dict]] = Field(default=None, description="用户@关联对象(feature/range/layer/pin)，注入 grounding")
    phase: str = Field(default='think', description="问答阶段：think | answer | review")

    # answer / review 阶段：执行观察（主窗口编排器逐步收集的真实数据）。
    # observation 为新字段；execution_result 保留向后兼容（B1 前端旧名）。
    observation: Optional[str] = Field(default=None, description="执行观察结果（answer/review 用）")
    execution_result: Optional[str] = Field(default=None, description="= observation（B1 旧名兼容）")

    # review 阶段：待审初稿。
    draft_answer: Optional[str] = Field(default=None, description="review 阶段：Stage 3 出的待审初稿")

    # answer 阶段：审查意见（pass=false 时带 revise_hints 触发修订重写）。
    review_feedback: Optional[str] = Field(default=None, description="answer 阶段：审查意见（按其修订重写）")
