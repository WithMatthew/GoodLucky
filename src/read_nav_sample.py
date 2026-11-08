"""W07D02：只读本地SPY净值样本；日期解析、缺值保留和排序。

运行：python -X utf8 -B src/read_nav_sample.py
依赖：Python标准库。无联网、交易或原文件写入。
"""

import csv
from datetime import date
import math
from pathlib import Path


def parse_rows(raw_rows):
    """将本课date/nav/source_row文本转换成新记录，原始输入不变。"""
    rows = []
    for raw in raw_rows:
        day = date.fromisoformat(raw["date"])
        if day.isoformat() != raw["date"]:
            raise ValueError("Expected YYYY-MM-DD")
        nav_text = raw["nav"].strip()
        nav = float(nav_text) if nav_text != "" else None
        if nav is not None and (not math.isfinite(nav) or nav <= 0):
            raise ValueError(f"Invalid NAV on {day}")
        rows.append({"date": day, "nav": nav, "source_row": int(raw["source_row"])})
    return sorted(rows, key=lambda row: row["date"])


def load_rows(path):
    with Path(path).open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != ["date", "nav", "source_row"]:
            raise ValueError("Unexpected CSV columns")
        return parse_rows(list(reader))


def inspect_rows(rows):
    """报告重复日期及缺值；不凭日期间隔推断交易日或自动修复。"""
    by_date = {}
    for row in rows:
        by_date.setdefault(row["date"], []).append(row)
    duplicates = {day.isoformat(): len(group) for day, group in by_date.items() if len(group) > 1}
    missing = [row["date"].isoformat() for row in rows if row["nav"] is None]
    return {"rows": len(rows), "duplicate_dates": duplicates, "missing_nav_dates": missing}


def main():
    path = Path(__file__).resolve().parents[1] / "data/derived/spy_nav_2024-01-02_2024-01-08.csv"
    rows = load_rows(path)
    print("Real SSGA published NAV sample (USD/share); not exchange close")
    for row in rows:
        nav = "missing" if row["nav"] is None else f"{row['nav']:.6f}"
        print(f"{row['date'].isoformat()} nav={nav} source_row={row['source_row']}")
    print(inspect_rows(rows))
    print("Trading-calendar completeness: not checked")


if __name__ == "__main__":
    main()
