# 03 - 4×5 矩阵映射

## 文件
- `poi-mapping-4x5.md`（16KB）

## 内容
- **4 领域**：urban_planning / urban_renewal / urban_operation / urban_governance
- **5 要素**：facility / environment / service / culture / event
- **20 个矩阵组合**：每个组合的语义定义 + 典型 POI
- **百度 POI 完整映射表**：每个百度二级分类 → domain/element
- **真实数据接入路径**：百度/高德 API 代码示例

## 矩阵设计逻辑

| 领域 | 关注重点 | 典型 POI |
|---|---|---|
| **urban_planning** 规划 | 控规调整、用地性质、重大设施 | 地铁站、桥、产业园、规划展览馆 |
| **urban_renewal** 更新 | 老旧改造、历史街区、棚改 | 老字号、历史建筑、文创、改造指挥部 |
| **urban_operation** 运营 | 商业运营、夜经济、文旅节庆 | 商场、影院、KTV、公园、市集 |
| **urban_governance** 治理 | 投诉、应急、防汛、市容 | 政务中心、消防、医院、应急避难 |

## 模拟数据权重建议

| 领域 | 占比 | 触发场景 |
|---|---|---|
| urban_operation | 45% | 商业、餐饮、文旅、夜经济 |
| urban_governance | 25% | 政务、医疗、交通、应急 |
| urban_renewal | 20% | 老旧小区、历史街区 |
| urban_planning | 10% | 控规、新基建、产业园 |

## 关键映射规则（精选）

### 美食类
- 中餐厅/外国餐厅/小吃 → `urban_operation × service`
- 咖啡厅 → `urban_operation × culture`
- 茶座/酒吧 → `urban_operation × culture/event`

### 房地产
- 住宅区 → `urban_renewal × service`（老小区偏更新）
- 写字楼 → `urban_operation × service`

### 交通设施
- 飞机场/火车站/公交站 → `urban_governance × facility`
- 地铁站/桥 → `urban_planning × facility`（重大规划）
- 充电站 → `urban_planning × facility`（新基建）

### 旅游景点
- 公园/植物园 → `urban_operation × environment`
- 博物馆/文物古迹/寺庙 → `urban_renewal × culture`
- 风景区 → `urban_operation × environment` 或 `urban_renewal × culture`

## 使用场景
1. L1 数据生成时，根据 POI 类型自动判定 `domain` 和 `element`
2. L2 极性分析时，按 4×5 矩阵聚合
3. 时间轴对比时，按 4×5 矩阵观察变化

## 完整内容
详见 `poi-mapping-4x5.md`（含百度 API 接入代码示例）。
