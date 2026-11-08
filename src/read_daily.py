"""W07D01：读取两行虚构日频数据，复现手算；无行情或账户连接。

运行：python -B src/read_daily.py
Python 3.11.9，只有标准库依赖。
仅演示约定好的两行完整数据；日期解析、排序与质量检查在后续课讲解。
"""

import csv
from pathlib import Path


def read_daily_rows(path):
    """按文件原顺序读取，每行是一个字典，所有字段值暂保留为字符串。"""
    with Path(path).open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def main():
    # 由脚本位置定位仓库，避免依赖本机的绝对路径。
    path = Path(__file__).resolve().parents[1] / "data/synthetic/daily_demo.csv"
    rows = read_daily_rows(path)

    # 本教学文件已按D0、D1顺序排列；列表下标从0开始。
    previous_close = float(rows[0]["close"])
    current_close = float(rows[1]["close"])
    volume = int(rows[1]["volume"])
    shares = 20

    price_return = (current_close - previous_close) / previous_close
    market_value = current_close * shares

    print("Synthetic teaching data only")
    print(f"rows={len(rows)}")
    print(f"raw_close={rows[1]['close']!r}")
    print(f"current_close={current_close:.2f} USD/share, volume={volume} shares")
    print(f"price_return={price_return:.2%}")
    print(f"market_value={market_value:.2f} USD")


if __name__ == "__main__":
    main()
