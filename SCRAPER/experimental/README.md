# experimental/ — L0 爬虫骨架隔离区（CB-39 P0-1·D1 裁定）

> 状态：**未贯通的实验骨架**，移出主线 scrapy 加载（`settings.py SPIDER_MODULES=[]`）。

## 为什么隔离

- 四个 spider（meituan/su12345/weibo/xiaohongshu）从未跑通生产链路——L0 实际获取走**购买/中转站途径**（CLAUDE.md 数据红线）。
- 文档曾以「L0~L4 五级管线」描述系统，而 L0 spider 属「存在但不贯通」——本轮（CB-39 P0-1 诚实度修复）显式隔离，消除能力声称与实际的错位。

## 恢复路径

贯通某 spider 时：`git mv` 回 `SCRAPER/spiders/` + `settings.py` 恢复 `SPIDER_MODULES=['spiders']` + 补测试与追踪埋点（MOD_SCRAPER 编号续连）。
