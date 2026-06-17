"""
PII guard（闭环补强 Wave3）— 扫描导出的分析结果 CSV，禁止含个人身份信息列。
对应 CLAUDE.md 规则 7：分析结果中禁止包含用户名、用户ID 等个人身份信息。

设计：作为 pytest 而非 edit hook——edit hook 看不到数据产物，而 CSV 是管道输出，
放测试里能自然进 CI + /verify，在导出泄露 PII 时第一时间 fail。
"""
import csv
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "DATA" / "processed"

# 禁止出现在结果 CSV 列名中的 PII 字段（小写匹配）
_FORBIDDEN_COLUMNS = {
    "user", "user_id", "userid", "username", "user_name",
    "uid", "nickname", "nick_name",
    "phone", "mobile", "telephone", "tel",
    "id_card", "idcard", "email", "e_mail",
    "ip", "ip_address",
}


def _find_result_csvs():
    if not PROCESSED_DIR.exists():
        return []
    return sorted(PROCESSED_DIR.rglob("*_result_csv.csv"))


_RESULT_CSVS = _find_result_csvs()


def test_processed_dir_exists_or_skip():
    """DATA/processed 不存在时，PII 扫描无对象——记录但不 fail。"""
    if not PROCESSED_DIR.exists():
        pytest.skip("DATA/processed not present yet (no pipeline output to scan)")
    # 目录存在但无结果 CSV 也算通过（尚未导出）


@pytest.mark.parametrize(
    "csv_path",
    _RESULT_CSVS,
    ids=[str(p.relative_to(PROCESSED_DIR)) for p in _RESULT_CSVS],
)
def test_no_pii_columns(csv_path):
    with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            pytest.skip("empty csv")

    header_lower = [h.strip().lower() for h in header]
    leaked = sorted(set(header_lower) & _FORBIDDEN_COLUMNS)
    assert not leaked, (
        f"PII leak in {csv_path.name}: forbidden columns {leaked}. "
        "CLAUDE.md rule 7 forbids exporting PII columns; drop them in the pipeline."
    )
