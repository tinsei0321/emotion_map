# Key 轮换 SOP（CB38 P0-3 配套 · 2026-08-16）

> 目标：作废可能泄露的两把 key（AMAP_KEY / DEEPSEEK_API_KEY），全程不断调用。
> 背景：CB38 审计 §6.5 —— serve 曾全网卡服务仓库根（GET /.env 可读 key），且审计过程存在一次泄露进子代理会话的风险披露。
> 已完成（无需用户操作）：frontend/serve.py 已加路径白名单 + 默认仅绑 127.0.0.1（暴露面已封堵，实测 /.env → 403）。

## 四步轮换（旧 key 在第 4 步前始终有效）

1. **控制台新建 key（旧 key 先不删）**
   - AMAP：https://console.amap.com → 应用管理 → 你的应用 → 新增 key（类型选「Web服务」）
   - DeepSeek：https://platform.deepseek.com → API Keys → 创建
2. **复制环境文件并填入新 key**
   ```powershell
   copy .env .env.new   # 编辑 .env.new 中 AMAP_KEY / DEEPSEEK_API_KEY 两行为新值
   ```
3. **先验证后切换（核心防断流步骤）**
   ```powershell
   py tools/verify_keys.py --env-file .env.new
   ```
   - 两项 [OK] 才继续；任一 [ERR] 回控制台检查（key 类型/余额/权限），此期间线上旧 key 照常工作
4. **全绿后切换 + 复验 + 作废旧 key**
   ```powershell
   copy .env.new .env                 # 覆盖（serve 会在下次启动注入新 key）
   py frontend/serve.py 8080          # 重启（Ctrl+C 同停后端）
   py tools/verify_keys.py            # 复验线上 .env
   # 最后：控制台删除旧 key（作废泄露源）；删除 .env.new
   ```

## 验证器说明（tools/verify_keys.py）

- 调用路径与生产对齐：DeepSeek=ai_qa/llm.py（v1/chat/completions·flash 档）；AMAP 三探针=core/geocode.py 实际依赖（place/text 主力 + regeo 兜底为通过门槛，geocode/geo 仅提示）
- 绝不打印 key 值，只打印键名/存在性/HTTP 结果；退出码 0/1 可接 CI
- 存量现象（与本次无关）：当前 AMAP key 的 geocode/geo 单接口返回 infocode=30001（place/text 与 regeo 正常），生产对该路径有本地兜底；轮换新 key 后可观察是否转绿

## 安全备注

- .env 已被 .gitignore 排除（勿提交）；.env.new 同理不要提交，切换完成后删除
- serve 若需局域网演示：py frontend/serve.py 8080 --host=0.0.0.0（显式放开，白名单仍限制可读路径），演示后切回默认 127.0.0.1
