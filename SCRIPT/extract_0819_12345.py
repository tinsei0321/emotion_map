# -*- coding: utf-8 -*-
"""提取 0819 专项规划 PDF 页33 的 12345 热线数据（表格+图片）·主观数据落图锚点。

来源：D:\OneDrive\2026\15_城市更新专项规划研究\2 宜昌市城市更新\宜昌市中心城区城市更新专项规划_阶段性成果\宜昌市中心城区城市更新专项规划0819.pdf
位置：页 33「二、重点片区选择」→「根据 12345 热线数据分析」
产出：docs/urban-renewal-plan/_raw/0819/p33_12345分布图_*.png（图片·不入 git）
用法：py SCRIPT/extract_0819_12345.py
"""
import os
import sys

import pymupdf

sys.stdout.reconfigure(encoding='utf-8')

PDF = r"D:/OneDrive/2026/15_城市更新专项规划研究/2 宜昌市城市更新/宜昌市中心城区城市更新专项规划_阶段性成果/宜昌市中心城区城市更新专项规划0819.pdf"
OUT = "docs/urban-renewal-plan/_raw/0819"
PAGE = 33


def main():
    os.makedirs(OUT, exist_ok=True)
    doc = pymupdf.open(PDF)
    page = doc[PAGE]
    # 表格
    print("=== 页 33 文本 ===")
    print(page.get_text())
    try:
        tabs = page.find_tables()
        for t in tabs.tables:
            for row in t.extract():
                print(" | ".join(str(c).replace('\n', ' ') if c else '' for c in row))
    except Exception as e:
        print(f"表格提取失败: {e}")
    # 图片（12345 分布图）
    for i, img in enumerate(page.get_images(full=True)):
        pix = pymupdf.Pixmap(doc, img[0])
        fn = os.path.join(OUT, f"p{PAGE}_12345分布图_{i}.png")
        pix.save(fn)
        print(f"[OK] {fn} ({pix.width}x{pix.height})")


if __name__ == '__main__':
    main()
