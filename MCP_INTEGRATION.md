# MCP_INTEGRATION · 麦门三高参谋的 MCP 接入说明

本项目通过麦当劳官方 MCP Server（`mcd-mcp`）获取真实数据，接入与实测口径如下（实测日期：2026-10-21，证据见 `docs/TESTREPORT.md`）。

## 接入方式
- 传输：Streamable HTTP，端点 `https://mcp.mcd.cn`
- 鉴权：请求头 `Authorization: Bearer <MCP Token>`；Token 在 open.mcd.cn 控制台领取，只填在本地 MCP Client（本项目开发期用 WorkBuddy）里，**不进仓库、不进对话、不写进任何文件**；仓库内的 `mcp-config.example.json` 只有占位符
- 限流：每 Token 600 次/分钟（官方仓库 README）

## 本项目实际调用的工具（全部只读）
| 工具 | 用途 | 实测结果（2026-10-21） |
|---|---|---|
| `list-nutrition-foods` | 全量营养表 | 160 条；英文表头 `{productName,nutritionDescription,energyKj,energyKcal,protein,fat,carbohydrate,sodium,calcium}`，**无糖列、无价格列**；解析器 `scripts/parse_nutrition.py` 回填 `data/nutrition.json` |
| `query-nearby-stores` | 按位置查营业门店 | 返回 storeCode/营业时间/预约时段；实测 beCode 字段未返回、经纬度为 0.0 |
| `query-meals` | 门店在售菜单 | 有营业时间门禁：打烊后不带 `reservationDate` 报 600057；须按餐段带 reservationDate 拉取（本店早餐段 52 单品 / 正餐段 74 单品）；菜单价单位是元 |
| `calculate-price` | 官方核价 | 入参 productCode + quantity，**金额单位是分**；实测麦辣鸡腿汉堡（1440）返回 2600 分 = ¥26.00，与菜单价逐分一致 |
| `now-time-info` | 当前时间/餐段判断 | 已在工具清单中，未在本轮实测单独调用 |

## 安全边界
- 禁用一切写工具：`create-order`、`auto-bind-coupons`、`draw-lottery` 等从未调用，代码中不存在；下单只能由用户本人在客户端另行确认
- 求解是本地确定性计算（`scripts/advisor.py`），营养数值不经 LLM 改写；无真实数据时明确标注「示例数据演示」
- 输出只做营养数据核算，不构成医疗/营养专业建议；控糖画像因官方营养表无糖字段，不能用本数据单独验证（报告中如实标注，不以碳水冒充糖）
