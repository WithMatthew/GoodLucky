"""W09D03-A：虚构买入持有账本；仅使用Python标准库。

运行：python -X utf8 -B -m src.buy_and_hold
不读取文件、行情或账户；不发订单；导入模块无执行副作用。
实际验证版本与教学假设见docs/lessons/week-09.md。
"""

from math import isfinite


def _number(value, name, minimum=0, positive=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name}必须是整数或浮点数")
    if not isfinite(value) or value < minimum or (positive and value == 0):
        raise ValueError(f"{name}超出本教学模型允许范围")


def _snapshot(step, price, shares, cash, dividend_cash, interest, initial_cash):
    market_value = shares * price
    total_value = market_value + cash
    normalized_value = total_value / initial_cash
    if not all(isfinite(v) for v in (cash, market_value, total_value, normalized_value)):
        raise ValueError("账本计算超出有限数值范围")
    return {
        "step": step,
        "price": price,
        "shares": shares,
        "dividend_cash": dividend_cash,
        "interest": interest,
        "cash": cash,
        "market_value": market_value,
        "total_value": total_value,
        "normalized_value": normalized_value,
        "cumulative_return": normalized_value - 1,
    }


def buy_and_hold_ledger(initial_cash, shares, entry_price, periods):
    """返回T0建仓后及每个后续观察时点的账本列表；不修改输入。

    initial_cash：建仓前美元现金，有限正数。
    shares：预定买入的整数份数，非负；建仓成本不得超过现金。
    entry_price：T0题设给定的假设成交价，美元/份，有限正数。
    periods：按时间先后排列的字典，每个字典必须含：
        price：本期末市场估值价（美元/份，正数），不是复权价。
        dividend_per_share：本期末到账的每份分红（美元/份，非负）。
        cash_rate：本期对期初现金支付的收益率，小数，至少为-1。

    明确约定：输入价格和收入均为虚构教学值；T0后份数固定，不再投资；
    分红与利息在各期期末到账，当期新分红不赚取该期利息。
    各观察时点无未到账应收款；分红资格由输入者预先核对。
    无外部资金流、费用、税费、借款、拆股、汇率变化或中途交易。
    这不是逐日处理真实除息/付款日期的引擎，也不是券商现金计息规则。
    不填补缺失或推断日期，列表顺序由输入者保证；空列表仅返回T0。
    浮点数仅在展示时舍入，不作为精确货币结算工具。
    """
    _number(initial_cash, "initial_cash", positive=True)
    _number(entry_price, "entry_price", positive=True)
    if isinstance(shares, bool) or not isinstance(shares, int) or shares < 0:
        raise ValueError("shares必须是非负整数")
    if shares * entry_price > initial_cash:
        raise ValueError("建仓金额超过可用现金；本例不允许借款")

    cash = initial_cash - shares * entry_price
    ledger = [_snapshot(0, entry_price, shares, cash, 0, 0, initial_cash)]
    for step, period in enumerate(periods, start=1):
        _number(period["price"], "price", positive=True)
        _number(period["dividend_per_share"], "dividend_per_share")
        _number(period["cash_rate"], "cash_rate", minimum=-1)

        # 此时cash仍是期初余额；本期期末才到账的分红不计入本期计息基数。
        interest = cash * period["cash_rate"]
        dividend_cash = shares * period["dividend_per_share"]
        cash = cash + interest + dividend_cash
        ledger.append(_snapshot(
            step, period["price"], shares, cash, dividend_cash, interest, initial_cash
        ))
    return ledger


def main():
    # 复用用户已通过的W09D02-A；不在此运行尚待用户预测的练习变式。
    periods = [
        {"price": 49, "dividend_per_share": 1, "cash_rate": 0},
        {"price": 52, "dividend_per_share": 0, "cash_rate": 0.01},
    ]
    ledger = buy_and_hold_ledger(1000, 10, 50, periods)
    print("data_kind=fictional_teaching; period=unspecified; currency=USD")
    print("fixed_shares=true; dividend_reinvestment=false; cash_rate=per_period")
    print("step shares dividend interest cash market_value total_value normalized_value cumulative_return")
    for row in ledger:
        print(f"T{row['step']} {row['shares']} {row['dividend_cash']:.2f} "
              f"{row['interest']:.2f} {row['cash']:.2f} {row['market_value']:.2f} "
              f"{row['total_value']:.2f} {row['normalized_value']:.4f} "
              f"{row['cumulative_return']:.2%}")


if __name__ == "__main__":
    main()
