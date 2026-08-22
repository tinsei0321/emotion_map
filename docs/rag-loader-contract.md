# RAG loader 接口契约（P0-6 · v1.2-pre 扩展版 · 泳道①②对着编码·③迁移复用）

> PT-CB9 P0-6 产出。单一权威源：chunk schema 与 loader 函数签名以此为准（v1.2-pre D2/§二 收编）。

## 一 chunk schema（v1.2-pre 扩展）

```python
chunk = {
    # ── 现行四字段（tools/rag_index.py 现状·不动） ──
    'text':   str,          # 片段全文（≤2000·CB-22 全文纪律：全文存 meta 防截断失义）
    'source': str,          # 溯源 'docs/...md#小节序' | 'ai_qa/outlet_kb/xxx.py#key'
    'type':   str,          # 'note' | 'case' | 'fact' | 'concept'
    'dim':    str,          # 数据维度标注（_infer_dim）

    # ── v1.2 新增：治理字段（泳道①入库时填充） ──
    'status': str,          # 'active' | 'superseded'（压旧口径·默认 active）——检索过滤维度
    'lineage': str | None,  # 同源谱系标注（39 md↔282 蒸馏段去重用·格式 'src:<上游文档>#<节>'）

    # ── v1.2 新增：A1 前注三字段（护栏 2·None=未启用 A1·向后兼容） ──
    'ctx_prefix':       str | None,  # 前注 1-2 句（文档名+小节定位+口径状态）·embedding/BM25 拼接吃
    'ctx_prefix_model': str | None,  # 生成模型溯源 'deepseek-v4-flash@2026-08-22'
    'ctx_prefix_hash':  str | None,  # 前注内容 hash（与 content_hash 分离·build 校验正文变→前注必重算）
}
# content_hash（索引层派生）：覆盖 text + ctx_prefix 整体——失配则 build 不更新（护栏 3）
```

## 二 loader 函数签名

```python
# tools/rag_index.py（泳道①改造目标·③搬家时保持签名不变）
def load_chunks() -> list[dict]:
    """全量 chunk（含治理字段·status=superseded 默认过滤由检索层做非 loader 做）。"""

def build_index(include_ctx_prefix: bool = True) -> dict:
    """构建索引：embed/BM25 输入 = ctx_prefix + text（A1 启用时）·产物含 content_hash 全集。"""

def search(query: str, k: int = 5) -> dict:
    """检索核心（MCP rag_query 与 ai_qa diagnose 唯一共同真身·H3 断言对象）。"""
```

## 三 followup_cue 派生所需元数据（H1·泳道②实现依赖·此声明=存在性契约）

| 派生规则 | 依赖数据 | 现状 |
|---|---|---|
| 维度相邻（第一价值） | dim→相邻 dim 映射表（静态小表·入库进 git） | **待建**（泳道②任务·`ai_qa/rag_dims.json` 类） |
| 口径关联（第二·文案翻译） | K 卡 topic→用户语言文案映射 | 口径注册表在·文案映射待建 |
| 小节邻接（兜底·过滤 meta 小节） | source 的小节序号 + meta 小节黑名单（修订/附录/索引） | source 在·黑名单待建 |

## 四 红线

- ctx_prefix 是**内部 schema 字段**·不进 rag_query 对外返回（接口锁 G4 零破坏）。
- 检索核心 search() 宿主无关（同义词=EMC 词表·语义改写留宿主）。
- superseded 过滤=检索层职责（默认滤除·可显式开）。

> P0-6 · zcode · 2026-08-22 · 泳道①②可编码·claude组 确认条款见回收
