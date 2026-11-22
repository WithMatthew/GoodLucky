"""读取 MLF-W02 已固定的两个训练月，输出用于读表练习的四列。"""

from datetime import date
from hashlib import file_digest
from pathlib import Path

import pyreadr


PROJECT_ROOT = Path(__file__).resolve().parents[3]
SOURCE_COMMIT = "572b22acd4dbf58ef9a6dadbdcd976344d3af1d4"
SOURCE = PROJECT_ROOT / "data" / "ml-factor" / "raw" / SOURCE_COMMIT / "data_ml.RData"
SHA256 = "eb561b24eeae60de9c3f335f0d388dcd1ed9b04243790aef3ce88d616a44b774"
FIELDS = ["stock_id", "date", "Mom_11M_Usd", "R1M_Usd"]
EXPECTED_KEYS = [(228, date(2013, 10, 31)), (228, date(2013, 11, 30))]


def main() -> None:
    with SOURCE.open("rb") as stream:
        if file_digest(stream, "sha256").hexdigest() != SHA256:
            raise ValueError("作者文件与本课登记的 SHA-256 不符，请核对固定版本。")
        stream.seek(0)
        # 319 是该版本中按标识和观察月核对过的首行偏移，从零起算。
        tables = pyreadr.read_r(stream, use_objects=["data_ml"], row_offset=319, row_limit=2)

    sample = tables["data_ml"].loc[:, FIELDS]
    keys = list(zip(sample["stock_id"], sample["date"]))
    if keys != EXPECTED_KEYS:
        raise ValueError("提取行的股票标识或观察月与课程登记不符。")
    print(sample.to_csv(index=False, lineterminator="\n"), end="")


if __name__ == "__main__":
    main()
