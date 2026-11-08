"""W06D03：用虚构数据核对一次再平衡，仅使用 Python 标准库。

从仓库根目录运行：python -B src/rebalance.py
金额为美元，价格为美元/份，目标权重用小数；现金权重为剩余比例。
模型无费用、税费、外部资金流、分红利息、价差滑点或汇率变化，
无杠杆、负债和卖空；价格固定，核算所有交易完成并结算后的结果。
输出理想目标份额，可能含小数；本课案例均为整数份。
不建模真实交易单位和资金可用权限，不连接行情、账户或下单接口。
"""

from math import isfinite


def rebalance(
    stock_shares, bond_shares, stock_price, bond_price,
    cash, stock_weight, bond_weight,
):
    """返回交易金额、交易后份额、现金、总价值与权重。

    stock_trade 和 bond_trade：正数表示买入支出，负数表示卖出回款。
    输入权重由题目给定，函数不会预测行情或判断最优配置。
    """
    values = (
        stock_shares, bond_shares, stock_price, bond_price,
        cash, stock_weight, bond_weight,
    )
    if not all(isfinite(value) for value in values):
        raise ValueError("输入必须为有限数值")
    if min(stock_shares, bond_shares, cash) < 0:
        raise ValueError("份额和现金不能为负")
    if stock_price <= 0 or bond_price <= 0:
        raise ValueError("每份价格必须为正")
    if min(stock_weight, bond_weight) < 0 or stock_weight + bond_weight > 1:
        raise ValueError("股票与债券目标权重须非负，合计不能超过1")

    stock_value = stock_shares * stock_price
    bond_value = bond_shares * bond_price
    total_before = stock_value + bond_value + cash
    if total_before <= 0:
        raise ValueError("账户总价值必须为正才能计算权重")

    stock_trade = total_before * stock_weight - stock_value
    bond_trade = total_before * bond_weight - bond_value
    stock_shares_after = stock_shares + stock_trade / stock_price
    bond_shares_after = bond_shares + bond_trade / bond_price
    cash_after = cash - stock_trade - bond_trade

    stock_value_after = stock_shares_after * stock_price
    bond_value_after = bond_shares_after * bond_price
    total_after = stock_value_after + bond_value_after + cash_after
    weights_after = (
        stock_value_after / total_after,
        bond_value_after / total_after,
        cash_after / total_after,
    )
    return {
        "total_before": total_before,
        "stock_trade": stock_trade,
        "bond_trade": bond_trade,
        "stock_shares_after": stock_shares_after,
        "bond_shares_after": bond_shares_after,
        "cash_after": cash_after,
        "total_after": total_after,
        "weights_after": weights_after,
    }


if __name__ == "__main__":
    result = rebalance(
        stock_shares=80, bond_shares=40,
        stock_price=100, bond_price=100,
        cash=3000, stock_weight=0.50, bond_weight=0.40,
    )
    for key, value in result.items():
        if key == "weights_after":
            print(f"{key}=" + ", ".join(f"{weight:.2%}" for weight in value))
        else:
            print(f"{key}={value:.2f}")
