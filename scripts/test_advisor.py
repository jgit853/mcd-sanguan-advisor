#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""advisor.py 离线自测 (无需 Token): 约束正确性 + 换餐量化 + 示例数据完整性"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import advisor


def test_profiles_have_results():
    for key in advisor.PROFILES:
        out = advisor.solve(key, budget=60.0)
        assert out["results"], f"profile {key} should have results within ¥60"


def test_sodium_cap_respected():
    out = advisor.solve("sodium", budget=60.0)
    for e in out["results"]:
        assert e["totals"]["sodium"] <= 800, e


def test_sugar_cap_respected():
    out = advisor.solve("sugar", budget=60.0)
    for e in out["results"]:
        assert e["totals"]["sugar"] <= 25, e
        assert "可口可乐中杯" not in e["items"]


def test_fat_profile_avoids_fried():
    items, _ = advisor.load_items()
    fried_names = {i["name"] for i in items if i["fried"]}
    out = advisor.solve("fat", budget=60.0)
    for e in out["results"]:
        assert not fried_names.intersection(e["items"]), e
        assert e["totals"]["fat"] <= 22, e


def test_budget_respected():
    out = advisor.solve("all", budget=35.0)
    for e in out["results"]:
        assert e["totals"]["price"] <= 35.0, e


def test_sorting_sodium_first():
    out = advisor.solve("all", budget=60.0)
    sodiums = [e["totals"]["sodium"] for e in out["results"]]
    assert sodiums == sorted(sodiums), sodiums


def test_swap_quantified():
    # 取当前数据集(示例或真实回填)中钠最高的主食做换餐, 不写死单品名:
    # 示例数据里是麦辣鸡腿堡, 真实数据(2026-10-21)里官方名为麦辣鸡腿汉堡
    items, _ = advisor.load_items()
    target = max((i for i in items if i["cat"] == "main"), key=lambda i: i["sodium"])
    r = advisor.swap(target["name"])
    assert r["suggestions"], "highest-sodium main should have lower-sodium swaps"
    top = r["suggestions"][0]
    assert top["sodium_saved_mg"] > 0 and top["sodium_saved_pct"] > 0
    assert top["sodium"] + top["sodium_saved_mg"] == r["sodium"]


def test_swap_unknown_item():
    r = advisor.swap("不存在的餐品")
    assert "error" in r


def test_sample_data_shape():
    for i in advisor.SAMPLE_ITEMS:
        for k in ["name", "cat", "price", "kcal", "protein", "fat", "carbs", "sodium", "sugar", "fried"]:
            assert k in i, (i, k)
        assert i["cat"] in ("main", "side", "drink")


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"PASS {fn.__name__}")
    print(f"All {len(fns)} tests passed.")
