# 会话交接卡

> 换机后读取此文件恢复上下文。每天收工前更新。

## 🔄 进行中（未完成）

| 任务 | 进度% | 下一步 | 阻塞 |
|------|:-----:|--------|------|
| L0→L1→L2 端到端管线验证 | ⏸️ 50% | **用户搁置至下周**：L1→L2 已验证通过，完整三阶段届时再跑 | 用户决策 |
| Kepler UI 改造 | 80% | Token 体系补全 / 弹窗暗色主题统一 | 须保持当前基准 |
| 文档修正 | 0% | Python 版本 3.14.5、L1 列数 26、pm.agent.md 角色澄清 | — |

## 📌 上下文快照

- **当前分支**：`main`
- **最新 commit**：`019834f` Merge (2026-06-16 10:58)
- **Git 状态**：clean，已 push（与 origin/main 同步）
- **Python**：3.14.5 | **Streamlit**：1.58.0 | **端口**：8501
- **DeepSeek API Key**：✅ 已配置（.env）
- **技能包**：455 个 Skill（Anthropic 17 + daymade 64 + python-skills 12 + laurigates 362）

### 数据资产

| 文件 | 大小 | 说明 |
|------|------|------|
| `DATA/raw/simulated_20260613_100k_raw.csv` | 28 MB | L0 模拟原始数据（100k 条） |
| `DATA/processed/simulated_l1_2000_规划范围_L1_result_csv.csv` | 787 KB | L1 治理结果（2000 条样本） |
| `DATA/processed/*_L2_result_csv.csv` | 794 KB | L2 情感分析结果 |
| `DATA/processed/*_L2_result_geojson.geojson` | 1.8 MB | L2 地理可视化输出 |

### 换机启动指令

```
git pull origin main
pip install -r requirements.txt
python -m streamlit run apps/app_main.py
```

---

## 2026-06-15 (周一) — 完整进展

### 上午：架构 + 文档 + 配置

| # | 任务 | 关键成果 |
|---|------|----------|
| 1 | Agent 架构 v2.0 升级 | 11→8 Agent 精简 + 自动编排；Debugger→Developer、Design Reviewer→Designer(自审)、PM→主线程 |
| 2 | PRD + Spec 文档 | 5 类用户画像 + 27 功能 MoSCoW + 数据管道字段 + UI 规格 + 性能预算 |
| 3 | .claude 配置初始化 | settings.json (8 Agent + autoCompactThreshold=85) + memory/ 记忆体系 + agent 文件迁移至 `.claude/agents/` |

### 下午：Kepler UI + Harness + 管线验证

| # | 任务 | 关键成果 |
|---|------|----------|
| 4 | Harness 体系搭建 | CLAUDE.md 三层 + SessionStart/End Hooks + 455 Skill 包安装 |
| 5 | 项目框架优化 | `_safe_print` → `core/utils.py` 统一 / `app_main.py` 拆出控制台 / `layer_registry.py` 共享 / CLI 参数化 / pm.agent.md 归档 / 清理 16 个冗余文件 |
| 6 | 记忆体系 | 三层记忆 + brand-visual.md / copywriting-style.md / api-conventions.md + .claudeignore |
| 7 | **Kepler.gl 风格 UI 改造** (80%) | 全屏地图 CSS / 右侧竖排 HUD [R][D][A][H] / 毛玻璃按钮 / CSS tooltip (胶囊形) / 图例中文 / Toast 通知 / LY 图层 toggle / 分级渲染 / 备份恢复脚本 |
| 8 | L1→L2 管线验证 | 2000 行全量通过，SnowNLP ~6s，CSV+GeoJSON 正确导出，追踪点全触发 |
| 9 | 文档一致性审查 | 发现 3 处不一致（Python 版本 / L1 列数 / pm.agent.md 角色）— 待修正 |

### 关键决策

- **自动编排 > 手动 @agent**：一句指令自动 spawn Agent 走 SOP
- **UI 基准**：Kepler 风格全屏地图+HUD 已确认满意，此后所有 UI 修改基于此版不回退
- **Tooltip 方案**：纯 CSS `::after` + `border-radius:100px`，不再用 JS 注入
- **坐标转换**：宜昌双源策略（社交 GCJ-02 + 规划 CGCS2000），灵活支持自定义 EPSG
- **对话语言**：中文（记录在 `memory/user-prefs.md`）

### ⚠️ 注意事项

- **不要**删除 `_add_boundary_if_exists` 或忘记 `RENDER_TIERS` 导入 — 已犯错两次
- **不要**用 CSS 重写 `stDialog` 样式 — 曾导致弹窗错乱，已回退
- **代码中仍有大量未使用的 import**，可择机清理但不影响功能
- **pm.agent.md** 未注册但保留在 agents/ 目录（行为指南角色）

---

## 2026-06-14 (周日) — 概要

- LY 图层 checkbox 修复 + [确定] 按钮
- 数据层架构优化：L1_COLUMNS 9 组重排 + v1.0 代码清退
- L1~L4 confidence 列全局重命名：l1/l2/l3/l4_confidence（4 文件 13 处引用）
- 走完整 SOP：Developer → Reviewer(2轮) → Tester(9/9)

---

## 每日启动

```powershell
# 启动 Streamlit 地图浏览器（端口 8501）
py launch.py

# 浏览器访问
#   http://localhost:8501              — 地图浏览器
#   http://localhost:8501/?page=console — 分析控制台
```
