# -*- coding: utf-8 -*-
"""把 page7 三类社区面注册进 presets manifest（体检控件对象组末尾）。"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST = os.path.join(ROOT, "DATA", "boundaries", "presets", "manifest.json")

NEW_ITEMS = [
    {
        "id": "page7_dual_high",
        "label": "page7-双高社区（5）",
        "file": "page7_双高社区面.geojson",
        "nameField": "社区",
        "note": "page7 三类社区·双高（体检高+诉求高）5社区·剪裁自130社区面",
    },
    {
        "id": "page7_obj_high",
        "label": "page7-问题指标高社区（8）",
        "file": "page7_问题指标高社区面.geojson",
        "nameField": "社区",
        "note": "page7 三类社区·问题指标高（体检高·诉求未暴露）8社区·剪裁自130社区面",
    },
    {
        "id": "page7_sub_high",
        "label": "page7-诉求呼声高社区（7）",
        "file": "page7_诉求呼声高社区面.geojson",
        "nameField": "社区",
        "note": "page7 三类社区·诉求呼声高（诉求高·体检未印证）7社区·剪裁自130社区面",
    },
]


def main():
    with open(MANIFEST, encoding="utf-8") as f:
        data = json.load(f)

    target = None
    for g in data:
        if any(it.get("id") == "checkup_cfg_community_xlwj" for it in g.get("items", [])):
            target = g
            break
    if target is None:
        raise SystemExit("未找到体检控件对象组")

    existing = {it["id"] for it in target["items"]}
    added = 0
    for it in NEW_ITEMS:
        if it["id"] in existing:
            print(f"[skip] 已存在 {it['id']}")
            continue
        target["items"].append(it)
        added += 1

    with open(MANIFEST, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print(f"[OK] 新增 {added} 项 → 体检控件对象组")


if __name__ == "__main__":
    main()
