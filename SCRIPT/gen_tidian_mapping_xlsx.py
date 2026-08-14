# -*- coding: utf-8 -*-
# 生成「体检点数据类型来源对应」Excel（放 DATA/analysis/，供查阅）。
import os

import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "DATA", "analysis", "体检点数据类型来源对应_2026-08-14.xlsx")

HDR_FILL = PatternFill("solid", fgColor="404040")
HDR_FONT = Font(bold=True, color="FFFFFF")
EXCL_FILL = PatternFill("solid", fgColor="F2F2F2")   # 附加/覆盖率 排除行浅灰
SUB_FILL = PatternFill("solid", fgColor="D9E2F3")    # 小计行浅蓝
THIN = Side(style="thin", color="BFBFBF")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)
LEFT = Alignment(horizontal="left", vertical="center", wrap_text=True)


def _write(ws, r, vals, fill=None, align=None):
    for c, v in enumerate(vals, 1):
        cell = ws.cell(r, c, v)
        cell.border = BORDER
        cell.alignment = align or LEFT
        if fill:
            cell.fill = fill


def _header(ws, r, vals):
    for c, v in enumerate(vals, 1):
        cell = ws.cell(r, c, v)
        cell.fill = HDR_FILL
        cell.font = HDR_FONT
        cell.border = BORDER
        cell.alignment = CENTER


def build_detail(ws):
    _header(ws, 1, ["源头维度", "源头子类", "源头图斑类型", "图斑数", "性质", "提取去向（最终8类）", "方面", "备注"])
    rows = [
        ("住房", "安全耐久", "结构隐患住宅", 42, "负面", "安全·住房", "安全韧性", ""),
        ("住房", "安全耐久", "燃气隐患住宅", 6, "负面", "安全·市政管网", "安全韧性", "燃气归管网"),
        ("住房", "安全耐久", "楼道隐患住宅", 240, "负面", "安全·安全消防", "安全韧性", ""),
        ("住房", "安全耐久", "围护隐患住宅", 454, "负面", "安全·住房", "安全韧性", ""),
        ("住房", "功能完备", "非成套住宅", 31, "负面", "民生·住房", "民生基础", ""),
        ("住房", "功能完备", "管线管道破损住宅", 186, "负面", "安全·市政管网", "安全韧性", "管线归管网"),
        ("住房", "功能完备", "适老化改造住宅", 39, "负面", "民生·住房", "民生基础", ""),
        ("住房", "绿色智能", "数字化改造住宅", 25, "附加·排除", "—（不参与）", "其他", "绿色智能=附加发展类"),
        ("小区", "设施完善", "养老未达标小区", 2, "负面", "民生·公服设施", "民生基础", ""),
        ("小区", "设施完善", "婴幼儿照护未达标", 34, "负面", "民生·公服设施", "民生基础", ""),
        ("小区", "设施完善", "幼儿园未达标", 11, "负面", "民生·公服设施", "民生基础", ""),
        ("小区", "设施完善", "小学学位缺口", 31, "负面", "民生·公服设施", "民生基础", ""),
        ("小区", "设施完善", "停车泊位缺口", 140, "负面", "民生·停车设施", "民生基础", ""),
        ("小区", "设施完善", "充电桩缺口", 84, "负面", "民生·停车设施", "民生基础", ""),
        ("小区", "设施完善", "电动车充电未配建", 50, "负面", "民生·停车设施", "民生基础", ""),
        ("小区", "环境宜居", "步行道不达标", 24, "负面", "民生·交通设施", "民生基础", ""),
        ("小区", "环境宜居", "公共活动场地未达标", 27, "负面", "民生·公服设施", "民生基础", ""),
        ("小区", "管理健全", "未实施物业小区", 273, "负面", "民生·物业街面", "民生基础", ""),
        ("小区", "管理健全", "智慧化改造小区", 31, "附加·排除", "—（不参与）", "其他", "智慧化=附加发展类"),
        ("街区", "功能完善", "中学覆盖率", 535, "覆盖率·排除", "—（不参与）", "—", "覆盖率=面积指标"),
        ("街区", "功能完善", "公园覆盖率", 515, "覆盖率·排除", "—（不参与）", "—", "覆盖率=面积指标"),
        ("街区", "功能完善", "菜市场覆盖率", 422, "覆盖率·排除", "—（不参与）", "—", "覆盖率=面积指标"),
        ("街区", "功能完善", "多功能运动场地未达标", 6, "负面", "民生·公服设施", "民生基础", ""),
        ("街区", "整洁有序", "乱停乱放车辆道路", 5, "负面", "民生·物业街面", "民生基础", "线转点"),
    ]
    r = 2
    for row in rows:
        excl = "排除" in row[4]
        _write(ws, r, list(row), fill=EXCL_FILL if excl else None)
        r += 1
    widths = [8, 10, 22, 8, 12, 18, 10, 20]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = w


def build_summary(ws):
    _header(ws, 1, ["最终社区点（8类）", "方面", "源图斑构成", "源图斑数", "提取点数据", "社区矩阵", "差异", "差异说明"])
    rows = [
        ("安全·住房", "安全韧性", "结构隐患42 + 围护隐患454", 496, 496, 496, 0, "零丢失"),
        ("安全·安全消防", "安全韧性", "楼道隐患240", 240, 240, 240, 0, "零丢失"),
        ("安全·市政管网", "安全韧性", "管线破损186 + 燃气隐患6", 192, 192, 192, 0, "零丢失"),
        ("安全小计", "—", "—", 928, 928, 928, 0, "零丢失"),
        ("民生·公服设施", "民生基础", "养老2+婴幼儿34+幼儿园11+学位31+活动场地27+运动场地6", 111, 111, 109, 2, "2点落缝范围外"),
        ("民生·住房", "民生基础", "非成套31 + 适老化39", 70, 70, 70, 0, "零丢失"),
        ("民生·停车设施", "民生基础", "泊位140+充电桩84+电动车50", 274, 274, 274, 0, "零丢失"),
        ("民生·交通设施", "民生基础", "不达标步行道24", 24, 24, 24, 0, "零丢失"),
        ("民生·物业街面", "民生基础", "未物业273 + 乱停乱放5", 278, 278, 278, 0, "零丢失"),
        ("民生小计", "—", "—", 757, 757, 755, 2, "2点落缝范围外"),
    ]
    r = 2
    for row in rows:
        subtotal = "小计" in str(row[0])
        _write(ws, r, list(row), fill=SUB_FILL if subtotal else None)
        r += 1
    widths = [18, 10, 42, 9, 10, 10, 8, 18]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = w


def main():
    wb = openpyxl.Workbook()
    ws1 = wb.active
    ws1.title = "类型来源对应明细"
    build_detail(ws1)
    ws2 = wb.create_sheet("汇总对照")
    build_summary(ws2)
    wb.save(OUT)
    print("[OK]", os.path.basename(OUT))


if __name__ == "__main__":
    main()
