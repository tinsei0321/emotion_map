---
name: apply-design-sense-no-bounce
description: 别把能据设计常识+用户习惯自判的决策甩回用户；先调直觉与 memory 习惯，勿回弹琐问
metadata: 
  node_type: memory
  type: feedback
  originSessionId: ab9ecdfe-67aa-400a-9932-8d2c86b24a90
  modified: 2026-07-21T16:49:51.300Z
---

用户严厉反馈：近轮 CPD UI 调整中，我「过度字面分析 + 把本该自己定的设计决策甩回用户」，犯低级错误、冒出不该问的问题，像是忘了设计美学/UI 常识/交互逻辑/用户习惯。

**Why**：我把「给推荐不穷举」「不跑非必要验证」「调动次数优先」记住了，却丢了**先用设计常识 + memory 里的用户习惯直接拍板**这一层。陷进字面纠结（如「上移」+「180px」的字面矛盾）和 needless option-surfacing（如「18px 是否太小」反问），消耗用户耐心。

**How to apply**（设计决策先过这关，再考虑问）：
1. **方向/尺寸/颜色**：用 UI 常识直接定。「上移」= 更靠上（更小 top）；按钮触达 ≥ 合理下限（输入钮别 <28-32，工具钮可 20 但锁正方形）；浅底/胶囊用柔和浅灰/米白，**纯白易突兀**（用户偏好柔和，见 [[frontend-default-light-theme]]）。
2. **用户习惯在 memory 里**：先 recall——`frontend-default-light-theme`（浅底柔和）/`capsule-button-design-language`（无线框+阴影+选中蓝+悬停灰+紧凑）/`design-language-consistency-iron-rule`（跨场景一致，改一处 grep 同类）/`ramp-discrete-segments`（离散分段）/`tip-popup-unified-hover-design-language`。
3. **只在真歧义（架构分叉、不可逆、数据语义）问**；纯视觉微调（位置/尺寸/圆角/配色）直接按常识 + 习惯定，交付后用户 F5 校正。问之前先想「这个我能否据常识+习惯自己拍？」能→别问。
4. **3+5 按钮组、正方形、等高对齐、断开格局**这类是设计语言铁律，主动维护，别等用户指出变形。
5. **EMC/主题组件颜色一律走 theme var**（`var(--geojson-color-*)` / `var(--emc-accent)` / `var(--emc-divider)`），**严禁硬编码** hex/`rgba(255,255,255,*)`——Dark/Light 双模式切换时硬编码值不跟随→浅字浅底看不清、Dark 件在 Light 下突兀（追问胶囊、容量圈 tooltip 反复踩此坑，5.169 根治）。改任何 EMC 内组件先 grep 硬编码色→换 var。position:fixed 在 body 的浮层（如 .aiq-cap-tip）用 `[data-theme="light"] .xxx`（不缀 #emc-panel）。关联 [[design-language-consistency-iron-rule]]、[[frontend-default-light-theme]]。

落地：折叠胶囊纯白→浅灰、输入钮 18→32、工具钮锁 aspect-ratio + 3+5 margin-break（commit 5.159）。关联 [[cpd-soft-collapse]]、[[design-language-consistency-iron-rule]]、[[professionalize-user-wording]]。
