# -*- coding: utf-8 -*-
"""体检点全覆盖三图层整合进 Range 预设库（2026-08-18·用户指令）。

三图层（源 = DATA/analysis/77项量化/·08-17 扩域全覆盖口径·page7 客观线源）：
  1) 两大类合并  checkup_qty_合并_全覆盖.geojson     2296 点（民生基础需求 946 + 安全韧性底线 1350）
  2) 安全韧性    checkup_qty_安全_合并_全覆盖.geojson 1350 点（board=安全韧性底线）
  3) 民生基础    checkup_qty_民生_合并_全覆盖.geojson  946 点（board=民生基础需求）
产出（幂等可复跑）：
  1) DATA/boundaries/presets/checkup_qty_{合并|安全_合并|民生_合并}.geojson（沿既有量化预设命名·去全覆盖后缀）
  2) presets manifest 注册 qty_合并 / qty_安全_合并 / qty_民生_合并（体检控件对象组·插在按类 8 预设块首）
对账断言：点数 2296/1350/946 锁定 + board 纯度（合并=双 board·分项=单 board）——口径漂移即报错。
加载路径：Range 库点层走 detectColorMode → needsAnalysis 灰点参考层（grid/zonal 聚合数据源·同既有 8 量化预设）。
"""
import json
import os
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(ROOT, "DATA", "analysis", "77项量化")
PRESET_DIR = os.path.join(ROOT, "DATA", "boundaries", "presets")
MANIFEST = os.path.join(PRESET_DIR, "manifest.json")

# (源后缀, 预设文件名, id, label, 期望点数, 期望 board 集)
LAYERS = [
    ("合并", "checkup_qty_合并.geojson", "qty_合并",
     "量化-两大类合并·全覆盖（2296点）", 2296, {"安全韧性底线", "民生基础需求"}),
    ("安全_合并", "checkup_qty_安全_合并.geojson", "qty_安全_合并",
     "量化-安全韧性·合并全覆盖（1350点）", 1350, {"安全韧性底线"}),
    ("民生_合并", "checkup_qty_民生_合并.geojson", "qty_民生_合并",
     "量化-民生基础·合并全覆盖（946点）", 946, {"民生基础需求"}),
]

NOTE = ("体检全覆盖点（08-17 扩域口径·page7 客观线源）·zonal/grid 聚合分析源·"
        "与按类 8 量化预设同组·灰点参考层（needsAnalysis）")


def _safe_print(msg):
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode("gbk", "replace").decode("gbk"))


def deploy_files():
    for suffix, fname, _id, _label, _n, _b in LAYERS:
        src = os.path.join(SRC_DIR, f"checkup_qty_{suffix}_全覆盖.geojson")
        dst = os.path.join(PRESET_DIR, fname)
        with open(src, encoding="utf-8") as f:
            d = json.load(f)
        feats = d["features"]
        # 对账断言：点数 + board 纯度（口径锁定·漂移即报错）
        n = len(feats)
        if n != _n:
            raise SystemExit(f"[ERR] {suffix} 点数漂移：期望 {_n} 实际 {n}")
        boards = set((f["properties"] or {}).get("board") for f in feats)
        if boards != _b:
            raise SystemExit(f"[ERR] {suffix} board 纯度漂移：期望 {_b} 实际 {boards}")
        shutil.copyfile(src, dst)
        _safe_print(f"[OK] 部署 {fname}（{n} 点·board={'+'.join(sorted(boards))}）")


def register_manifest():
    with open(MANIFEST, encoding="utf-8") as f:
        data = json.load(f)
    target = None
    for g in data:
        if any(it.get("id") == "checkup_cfg_community_xlwj" for it in g.get("items", [])):
            target = g
            break
    if target is None:
        raise SystemExit("[ERR] 未找到体检控件对象组")

    existing_ids = {it.get("id") for it in target["items"]}
    if all(i in existing_ids for i in ("qty_合并", "qty_安全_合并", "qty_民生_合并")):
        _safe_print("[skip] manifest 三预设均已注册")
        return
    # 插在按类 8 量化预设块首（qty_安全_住房 之前）——聚合层在前、分类层在后
    idx = next((i for i, it in enumerate(target["items"]) if it.get("id") == "qty_安全_住房"),
               len(target["items"]))
    new_items = [
        {"id": _id, "label": _label, "file": fname, "nameField": "指标", "note": NOTE}
        for _suffix, fname, _id, _label, _n, _b in LAYERS
        if _id not in existing_ids
    ]
    target["items"][idx:idx] = new_items
    with open(MANIFEST, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    _safe_print(f"[OK] manifest 注册 {len(new_items)} 项 → 体检控件对象组·量化预设块首")


def main():
    deploy_files()
    register_manifest()


if __name__ == "__main__":
    main()
