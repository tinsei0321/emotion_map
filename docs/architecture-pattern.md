# 情绪地图项目架构规范

> **⚠ 2026-07-18 退役声明**：`apps/` Streamlit 层 + `launch.py` 已整层退役（前端 `frontend/` 完全接管，启动 `py frontend/serve.py 8080`）。下表「应用层(遗留)/UI 组件层(遗留)」及后续 Streamlit 描述仅作历史记录。

## 七层架构（从下至上）

| 层级 | 目录 | 职责 |
|------|------|------|
| 数据层 | `data/` | L0(原始爬取) / L1~L4(分析结果)，格式 csv/geojson |
| 数据采集层 | `SCRAPER/` | 多源数据爬取（大众点评/美团/小红书/微博/12345），基于 Scrapy，输出到 data/raw/ |
| 基础设施层 | `core/` | config / data_loader / export / **tracker(决策追踪)** |
| 数据分析引擎层 | `SCRIPT/` | L1(数据治理)→L2(SnowNLP)→L3(LLM/溯佰科)→L4(多维归因) 四级管道 |
| 空间分析引擎层 | `core/` | 底图渲染 + 空间可视化(点状/热力图) + 空间分析(热点/缓冲区/聚合)（遗留 Streamlit 栈，前端用 MapLibre） |
| UI 组件层（遗留） | `core/` | Streamlit 可复用组件（HUD/弹窗/图例/CSS） |
| **前端层（主）** | `frontend/` | **MapLibre GL JS** 主界面（geojson.io 1:1），新功能一律在此 |
| 应用层（遗留） | `apps/` | Streamlit 遗留主应用，所有页面通过 ?page= 路由（仅维护不扩展） |

## 入口统一原则
- **前端主入口** = `frontend/index.html`（`py -m http.server 8080` 从项目根启动），新功能一律进 `frontend/`
- **遗留 Streamlit**：仅一个端口 (8501)，`app_main.py` 内 `?page=` 路由（迁移期遗留，不再新增页面）；`launch.py` 启动遗留 Streamlit 进程
- `run_analysis.py` 是独立的 CLI + Tkinter 桌面入口，不依赖 Streamlit
- 所有入口（CLI / Tkinter / 遗留 Streamlit / 前端 API）共用同一个 `run_analysis_task()`

## 新增子页面流程

> **⚠ 新功能一律进 `frontend/`**（MapLibre）。以下流程仅适用于维护遗留 Streamlit 页面。

1. 在 `app_main.py` 中新建 `show_xxx_page()` 函数
2. 在 `main()` 顶部路由表中注册：`if page == 'xxx': show_xxx_page(); return`
3. 侧边栏放 `[返回地图浏览器](/)` 链接
4. 页面间跳转用 `st.link_button` 或 `st.markdown` 链接，URL 格式 `/?page=xxx&param=value`

## 分析逻辑共用
- 所有 UI（CLI / Tkinter / Streamlit）调用同一个 `run_analysis_task()`（在 `emotion_analysis_v1.py`）
- 导出文件命名统一：`{name}_{L1|L2|L3|L4}_result_csv.csv`
- print() 全部用 `_safe_print()` 包裹，防止 Windows GBK 编码崩溃
- 禁止劫持 `builtins.print`

## 文件职责
| 文件 | 职责 |
|------|------|
| `frontend/` | **前端主界面**（MapLibre GL JS，geojson.io 1:1），HTML/CSS/JS |
| `apps/app_main.py` | 遗留 Streamlit 主应用（地图 + 子页面路由，迁移期遗留） |
| `SCRIPT/emotion_analysis_v1.py` | 核心分析引擎（数据结构、管道、任务入口） |
| `SCRIPT/run_analysis.py` | CLI + Tkinter 桌面入口 |
| `core/config.py` | 全局配置（天地图Key、情绪阈值、颜色映射等） |
| `core/data_loader.py` | 统一数据加载入口 |
| `core/map_engine.py` | 空间分析引擎（底图/点状/热力图/空间分析） |
| `core/ui_components.py` | 可复用 Streamlit UI 组件 |
| `core/export.py` | CSV/GeoJSON 导出 |
| `SCRAPER/data_scraper.py` | 多源数据爬取统一入口（EmotionScraper 类 + CLI） |
| `SCRAPER/spiders/` | Scrapy Spider 目录（首个：xiaohongshu_spider） |
| `SCRAPER/settings.py` | Scrapy 全局配置 |
| `core/tracker.py` | 决策追踪系统（装饰器/上下文管理器/日志/ID注册表） |
| `launch.py` | 一键启动遗留 Streamlit（:8501） |

## 关键概念
- **溯佰科**：城市规划时空大模型平台（数据底座+GIS工具+NL工作台），非 LLM 大模型。情绪地图未来以 Agent 嵌入
- **L0~L4 数据分级**：L0=原始爬取 → L1=治理后城市情绪DATA → L2=SnowNLP情绪地图DATA → L3=LLM增强DATA → L4=多维归因DATA
- **空间分析 MVP**：geopandas + shapely 自研，3个核心功能（热点分析/缓冲区分析/行政单元聚合）
- **数据采集铁律（空间范围优先）**：
  1. 第一优先级：加载行政区划边界 Polygon → 搜索边界内的地理位置内容
  2. 关键词搜索仅作为发现内部地名/POI的辅助手段
  3. 坐标生成必须用 point-in-polygon 约束（排除水域/山体等非建成区）
  4. 此策略适用于所有平台：大众点评/美团/小红书/微博/12345
- **数据隐私规范**：
  - 输出数据中禁止包含用户名、用户ID等个人身份信息
  - 保留：标题/正文（已公开发布的内容）、发布时间、点赞数、来源平台、子区域标签

## Agent 协作体系
- 项目使用 8 个专用 Agent 协作开发，定义在 `.claude/agents/*.agent.md`（v2.0）
- 全局协作规则见根目录 `AGENTS.md`
- 标准流程：PM 分配 → Developer 编码 → Reviewer 审查 → Tester 测试 → Docs 文档 → PM 闭环
- 数据采集/治理：PM → Data Agent (L0采集+L1治理) → Developer → Reviewer → Tester
- 遇到 Bug 时由 Debugger 诊断，不改代码，输出修复方案交给 Developer
- 所有 Agent 启动时自动加载本文件了解架构规范

## 决策追踪系统 (Decision Tracking System)

### 目的
将 bug 定位从 O(n) 全量代码搜索降为 O(1) 决策 ID 精准跳转。

### 核心概念
每个功能/行为/代码块分配唯一决策 ID，运行时自动记录追踪日志：

| ID 层级 | 格式 | 含义 | 示例 |
|---------|------|------|------|
| 模块级 | `MOD_XXX` | 整个 .py 文件 | `MOD_GOV` |
| 函数级 | `MOD_XXX.F_NNN` | 某个函数 | `MOD_GOV.F_001` |
| 决策点 | `MOD_XXX.D_NNN` | if/else/循环分支 | `MOD_GOV.D_003` |

### 运行时日志格式
```
[TRACE] 14:30:01 | MOD_GOV.F_001 | enter | in: len=24
[TRACE] 14:30:01 | MOD_GOV.D_003 | enter | in: n=24
[TRACE] 14:30:01 | MOD_GOV.D_003 | exit | out: n=21 | 12.4ms
[TRACE] 14:30:01 | MOD_GOV.D_003 | [ERR] | KeyError: 'lon'
```

### 使用方式

```python
from core.tracker import track, TrackContext, trace_log, trace_error, register_track_id

# 注册 ID
register_track_id("MOD_GOV.F_001", "坐标转换入口")

# 函数追踪
@track("MOD_GOV.F_001", track_args=True)
def transform_coordinates(df):
    ...

# 决策点追踪
with TrackContext("MOD_GOV.D_003", input_n=24):
    df = do_filter(df)

# 手动埋点
trace_log("MOD_GOV.D_005", detail=f"filtered {n} rows")

# 异常追踪
except Exception as e:
    trace_error("MOD_GOV.F_001", "transform failed", exc=e)
```

> 模块 ID 分配表详见 `AGENTS.md` 铁律9说明 + `core/tracker.py` 注册表（代码即真相）。

### Debug 工作流
```
报错 → 看 [TRACE] 日志 → 定位出错决策 ID → grep 跳转代码 → 精准修复
```
## Toolbox 缁熶竴宸ュ叿闆嗗眰锛?026-07-25 路 鍒嗘敮 toolbox-unified-toolset锛?
EMC 鐨?GIS 宸ュ叿涓?Toolbox 鎵嬪姩宸ュ叿鏇炬槸涓ゅ瀹炵幇锛坱ools.js 鍐呰仈 vs *-tool.js锛夈€傛湰灞傜粺涓€涓猴細
**涓ゆ潯瑙﹀彂璺緞锛圗MC 瀵硅瘽 / Toolbox 鎵嬪姩锛夎皟鐢ㄥ悓涓€鎵瑰伐鍏锋ā鍧楋紝鍥惧眰浜у嚭涓€鑷达紙鍚屼竴 _execute 鏍革級**銆?
### 鏋舵瀯

`
瑙﹀彂灞?  璺緞涓€ EMC: frontend/js/ai_qa/tools.js锛堣杽濮旀墭锛氬弬鏁板綊涓€/observation 鏂囨/registry 绨胯锛?  璺緞浜?UI : index.html tool-row 鈫?param-panel pp-pane dialog锛堜笁姝ュ悜瀵硷級
                鈹? 閮借皟 generateXxxForAI(opts) / 鍚屼竴 _execute 鏍?宸ュ叿闆嗗眰锛堝悓灞傜骇銆侀珮鍐呰仛浣庤€﹀悎銆佹ā鍧楅棿浜掍笉 import锛?  frontend/js/         heatmap-tool.js 路 grid-tool.js 路 buffer-tool.js锛堝師鍦奥穊uffer 鍙屾ā寮忓悎涓€锛?  frontend/js/toolbox/ shared.js锛堝敮涓€鍏变韩鍩哄缓锛?                       zonal-tool.js 路 area-stats-tool.js 路 rank-tool.js 路 vector-tool.js锛堜簲鎿嶄綔鍚堜竴锛?                       nearest-tool.js 路 hotspot-tool.js锛堢函鍐呭祵路鏃?UI锛?鍚庣  /api/v1/spatial/*锛坔eatmap/grid/buffer-cover锛壜?/api/v1/geo/*锛堝叾浣欏叏閮风粡 api.js geoPost锛?`

### 渚濊禆绾㈢嚎锛堝崟鍚戯級

i_qa/tools.js 鈫?toolbox/* + js/涓夊伐鍏穈锛沗toolbox/* 鈫?shared.js + state/map/sidebar/import/api/landuse_colors/grid-tool锛?**toolbox 妯″潡涓ョ import ai_qa/**銆俿hared.js import sidebar 涓烘棦鏈夊惊鐜ā寮忥紙grid-tool.js:12 鍚屄?export function 鎻愬崌澹版槑涓嬭繍琛屾椂璋冪敤 TDZ 瀹夊叏锛涗弗绂?sidebar 椤跺眰 const 姹傚€间緷璧?toolbox export锛夈€?
### 妯″潡濂戠害

- **ForAI 杩斿洖**锛堜笌 generateGridForAI 鍚屾瀯锛夛細{ layerId, layerName, featureCount, fc, rows?, ... }锛?  澶辫触 throw锛堝鎵樺眰 catch 褰掍竴 [ERR] 鏂囨锛夈€?- **妯″潡楠ㄦ灦**锛氭瘡妯″潡 _execute(params, {editLayerId, silent}) 鍗曚竴鎵ц鏍?+ openXxxDialog(layerId)
  锛堢紪杈戞€佷粠 paint._ui 鍥炲～锛? initXxxTool() + generateXxxForAI(opts)銆?- **paint._ui**锛氭墍鏈変骇鐗╁啓 _ui={tool, ...params} 鏀拺渚ф爮瑕佺礌鎸夐挳缂栬緫鍥炲～锛沚uffer 鍙屾ā寮忔樉寮?  kind:'cover'|'emotion'锛堝瓨閲忔棤 kind 鎸?color 鍒ゆ嵁锛氭湁 color鈫抍over 鍚﹀垯 emotion路绂?distance/sourceLayer锛夈€?- **鍛藉悕**锛圕6 绾㈢嚎锛夛細鍚?鍐呭/鑼冨洿/瑕佺礌鍚嶏紝鍕垮伐绋嬪墠缂€锛堝銆岃仛鍚埪疯鏀垮尯銆嶃€屾花姹熷叕鍥?00m銆嶃€屼氦路鍟嗕笟鐢ㄥ湴涓庤タ闄靛尯銆嶏級銆?- **浜掓枼/鑱氱劍鍒嗗伐**锛氭ā鍧?_execute 钀藉浘璋?enforceMutualExclusion锛堟墜鍔ㄥ満鏅悓绫荤嫭鍗狅級锛汦MC 濮旀墭灞?  _adoptToolboxResult锛? _registerToolboxLayer + consumed 娓呯悊 + AI 缁?parentId + focusOnlyResults
  娌夋蹈鑱氱劍 + layers:changed 琛ュ彂锛夆€斺€斾袱璺緞鍥惧眰浜у嚭涓€鑷淬€佽仛鐒﹁涓哄樊寮傚寲锛堜骇鍝佹湰鎰忥級銆?
### EMC 娴佹按绾挎壙閲嶅绾︼紙C1-C6锛?
宸ュ叿鍚嶄笉鍙橈紙stages.js SKILL_DEFS 鈫?paradigm.py TEMPLATE_REGISTRY锛? 杩?{observation, data:{rows?, layerId?}}
锛坃ANALYTICAL_TOOLS 璁?rows 闈炵┖锛? 鍙傛暟 schema 闆跺彉鍖栦笖鍐呴儴瀛楁绂?mode|how锛坃PARAM_ALIAS 閬胯路鐢?kind锛?
setToolContext provenance锛坮egistry//瀵硅处锛? _GEO_TOOLS F3 gate锛堝悕涓嶅彉鍗冲厤鐤級/ 鍛藉悕璇箟锛坃verifyClaims锛夈€?
### UI 鍏ュ彛

Toolbox 椤?7 鍏ュ彛锛欻eatMap / Grid / Buffer锛堝弻妯″紡锛氳鐩栬寖鍥绰峰湀鍐呮儏缁級/ Zonal锛堣仛鍚埪峰鍖哄姣旓級/
闈㈢Н缁熻 / Rank / 鐭㈤噺鍒嗘瀽锛堝彔缃疯鍓锋娊鍙柭峰悎骞堵风瓫閫夛級锛沶earest/hotspot 绾唴宓屼粎 EMC 鍙Е鍙戯紱
澶氱淮褰掑洜淇濇寔鍗犱綅銆?
### 楠岃瘉璁炬柦

- 	ests/browser/tool_obs_snapshot.py锛?2 宸ュ叿 observation 蹇収锛?-save 鍩虹嚎 / --diff 姣斿路
  鍩虹嚎 	ests/reports/toolbox-obs-baseline.json锛夆€斺€斿鎵樻敼閫犻€愬瓧瀹堥棬锛堟紨绀洪摼鍛介棬锛夈€?- 	ests/browser/test_toolbox_unified.py锛? 鍏ュ彛/涓よ矾寰勬瘮瀵?Buffer 鍙屾ā寮?鍥炲～/color 鍒ゆ嵁/console 绾㈢嚎銆?- 	ests/browser/test_toolbox_pipeline.py锛欵MC 娴佹按绾挎満鍒舵柇瑷€锛堟棤 [ERR]/geo 200/鍑哄彛瑁佸畾路瀹瑰繊 LLM 璺敱鏂瑰樊锛夈€?- 鎵ц鎵嬪唽锛歚.codebuddy/plans/toolbox-unified-toolset-execution.md锛坴2.2路鍚?EMC 濂戠害 C1-C6 涓庡叓姝?DoD锛夈€?