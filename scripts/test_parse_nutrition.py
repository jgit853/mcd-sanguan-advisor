#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""parse_nutrition.py 自测: 仿真 MCP 返回 (信封+markdown+逗号表格)"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import parse_nutrition as pn

RAW_WITH_SUGAR = """
{"success": true, "code": 200, "data": "餐品营养信息如下"}
```text
餐品名称,能量(kcal),蛋白质(g),脂肪(g),碳水化合物(g),钠(mg),糖(g)
板烧鸡腿堡,400,26,13,42,890,7
中薯条,330,4,16,42,260,0
无糖可乐中杯,1,0,0,0,15,0
玉米杯,110,3,2,20,15,4
麦辣鸡腿堡,530,24,25,51,1240,6
锡兰红茶,5,0,0,1,5,0
```
以上数据仅供参考。
"""

RAW_NO_SUGAR = """
餐品名称,能量,蛋白质,脂肪,碳水化合物,钠
吉士汉堡包,300,15,12,33,680
苹果派,230,2,11,31,170
纯牛奶,130,6,5,15,90
"""


def test_parse_with_sugar():
    d = pn.parse(RAW_WITH_SUGAR, snapshot="2026-10-19")
    assert len(d["items"]) == 6, d["items"]
    assert d["meta"]["sugar_missing"] is False
    assert d["meta"]["price_missing"] is True
    assert d["snapshot_date"] == "2026-10-19"


def test_values_and_types():
    d = pn.parse(RAW_WITH_SUGAR)
    by = {i["name"]: i for i in d["items"]}
    assert by["板烧鸡腿堡"]["sodium"] == 890 and by["板烧鸡腿堡"]["cat"] == "main"
    assert by["中薯条"]["fried"] is True and by["中薯条"]["cat"] == "side"
    assert by["无糖可乐中杯"]["cat"] == "drink" and by["无糖可乐中杯"]["sugar"] == 0
    assert by["麦辣鸡腿堡"]["fried"] is True
    assert by["锡兰红茶"]["cat"] == "drink"


def test_no_sugar_column():
    d = pn.parse(RAW_NO_SUGAR)
    assert d["meta"]["sugar_missing"] is True
    assert all(i["sugar"] == 0 for i in d["items"])
    assert len(d["items"]) == 3


def test_bad_input_raises():
    try:
        pn.parse("这是一段没有表格的文本,只有逗号")
        raise AssertionError("should have raised")
    except ValueError:
        pass


def test_output_shape_for_advisor():
    d = pn.parse(RAW_WITH_SUGAR)
    for i in d["items"]:
        for k in ["name", "cat", "price", "kcal", "protein", "fat", "carbs", "sodium", "sugar", "fried"]:
            assert k in i, (i, k)


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"PASS {fn.__name__}")
    print(f"All {len(fns)} tests passed.")
