# 麦门三高参谋 · mcd-sanguan-advisor

> 别人帮你算怎么吃麦当劳**最省钱 / 最低卡**，三高参谋帮血压、血糖、血脂敏感的人算：**这一餐的钠、糖、脂肪到底有没有越线，越线了换哪一样能降多少。**

**在线演示**：👉 [jgit853.github.io/mcd-sanguan-advisor/demo.html](https://jgit853.github.io/mcd-sanguan-advisor/demo.html)（打开即玩，单文件、零依赖、无需 Token）：选画像 → 出 Top3 组合 → 还能查「换个低钠的差多少」。也可以把本仓库的 `demo.html` 下载后用浏览器打开。

> 2026 麦当劳程序员创意开发大赛参赛作品（使用 WorkBuddy 开发）。参赛者独立开发，非麦当劳官方产品。

> 本项目已链接认可 [LINUX DO](https://linux.do) 社区，感谢佬友们的反馈。

## 为什么做这个
- 麦当劳官方 MCP 的 `list-nutrition-foods` 一次给出全量餐品的钠含量，但现有参赛作品里，钠基本只是「顺带输出的一个数字」，没有作品把钠做成**第一硬约束**。
- 中国高血压患者约 2.45 亿（公开流行病学口径量级），这批人不是不吃快餐，而是没人帮他们把一顿快餐的钠算清楚。本 Skill 就是补这个位。

## 功能
| 模式 | 你说 | 它做 |
|---|---|---|
| 画像配餐 | 「三高综合，预算 45」 | 拉官方营养数据 → 确定性约束求解 → Top3 组合（钠/糖/脂肪/热量/蛋白/价格全列） |
| 单项画像 | 「控糖」「控脂」 | 控糖硬顶糖 ≤25g/餐（自动排除含糖饮料）；控脂硬顶脂肪 ≤22g 且排除油炸品 |
| 换餐参谋 | 「麦辣鸡腿堡换个低钠的」 | 同类更低钠替代 Top3，带量化差值：例 麦辣鸡腿堡(钠1240mg) → 吉士汉堡包(680mg)，少 560mg（-45.2%）* |
| 钠自查 | 「这顿钠超标了吗」 | 按所选组合核算总钠并对照画像上限给结论 |
| 可视化演示 | 打开 demo.html | 画像切换、Top3 卡、钠仪表、换餐对比，无 Token 离线可玩；同目录有 data/nutrition.json 时自动切换官方数据 |

* 示例数值来自内置演示数据；实测运行以 MCP 官方实时数据为准，仓库输出会明确标注数据来源状态。

## 设计原则
1. **数值不进 LLM**：营养数据与求解全部走本地确定性脚本（`scripts/advisor.py`），结果可复算；LLM 只负责理解需求与讲解。
2. **只读优先**：只调用查询/核价类工具；不自动下单、不自动领券。下单需用户二次确认（本仓库不含下单实现）。
3. **诚实标注**：无 Token / MCP 不可用时自动降级为示例数据，并在输出首行标注，绝不冒充实时数据。

## 快速开始（离线演示，无需 Token）
```bash
python3 scripts/test_advisor.py # 9 项自测
python3 scripts/advisor.py --profile all --budget 45
python3 scripts/advisor.py --swap 麦辣鸡腿堡
```

## 接真实数据（WorkBuddy）
1. 申请 Token：https://open.mcd.cn/mcp 手机号登录 →「控制台」→「激活」→ 复制 Token。
2. WorkBuddy 左侧边栏→→→，粘贴 `mcp-config.example.json`，把 `${MCD_MCP_TOKEN}` 换成你的 Token（或用环境变量注入），保存并启用。
3. 安装 Skill：把本目录复制到 `~/.workbuddy/skills/mcd-sanguan-advisor/`（Windows 为 `%USERPROFILE%\.workbuddy\skills\`）。
4. 在对话框说：「我血压偏高，预算 40，帮我配一餐麦当劳」即可触发。首次触发会把 `list-nutrition-foods` 的结果回填到 `data/nutrition.json`，之后求解全部基于官方数据。

## 目录
```
SKILL.md # Skill 定义 (触发/工作流/硬约束)
scripts/advisor.py # 确定性求解器 (画像约束 + 换餐)
scripts/test_advisor.py # 离线自测 (9 项)
data/ # nutrition.json 由 MCP 实测回填 (仓库内仅.gitkeep)
references/api-notes.md # MCP 工具契约与实测偏差记录
mcp-config.example.json # MCP 连接配置示例 (Token 走环境变量)
```

## 免责
本项目输出只做营养数据核算，不构成医疗、营养或其他专业建议；餐品、价格、营养数据以麦当劳官方渠道实时结果为准。Token 请妥善保管，不要提交到任何仓库。

---
本赛按 GitHub Star 排名，如果这个项目对你有用，欢迎点一个 Star 支持一下。
