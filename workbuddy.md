# WorkBuddy 使用记录 · 麦门三高参谋

本项目全程在腾讯 WorkBuddy 中完成麦当劳官方 MCP 的接入与实测（2026-10-21），记录如下。

## 接入（WorkBuddy 自定义 MCP）
- 在 WorkBuddy「MCP 服务管理」中以自定义配置接入 `mcd-mcp`：Streamable HTTP，端点 `https://mcp.mcd.cn`，请求头 `Authorization: Bearer <Token>`（Token 在 open.mcd.cn 控制台领取，只保存在 WorkBuddy 本地配置中，未出现在聊天、仓库或任何文件中）
- 首次连接完成信任确认后启用：**38/38 个工具已启用**

## 在 WorkBuddy 中实际调用的工具（全部只读）
| 日期（北京时间） | 工具 | 结果 |
|---|---|---|
| 2026-10-21 19:27 | `list-nutrition-foods` | 返回 160 条营养数据（traceId 3336e949b82e96c65984315d435e6a81），原文回填 `data/nutrition.json` |
| 2026-10-21 19:40 | `query-nearby-stores` | 返回北京西站一带 5 家营业门店（traceId 0d90eec68a406d82af7959ab53bc81d1） |
| 2026-10-21 22:36–22:37 | `query-meals` | 门店 1950363：打烊后无 reservationDate 报 600057；按预约餐段拉取早餐段 52 单品、正餐段 74 单品 |
| 2026-10-21 22:37 | `calculate-price` | 麦辣鸡腿汉堡（productCode 1440）核价 2600 分 = ¥26.00，与菜单价一致（traceId 2ec97ad4466fcc7ce21a7c86d108460b） |

## 纪律
- 只调用只读工具；`create-order`、`auto-bind-coupons`、`draw-lottery` 等写操作从未调用
- 每次调用都要求 WorkBuddy 输出工具返回原文、不总结不改写，原文作为实测证据存档在 `data/` 并写入 `docs/TESTREPORT.md`
- 本地确定性求解器（`scripts/advisor.py`）负责配餐计算，数值不经 LLM 改写
