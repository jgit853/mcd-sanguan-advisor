#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
parse_nutrition.py — 把麦当劳 MCP `list-nutrition-foods` 的原始返回文本解析为 data/nutrition.json

用法: python3 scripts/parse_nutrition.py <原始返回文件> [-o data/nutrition.json]

实测契约 (见 references/api-notes.md):
- 返回不是 JSON, 是裹在 {success,code,data} 信封/ markdown 里的逗号分隔文本表格。
- 列含: 名称、能量、蛋白质、脂肪、碳水化合物、钠 (糖列可能不存在)。
推断规则 (无官方分类字段时使用, 结果仅供求解演示, 核价以 query-meals 为准):
- cat: 名称含 堡/卷/饭 -> main; 含 茶/咖啡/可乐/牛奶/豆浆/汁/雪碧 -> drink; 其余 -> side
- fried: 名称含 炸/薯条/派/麦乐鸡/麦辣/脆 -> true
- 价格不在营养表内: price=0, meta.price_missing=true (advisor 对 price=0 按未知处理)
- 糖列缺失: sugar=0, meta.sugar_missing=true
"""
import argparse
import csv
import io
import json
import os
import re
import sys
from datetime import date

HEADER_KEYS = {
    "name": ["餐品", "名称", "食品", "name", "productname"],
    "kcal": ["能量", "热量", "kcal", "energykcal"],
    "protein": ["蛋白质", "蛋白", "protein"],
    "fat": ["脂肪", "fat"],
    "carbs": ["碳水化合物", "碳水", "carbohydrate"],
    "sodium": ["钠", "sodium"],
    "sugar": ["糖", "sugar"],
}
MAIN_HINT = ["堡", "卷", "饭", "麦满分", "粥"]
DRINK_HINT = ["茶", "咖啡", "可乐", "牛奶", "豆浆", "果汁", "苹果汁", "美汁源", "雪碧", "拿铁", "美式",
              "奶铁", "燕麦奶", "雪冰", "卡布奇诺", "玛奇朵", "阿芙佳朵", "怡泉", "黑巧", "纯悦"]
FRIED_HINT = ["炸", "薯条", "派", "麦乐鸡", "麦辣", "脆"]
# 实测数据(2026-10-21)暴露的例外: 名称无品类关键词, 关键词推断必然误判, 按实物写死
EXACT_CAT = {"巨无霸": "main", "麦香鸡": "main", "麦香鱼": "main",
             "热朱古力": "drink", "麦旋酷阳光橙": "drink"}


def infer_cat(name):
    if name in EXACT_CAT:
        return EXACT_CAT[name]
    if any(h in name for h in DRINK_HINT):
        return "drink"
    if any(h in name for h in MAIN_HINT):
        return "main"
    return "side"


def num(x, default=0.0):
    if x is None:
        return default
    m = re.search(r"-?\d+(?:\.\d+)?", str(x))
    return float(m.group()) if m else default


def extract_rows(text):
    """从原始文本中找出 CSV 表格行: 先剥 markdown 代码块, 再逐行试解析。"""
    text = re.sub(r"```[a-zA-Z]*", "", text)
    lines = [ln.strip() for ln in text.splitlines() if "," in ln]
    header_idx = None
    colmap = {}
    for i, ln in enumerate(lines):
        cells = [c.strip() for c in next(csv.reader(io.StringIO(ln)))]
        found = {}
        for field, keys in HEADER_KEYS.items():
            for j, c in enumerate(cells):
                if any(k.lower() in c.lower() for k in keys):
                    found[field] = j
                    break
        if "name" in found and "kcal" in found and "sodium" in found:
            header_idx, colmap = i, found
            break
    if header_idx is None:
        raise ValueError("未找到营养表表头行 (需同时含 名称/能量/钠 列)")
    return lines, header_idx, colmap


def parse(text, snapshot=None):
    lines, hi, colmap = extract_rows(text)
    items = []
    sugar_missing = "sugar" not in colmap
    for ln in lines[hi + 1:]:
        cells = [c.strip() for c in next(csv.reader(io.StringIO(ln)))]
        if len(cells) <= max(colmap.values()):
            continue
        name = cells[colmap["name"]]
        if not name or name in ("-", "—"):
            continue
        sodium = num(cells[colmap["sodium"]])
        items.append({
            "name": name,
            "cat": infer_cat(name),
            "price": 0,
            "kcal": num(cells[colmap["kcal"]]),
            "protein": num(cells[colmap["protein"]]) if "protein" in colmap else 0,
            "fat": num(cells[colmap["fat"]]) if "fat" in colmap else 0,
            "carbs": num(cells[colmap["carbs"]]) if "carbs" in colmap else 0,
            "sodium": sodium,
            "sugar": num(cells[colmap["sugar"]]) if "sugar" in colmap else 0,
            "fried": any(h in name for h in FRIED_HINT),
        })
    if not items:
        raise ValueError("表头后未解析到任何餐品行")
    return {
        "items": items,
        "source": "mcp list-nutrition-foods",
        "snapshot_date": snapshot or date.today().isoformat(),
        "meta": {"price_missing": True, "sugar_missing": sugar_missing,
                 "note": "cat/fried 为规则推断; 价格需 query-meals/calculate-price 另行核价"},
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("-o", "--output", default=os.path.join(os.path.dirname(__file__), "..", "data", "nutrition.json"))
    args = ap.parse_args()
    with open(args.input, encoding="utf-8") as f:
        data = parse(f.read())
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"parsed {len(data['items'])} items -> {args.output}")


if __name__ == "__main__":
    main()
