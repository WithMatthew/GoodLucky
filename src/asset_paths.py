"""第 2 周第 3 天：合计虚构资产价值与留存现金，不连接行情或账户。

在仓库根目录运行：python src/asset_paths.py
仅使用 Python 标准库，运行环境为 Python 3.11.9。
"""


def total_asset_path(asset_values, cash_incomes):
    """返回按时间排列的每期末总资产列表，单位为元。

    asset_values：各期末资产本身的价值，不含另收的现金。
    cash_incomes：各期新收到的分红或利息，按同一时间顺序排列。

    两个输入均为等长列表，元素约定为有限非负数；本教学函数只检查长度。
    空列表返回空列表。现金初始为零，收入全部留存、不再投资、不计息。
    无外部资金流入流出、税费、汇率变化、持仓变化或到期还本。
    不适用于已经包含这些现金的总资产数据，或本金偿还、现金取出等情景。
    输入可用整数或浮点数；浮点数只在展示时舍入，不作为精确结算工具。
    """
    if len(asset_values) != len(cash_incomes):
        raise ValueError("资产价值与现金收入的期数必须一致")

    cash = 0
    totals = []
    for asset_value, income in zip(asset_values, cash_incomes):
        cash += income
        totals.append(asset_value + cash)
    return totals


if __name__ == "__main__":
    principal = 1000
    # 全部为课件自设数据；第三个方案的资产价值就是原有现金余额。
    scenarios = {
        "A": ([800, 1040], [20, 20]),
        "B": ([980, 1020], [30, 30]),
        "C": ([1000, 1000], [0, 0]),
    }
    for label, (asset_values, cash_incomes) in scenarios.items():
        totals = total_asset_path(asset_values, cash_incomes)
        cumulative_return = (totals[-1] - principal) / principal
        print(f"{label}: totals={totals}, two_year_return={cumulative_return:.2%}")
