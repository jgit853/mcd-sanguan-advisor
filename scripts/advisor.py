#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
麦门三高参谋 (mcd-sanguan-advisor) — 确定性配餐求解器

输入: 用户画像约束 (控钠/控糖/控脂/综合) + 预算 + 可选「想吃」单品
数据: 优先读 data/nutrition.json (由 MCP list-nutrition-foods 实测回填),
      文件不存在时用内置示例数据 (demo_sample=True, 输出会标注)。
输出: Top3 组合 (主食+小食+饮品) + 换餐建议 (同类更低钠替代, 带量化差值)

硬规则:
- 所有营养数值来自数据文件, 本脚本不猜数; 示例数据仅供离线演示。
- 只做只读求解, 不下单、不领券; 下单必须由用户在 WorkBuddy 里另行确认。
- 输出不构成医疗/营养专业建议。
"""
import itertools
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(HERE, "..", "data", "nutrition.json")

# 内置示例数据: 公开营养表量级近似值, 仅供离线 demo; 实测以 MCP 官方数据回填为准。
SAMPLE_ITEMS = [
    {"name": "巨无霸", "cat": "main", "price": 24.5, "kcal": 530, "protein": 25, "fat": 26, "carbs": 44, "sodium": 1010, "sugar": 9, "fried": False},
    {"name": "板烧鸡腿堡", "cat": "main", "price": 22.5, "kcal": 400, "protein": 26, "fat": 13, "carbs": 42, "sodium": 890, "sugar": 7, "fried": False},
    {"name": "麦香鸡", "cat": "main", "price": 13.5, "kcal": 400, "protein": 17, "fat": 19, "carbs": 40, "sodium": 790, "sugar": 5, "fried": True},
    {"name": "双层吉士汉堡", "cat": "main", "price": 19.0, "kcal": 440, "protein": 25, "fat": 24, "carbs": 34, "sodium": 980, "sugar": 7, "fried": False},
    {"name": "麦辣鸡腿堡", "cat": "main", "price": 21.0, "kcal": 530, "protein": 24, "fat": 25, "carbs": 51, "sodium": 1240, "sugar": 6, "fried": True},
    {"name": "吉士汉堡包", "cat": "main", "price": 12.5, "kcal": 300, "protein": 15, "fat": 12, "carbs": 33, "sodium": 680, "sugar": 6, "fried": False},
    {"name": "中薯条", "cat": "side", "price": 13.0, "kcal": 330, "protein": 4, "fat": 16, "carbs": 42, "sodium": 260, "sugar": 0, "fried": True},
    {"name": "玉米杯", "cat": "side", "price": 9.0, "kcal": 110, "protein": 3, "fat": 2, "carbs": 20, "sodium": 15, "sugar": 4, "fried": False},
    {"name": "苹果派", "cat": "side", "price": 9.5, "kcal": 230, "protein": 2, "fat": 11, "carbs": 31, "sodium": 170, "sugar": 12, "fried": True},
    {"name": "麦乐鸡5块", "cat": "side", "price": 14.0, "kcal": 220, "protein": 13, "fat": 12, "carbs": 15, "sodium": 540, "sugar": 0, "fried": True},
    {"name": "田园沙拉(不加酱)", "cat": "side", "price": 12.0, "kcal": 60, "protein": 3, "fat": 1, "carbs": 9, "sodium": 60, "sugar": 4, "fried": False},
    {"name": "可口可乐中杯", "cat": "drink", "price": 11.0, "kcal": 147, "protein": 0, "fat": 0, "carbs": 39, "sodium": 10, "sugar": 39, "fried": False},
    {"name": "无糖可乐中杯", "cat": "drink", "price": 11.0, "kcal": 1, "protein": 0, "fat": 0, "carbs": 0, "sodium": 15, "sugar": 0, "fried": False},
    {"name": "纯牛奶", "cat": "drink", "price": 12.0, "kcal": 130, "protein": 6, "fat": 5, "carbs": 15, "sodium": 90, "sugar": 13, "fried": False},
    {"name": "美式咖啡", "cat": "drink", "price": 13.0, "kcal": 10, "protein": 0, "fat": 0, "carbs": 2, "sodium": 5, "sugar": 0, "fried": False},
    {"name": "锡兰红茶(无糖)", "cat": "drink", "price": 12.0, "kcal": 5, "protein": 0, "fat": 0, "carbs": 1, "sodium": 5, "sugar": 0, "fried": False},
]

PROFILES = {
    "sodium": {"label": "控钠(血压关注)", "sodium_max": 800, "sugar_max": None, "fat_max": None, "kcal_max": 900, "avoid_fried": False},
    "sugar": {"label": "控糖(血糖关注)", "sodium_max": None, "sugar_max": 25, "fat_max": None, "kcal_max": 900, "avoid_fried": False},
    "fat": {"label": "控脂(血脂关注)", "sodium_max": None, "sugar_max": None, "fat_max": 22, "kcal_max": 800, "avoid_fried": True},
    "all": {"label": "三高综合", "sodium_max": 800, "sugar_max": 25, "fat_max": 25, "kcal_max": 850, "avoid_fried": False},
}


def load_items():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, encoding="utf-8") as f:
            data = json.load(f)
        return data["items"], False
    return SAMPLE_ITEMS, True


def total(combo):
    keys = ["price", "kcal", "protein", "fat", "carbs", "sodium", "sugar"]
    return {k: round(sum(i[k] for i in combo), 1) for k in keys}


def passes(t, p, budget):
    if budget is not None and t["price"] > budget:
        return False
    if p["sodium_max"] is not None and t["sodium"] > p["sodium_max"]:
        return False
    if p["sugar_max"] is not None and t["sugar"] > p["sugar_max"]:
        return False
    if p["fat_max"] is not None and t["fat"] > p["fat_max"]:
        return False
    if p["kcal_max"] is not None and t["kcal"] > p["kcal_max"]:
        return False
    return True


def solve(profile_key="all", budget=45.0, topn=3):
    items, demo = load_items()
    p = PROFILES[profile_key]
    mains = [i for i in items if i["cat"] == "main"]
    sides = [i for i in items if i["cat"] == "side"]
    drinks = [i for i in items if i["cat"] == "drink"]
    results = []
    relaxed = []
    for combo in itertools.product(mains, sides, drinks):
        if p["avoid_fried"] and any(i["fried"] for i in combo):
            continue
        t = total(combo)
        entry = {"items": [i["name"] for i in combo], "totals": t}
        if passes(t, p, budget):
            results.append(entry)
        elif passes(t, p, None):
            relaxed.append(entry)
    # 排序: 先钠升序 (三高人群第一约束), 再蛋白降序, 再价格升序
    results.sort(key=lambda e: (e["totals"]["sodium"], -e["totals"]["protein"], e["totals"]["price"]))
    out = {"profile": p["label"], "budget": budget, "demo_sample": demo, "results": results[:topn]}
    if not results and relaxed:
        relaxed.sort(key=lambda e: (e["totals"]["sodium"], e["totals"]["price"]))
        out["results"] = []
        out["over_budget_only"] = relaxed[:topn]
    return out


def swap(name):
    """给一个想吃的单品找同类更低钠替代, 返回量化差值。"""
    items, demo = load_items()
    target = next((i for i in items if i["name"] == name), None)
    if target is None:
        return {"error": f"未找到单品: {name}", "demo_sample": demo}
    alts = [i for i in items if i["cat"] == target["cat"] and i["name"] != name and i["sodium"] < target["sodium"]]
    alts.sort(key=lambda i: i["sodium"])
    suggestions = []
    for a in alts[:3]:
        d = target["sodium"] - a["sodium"]
        suggestions.append({
            "name": a["name"], "sodium": a["sodium"], "sodium_saved_mg": d,
            "sodium_saved_pct": round(d / target["sodium"] * 100, 1) if target["sodium"] else 0,
            "kcal": a["kcal"], "price": a["price"],
        })
    return {"item": name, "sodium": target["sodium"], "demo_sample": demo, "suggestions": suggestions}


def fmt(out):
    lines = []
    if out.get("demo_sample"):
        lines.append("⚠️ 当前为示例数据演示 (实测请用 MCP list-nutrition-foods 回填 data/nutrition.json)")
    lines.append(f"画像: {out['profile']} | 预算: ¥{out['budget']}")
    res = out.get("results") or []
    if res:
        for idx, e in enumerate(res, 1):
            t = e["totals"]
            lines.append(
                f"{idx}. {' + '.join(e['items'])} | ¥{t['price']} | {t['kcal']}kcal | "
                f"钠 {t['sodium']}mg | 糖 {t['sugar']}g | 脂肪 {t['fat']}g | 蛋白 {t['protein']}g"
            )
    elif out.get("over_budget_only"):
        lines.append("预算内无满足约束的组合; 以下是满足营养约束但超预算的方案:")
        for idx, e in enumerate(out["over_budget_only"], 1):
            t = e["totals"]
            lines.append(f"{idx}. {' + '.join(e['items'])} | ¥{t['price']} | 钠 {t['sodium']}mg")
    else:
        lines.append("无满足约束的组合, 建议放宽预算或约束后重试。")
    lines.append("注: 本输出只做营养数据核算, 不构成医疗或营养专业建议; 餐品数据以麦当劳官方实时结果为准。")
    return "\n".join(lines)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default="all", choices=list(PROFILES.keys()))
    ap.add_argument("--budget", type=float, default=45.0)
    ap.add_argument("--swap", default=None, help="想吃的单品名, 输出低钠替代建议")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    if args.swap:
        r = swap(args.swap)
        print(json.dumps(r, ensure_ascii=False, indent=2) if args.json else r)
    else:
        r = solve(args.profile, args.budget)
        print(json.dumps(r, ensure_ascii=False, indent=2) if args.json else fmt(r))
