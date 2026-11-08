"""从已下载的SSGA官方工作簿提取固定课堂窗口，不修改原始文件。

运行：python -X utf8 -B src/prepare_spy_nav_sample.py
只适配本课已核验的navhist工作表布局；仅依赖Python标准库。
此为备课辅助程序，课堂重点在read_nav_sample.py，而非XLSX内部格式。
"""

import csv
from datetime import date, datetime, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import platform
import re
from xml.etree import ElementTree as ET
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/ssga/spy_nav_2026-11-08.xlsx"
OUTPUT = ROOT / "data/derived/spy_nav_2024-01-02_2024-01-08.csv"
SOURCE_URL = "https://www.ssga.com/library-content/products/fund-data/etfs/us/navhist-us-en-spy.xlsx"
START, END = date(2024, 1, 2), date(2024, 1, 8)
NS = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
MONTHS = {name: i for i, name in enumerate(
    "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split(), 1)}


def extract_sample(path):
    """读取已核验的文字日期及NAV，不把净值改名为close或填补数据。"""
    with ZipFile(path) as archive:
        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        sheets = workbook.find("s:sheets", NS)
        if len(sheets) != 1 or sheets[0].get("name") != "navhist":
            raise ValueError("Unexpected workbook layout")
        strings = ["".join(item.itertext()) for item in
                   ET.fromstring(archive.read("xl/sharedStrings.xml"))]
        sheet = ET.fromstring(archive.read("xl/worksheets/sheet1.xml"))

    def value(cell):
        if cell.find("s:f", NS) is not None:
            raise ValueError("Unexpected formula in source data")
        raw = cell.findtext("s:v", "", NS)
        return strings[int(raw)] if cell.get("t") == "s" else raw

    source_rows = sheet.findall("s:sheetData/s:row", NS)
    header = {c.get("r"): value(c) for r in source_rows
              if int(r.get("r")) <= 4 for c in r}
    if (header.get("B2"), header.get("A4"), header.get("B4")) != ("SPY", "Date", "NAV"):
        raise ValueError("Source ticker/columns changed")
    selected = []
    for row in source_rows:
        number = int(row.get("r"))
        if number <= 4:
            continue
        cells = {c.get("r"): c for c in row}
        day_cell = cells.get(f"A{number}")
        if day_cell is None:
            continue
        day_text = value(day_cell)
        if not day_text:
            continue
        # 已核验的文件在行情表后附品牌更名说明；此处结束数据区。
        if day_text.startswith("State Street Global Advisors (SSGA) is now State Street Investment Management."):
            break
        match = re.fullmatch(r"(\d{2})-([A-Za-z]{3})-(\d{4})", day_text)
        if match is None or match[2] not in MONTHS:
            raise ValueError(f"Unexpected date at A{number}: {day_text}")
        day = date(int(match[3]), MONTHS[match[2]], int(match[1]))
        if START <= day <= END:
            nav_cell = cells.get(f"B{number}")
            nav = value(nav_cell) if nav_cell is not None else ""
            if nav and (not Decimal(nav).is_finite() or Decimal(nav) <= 0):
                raise ValueError(f"Invalid NAV at B{number}")
            selected.append({"date": day.isoformat(), "nav": nav, "source_row": number})
    if not selected:
        raise ValueError("No records within the fixed teaching window")
    return selected


def main():
    raw_hash = hashlib.sha256(RAW.read_bytes()).hexdigest()
    sample = extract_sample(RAW)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    # 保留来源中的倒序，供课堂程序再按日期排序；不自动去重或补值。
    with OUTPUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["date", "nav", "source_row"])
        writer.writeheader()
        writer.writerows(sample)
    metadata = {
        "source_url": SOURCE_URL,
        "raw_file": RAW.relative_to(ROOT).as_posix(),
        "raw_sha256": raw_hash,
        "raw_file_mtime_utc_after_download": datetime.fromtimestamp(
            RAW.stat().st_mtime, timezone.utc).isoformat(),
        "prepared_at_utc": datetime.now(timezone.utc).isoformat(),
        "python_version": platform.python_version(),
        "ticker": "SPY", "sheet": "navhist", "source_columns": "A=Date,B=NAV",
        "sample_start": START.isoformat(), "sample_end": END.isoformat(),
        "sample_file": OUTPUT.relative_to(ROOT).as_posix(),
        "sample_sha256": hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),
        "row_count": len(sample), "source_rows": [r["source_row"] for r in sample],
        "price_basis": "Published NAV per share in USD; not exchange close or total return",
        "treatment": "Normalize dates only; preserve source NAV and order; no filling/deleting",
    }
    OUTPUT.with_suffix(".metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if hashlib.sha256(RAW.read_bytes()).hexdigest() != raw_hash:
        raise RuntimeError("Raw source changed")
    print(json.dumps(metadata, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
