# 情绪地图 — 前端启动手册（初学者版）

> 这是**新的主界面**：MapLibre GL JS 前端（geojson.io 1:1 风格外壳）。
> Streamlit 旧页面**仍在、没删、作为遗留 MVP 暂时保留**（见文末），但**新功能一律写进这里**。

---

## 一、启动

### 方式 A：双击 `start.bat`（推荐·一键开主页 + 测试页）

项目根的 **`d:\Github\emotion_map\start.bat`** 双击即可：

- 自动清旧 serve / 后端 → 起 serve（no-cache）→ **serve 一就绪就自动开「主页 + 测试页」两个标签**
- 这个黑窗口要一直开着；**Ctrl+C 同停前端 + 后端**。

- **主页（纯界面）**：`http://localhost:8080/frontend/index.html`
- **测试页（带测试飞轮）**：`http://localhost:8080/frontend/index.html?test=1`

> 不想看测试时，关掉那个标签即可；`?test=1` 不加就是纯主页。
> 测试报告落盘在项目根 `tests/reports/`（文件名 = 日期 + 编号 + 类型）。

### 方式 B：手动起（3 步·VS Code）

> 用 VS Code 操作最省事。命令里的 `py` 是 Windows 的 Python 启动器（别用 `python`，本机 `python` 会报错）。

**第 1 步：打开终端**
- VS Code 打开项目文件夹 `d:\Github\emotion_map`
- 顶部菜单 **Terminal → New Terminal**（或按 `` Ctrl+` ``）
- 确认终端**当前路径在项目根** `d:/Github/emotion_map`（不是在 `frontend/` 里！）
  - 不确定就先敲：`cd d:/Github/emotion_map` 回车

**第 2 步：启动本地服务器（no-cache，推荐）**
在终端输入并回车：
```
py frontend/serve.py 8080
```
看到这行就成了：
```
[OK] frontend serve on http://localhost:8080 (no-cache)
```
（这个终端窗口要**一直开着**，关了页面就打不开了。）

> **为什么用 `serve.py` 不用 `py -m http.server`**：`serve.py` 对所有响应发 `Cache-Control: no-store` 头，浏览器**每次都加载最新 JS/CSS**，彻底告别"改了代码不生效、换个浏览器才正常"的缓存残留问题。无需再手动 Ctrl+Shift+R 硬刷新。
> （临时回退：`py -m http.server 8080` 仍可用，但会有缓存问题。）

**第 3 步：浏览器打开**
主页地址栏粘贴：
```
http://127.0.0.1:8080/frontend/index.html
```
要开**测试飞轮**（100 例 + 重跑 + 行内摘要 + 存报告）就加 `?test=1`：
```
http://127.0.0.1:8080/frontend/index.html?test=1
```
看到 **深蓝标题栏「宜昌市情绪地图 v1.0」+ 工具栏 + 浅色矢量底图（CARTO Positron）**，就成了。

**停止服务器**：回到那个终端，按 `Ctrl + C`。

---

## 二、改完代码怎么看效果

| 改了什么 | 怎么刷新 |
|----------|----------|
| `frontend/` 下的 CSS / JS / HTML | 浏览器按 **F5** 即可（用 `serve.py` 启动则**无缓存**，必定加载最新版） |
| `design/tokens.json`（配色/尺寸 token） | 终端先跑 `py design/generate_css.py`，再 F5 |
| 极少数情况仍怀疑缓存 | **Ctrl+Shift+R** 硬刷新（用 `serve.py` 一般无需此操作） |

---

## 三、为什么必须从「项目根」启动

前端底图引用的是相对路径 `../apps/static/tianditu_*.json`。
- 从**项目根**起服务器 → `../apps/static/` 指向真实文件 ✅
- 从 `frontend/` 里起服务器 → 路径越界，底图 **404**（地图灰屏）❌

所以第 1 步一定要确认终端在 `d:/Github/emotion_map`，不是在 `frontend/`。

---

## 四、常见问题

- **"Address already in use"（端口被占）**：换个端口，`py -m http.server 8081`，浏览器地址也改成 `8081`。
- **地图灰屏 / 底图瓦片不出**：检查 `apps/static/` 下有没有 `tianditu_img_nolabel.json` 等 4 个底图 JSON。
  这几个文件**被 gitignore（含 key）不会随 git 同步**，换机器要手动补，见 `memories/repo/session-handoff.md`「到公司第一步」。
- **页面全白**：浏览器按 **F12** → Console 看红字报错，多半是某个 JS 路径或语法问题。
- **终端敲 `python` 报 "exit 49"**：本机要用 `py`，不要用 `python`。

---

## 五、Streamlit 旧页面（遗留，可选）

- **状态**：代码仍在 `apps/`，**没删**，作为遗留 MVP 暂时保留。
- **要跑的话**：终端 `py launch.py`，浏览器开 `http://localhost:8501`。
- **定位**：不再加新功能；MapLibre 前端（本目录）是主界面，迁移收尾时 Streamlit 下线。

---

## 六、目录速览

```
frontend/
├── index.html          ← 入口（浏览器打开的就是它）
├── css/                ← 样式（layout/toolbar/sidebar/panel/popup/...）
├── js/                 ← 逻辑（main/map/panel/toolbar/sidebar/popup/state）
└── (设计 token 单源在 ../design/tokens.json，经 generate_css.py 生成 css/tokens.css)
```
