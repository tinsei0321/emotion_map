# 公司 · 工作交接卡

> **位置**：公司 | **最后更新**：2026-08-20 凌晨（home 收工·office 到岗续接） | **同步**：随 `EMC_harness_dsh` 推送。
> **到岗第一读**：`memories/repo/session-handoff.md` 当前节点 + `docs/todo.md` 2026-08-20 段 + `discuss/PT-CB6-大脑实测记录_dsh-2026-08-20.md` §四。

## 收工快照（08-20 凌晨 home 班）

- **PT-CB6 S6 用户复测通过**：Q2「12345 热线诉求最密集的 10 个社区是哪些？把结果铺到地图上」端到端成图；用户确认正常。
- **渲染通道三坑修复**（重要，office 勿再踩）：
  1. `frontend/serve.py` 单线程 TCPServer 被 SSE 占死 → 已改 `ThreadingTCPServer` + `daemon_threads=True`。
  2. `frontend/js/render_client.js` 缺 `spec_id` 去重 → 已加 `_seenSpecIds`，SSE 重连不再循环增删图层。
  3. `DATA/exports/render_inbox/` 旧测试 spec 积压 → 15 个移入 `_backup/`，根目录仅留内联 TOP10 spec `1787161960132-3411.json`。
- 最终图层：`[dsh] [真实] 12345热线诉求最密集TOP10社区(真实)`（内联 GeoJSON·community_choropleth_v1·value_field=诉求总量·community=174）。

## office 到岗动作

1. `git pull origin EMC_harness_dsh`。
2. 读 `docs/todo.md` 2026-08-20 段 + `discuss/PT-CB6-大脑实测记录_dsh-2026-08-20.md` §四。
3. **S7 回收判读**（zcode 主手）：将新增三个显示面缺陷并入 PT-CB6 缺陷清单：
   - serve.py 单线程 SSE 阻塞；
   - render_client 缺 spec_id 去重；
   - render_inbox 积压旧 spec 重放。
   裁决是否补测、是否修工具描述/文档。
4. 按主手排期决定是否继续 Q3/Q4 用户复测或进入下一批。

## 待办/风险

- `render_inbox/_backup/` 15 个旧 spec 未删，确认无用后可清。
- `tests/_tmp_*` 临时调试文件未提交，确认后可删。
- main 冻结勿动；一切在 `EMC_harness_dsh`。

## 禁止事项

- main 冻结勿动；白名单外禁碰；Excel 锁文件不提交；未裁决不 mv 数据文件。
