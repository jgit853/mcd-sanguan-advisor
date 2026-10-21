# MCP 工具契约与实测偏差记录

来源：本项目整理 + 同赛道公开参赛作品的实测报告交叉印证（2026-10）。接入前先读，避免重复踩坑。

## 本项目用到的只读工具
| 工具 | 用途 | 注意 |
|---|---|---|
| `now-time-info` | 当前时间/餐段判断 | 无副作用 |
| `query-nearby-stores` | 按位置找营业门店 | 恢复上次门店前需重新确认营业状态 |
| `query-meals` | 门店在售菜单 | 不同门店在售集合不同，求解前以目标门店菜单为准 |
| `list-nutrition-foods` | 全量营养数据（实测 160 条：能量 kJ/kcal、蛋白/脂肪/碳水/钠/钙） | **返回自定义表格字符串，非 JSON**；实测表头为英文 `{productName,nutritionDescription,energyKj,energyKcal,protein,fat,carbohydrate,sodium,calcium}` 并带 `[160]` 条数前缀，**无糖列、无价格列**；需写解析器（已兼容中英表头）；本项目 SKILL 工作流要求解析后回填 `data/nutrition.json` |
| `calculate-price` | 官方核价 | 入参是 `productCode + quantity`（不是 mealCode/count）；**金额单位是分**，展示须 /100 |

## 响应信封
MCP 响应是给 LLM 的 markdown/文本，真实数据裹在 `{success, code, data}` 信封里，解析时先拆信封再取数，不要直接对整段文本做 JSON 解析。

## 写操作（本项目禁用，仅记录边界）
- `create-order`、`auto-bind-coupons`、`draw-lottery` 等均为真实写操作（领券/下单/扣积分）。本项目硬约束：不自动调用；`draw-lottery` 与任何「运势」类本地算法无关，不要混淆。
- 限流：有参赛作品记录 MCP Token 限流约 600 次/分钟，批量核价时控制并发，不要无脑重试写请求。

## data/nutrition.json 格式
```json
{"items": [{"name": "板烧鸡腿堡", "cat": "main", "price": 22.5, "kcal": 400,
            "protein": 26, "fat": 13, "carbs": 42, "sodium": 890, "sugar": 7, "fried": false}],
 "source": "mcp list-nutrition-foods", "snapshot_date": "YYYY-MM-DD"}
```
`cat` 取值：main（主食/汉堡）/ side（小食）/ drink（饮品）。价格如与门店菜单不一致，以 `query-meals` + `calculate-price` 为准。
