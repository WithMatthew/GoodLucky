"""W03D03：虚构全年费用与跟踪差异算账，仅用标准库。

从仓库根目录运行：python -B src/fund_costs.py
全年平均净资产必须由调用者提供；不根据期初金额猜测。
仅适用于无分红、外部资金进出及其他费用的课件模型。
这不是按日计提费用的真实基金估值器，也不用于已扣费的净值数据。
"""

from math import isfinite


def fund_cost_summary(
    initial_assets,
    average_assets,
    gross_profit,
    expense_ratio,
    index_return,
):
    """金额均为同一币种；费率与收益率用小数，例如 0.005 表示 0.5%。

    gross_profit 是扣本项运营费前的全年投资净收益，可为负。
    tracking_difference 是基金收益率减指数收益率的小数差；
    乘 100 后为百分点，例如 -0.005 对应 -0.5 个百分点。
    浮点计算只用于教学，不作为精确结算工具。
    """
    values = (initial_assets, average_assets, gross_profit, expense_ratio, index_return)
    if not all(isfinite(value) for value in values):
        raise ValueError("输入必须为有限数值")
    if initial_assets <= 0 or average_assets < 0 or expense_ratio < 0:
        raise ValueError("期初净资产须为正，平均净资产与费用率不能为负")

    expense = average_assets * expense_ratio
    ending_assets = initial_assets + gross_profit - expense
    fund_return = (ending_assets - initial_assets) / initial_assets
    tracking_difference = fund_return - index_return
    return {
        "expense": expense,
        "ending_assets": ending_assets,
        "fund_return": fund_return,
        "tracking_difference": tracking_difference,
    }


if __name__ == "__main__":
    result = fund_cost_summary(2000, 2000, 160, 0.005, 0.08)
    print(f"expense_usd={result['expense']:.2f}")
    print(f"ending_assets_usd={result['ending_assets']:.2f}")
    print(f"fund_return={result['fund_return']:.2%}")
    print(f"tracking_difference_pp={result['tracking_difference'] * 100:.2f}")
