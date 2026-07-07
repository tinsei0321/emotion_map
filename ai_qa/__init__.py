"""ai_qa — 情绪地图 AI 问答子系统（独立小体系）。

为何独立成子系统（ADR·2026-07-07）：
AI 问答未来会做厚（多轮记忆 / Agent / 多模型协作 / 知识库 RAG），从散落于 core/ + frontend/js/
收拢为独立子系统，边界干净、未来好扩，不污染主体。

四层 Harness 架构（详见 docs/ai-qa-design.md）：
- 知识层 manifesto.py    —— MANIFESTO 领域宪法（喂给模型，让它真懂情绪地图）
- 思考层 prompts.py      —— build_think/answer/review_prompt（SOP 解题协议）
- 执行层 （前端 tools.js，tool 操作地图；后端无）
- 审查层 review.py       —— REVIEW_CHECKLIST 六条 + 审查员模型

入口：router.py 暴露 /chat（phase: think|answer|review），挂载到 api/main.py。
LLM 基础设施：llm.py（provider-agnostic，默认 DeepSeek，未来换溯佰科改一处）。

provider 切换：llm.py 的 base_url/model/key 三参 + env，其余不动。
"""
