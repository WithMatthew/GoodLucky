"""W05D03：用虚构账面金额核对资产、负债与股东权益。

从仓库根目录运行：python -B src/balance_sheet.py
本课输入使用同一时点的整数美元，资产仅包括现金和应收账款。
reported_equity 是独立提供的已填权益，不由本函数反推。
差额为零仅说明等式成立，不能证明账目真实、完整或分类正确。
"""


def balance_check(cash, receivables, liabilities, reported_equity):
    """返回总资产 assets 和等式左边减右边的差额 gap，单位同输入。"""
    assets = cash + receivables
    gap = assets - liabilities - reported_equity
    return {"assets": assets, "gap": gap}


if __name__ == "__main__":
    result = balance_check(
        cash=6000,
        receivables=1000,
        liabilities=2000,
        reported_equity=5000,
    )
    print(f"assets_usd={result['assets']}")
    print(f"gap_usd={result['gap']}")
