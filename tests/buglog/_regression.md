# 回归关注清单（resolved · 自动生成）

> 自动生成（`py tests/buglog/_gen_index.py`）·勿手改。已修复 bug 的标准化用例 + 根因指针。
> 供发版前**手动复验**。非飞轮自动执行——数据前提逐案不同（如 B001 需带字段 MC 的面层），
> 无法从语义描述自动装配；关联飞轮用例（case_ref）在常规跑中已覆盖执行。

## 用例速查

| ID | 标题 | 关联用例 | 模块 |
|:-:|------|:-:|:-:|
| B001 | 多要素裁剪失败螺旋（extract_feature 字段重命名断裂 + 单工具限制 + FC 推理死循环） | TC-06 | 数据识别 |

## 标准化用例（问句 + 预期，供手动复验）

### B001
- **问句**：「帮我从中心城区范围中裁剪出西陵 + 伍家岗的范围」
- **预期**：`extract_feature` 被选中且 `where` 正确引用字段名（`MC` 或重命名后的 `name`） / 西陵区 + 伍家岗区面图层已生成 / 结论诚实描述（不编造未生成的图层）
- **根因**：[2026-07-28-multi-extract-reasoning-spiral.md](../../docs/catch-ball/rootcause/2026-07-28-multi-extract-reasoning-spiral.md)
