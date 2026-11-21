"""W10D03：虚构三日均线策略，仅使用 Python 标准库。

运行：python -X utf8 -B -m src.moving_average
只在内存中记账，不读行情或账户、不发送订单；导入无执行副作用。
规则、字段、运行版本及手算对照见 docs/lessons/week-10.md。
"""

from math import isfinite


def _number(value, name, positive=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name}必须是整数或浮点数")
    if not isfinite(value) or value < 0 or (positive and value == 0):
        raise ValueError(f"{name}必须是有限的{'正数' if positive else '非负数'}")


def sma_ledger(initial_cash, previous_closes, days):
    """返回按交易日排列的教学账本，不修改输入。

    initial_cash：起点可用现金（美元），初始持仓为0、没有待成交订单。
    previous_closes：起点之前连续交易日的0至2个收盘价，只用于均线，
        不回放此前交易；输入者负责确保它们当时已经可知。
    days：按连续交易日排列的字典列表，必须包含：
        day：递增且连续的正整数交易日序号，不是真实日历日期；
        open：当天开盘成交/估值价，美元/份，正数；
        close：当天收盘价，美元/份，正数。仅末行可显式设为None，
            表示观察在该日开盘后结束，没有收盘观测，不生成新信号。

    固定三日窗口；历史不足三个收盘价则保持空仓、等待。
    收盘价>三日均线时目标1份，否则0份；下一开盘按差额全部成交。
    资金不足则报错停止，不借款、不部分成交或静默改写目标。
    无费用、税费、价差滑点、分红、拆股、现金利息和外部资金流。
    成交时更新现金，不另拆结算状态。浮点数仅用于教学，展示时舍入。
    输出每个完整交易日的收盘行；可选末行是开盘行，phase标明时点。
    trade是当天开盘实际交易份数（买正卖负），target是当天收盘新目标；
    最后一个收盘新目标保留在结果中，不虚构之后的成交或强制清仓。
    不自动报告收益率，避免把接续现金当成整个账户最初投入。
    """
    _number(initial_cash, "initial_cash")
    history = list(previous_closes)
    if len(history) > 2:
        raise ValueError("previous_closes只需起点前的0至2个连续收盘价")
    for price in history:
        _number(price, "previous_close", positive=True)
    for index, day in enumerate(days):
        number = day["day"]
        if isinstance(number, bool) or not isinstance(number, int) or number < 1:
            raise ValueError("day必须是正整数交易日序号")
        if index and number != days[index - 1]["day"] + 1:
            raise ValueError("交易日序号必须连续递增；不排序或填补缺行")
        _number(day["open"], "open", positive=True)
        if day["close"] is None:
            if index != len(days) - 1:
                raise ValueError("只有最后一天可以明确在开盘后结束")
        else:
            _number(day["close"], "close", positive=True)

    cash = initial_cash
    shares = 0
    target = 0
    ledger = []

    for day in days:
        # 开盘：target仍来自上一天收盘；此处没有使用今天的close。
        trade = target - shares
        if trade > 0 and trade * day["open"] > cash:
            raise ValueError(f"第{day['day']}天开盘资金不足，不能借款买入")
        cash = cash - trade * day["open"]
        shares = shares + trade

        average = None
        new_target = None
        phase = "open"
        mark_price = day["open"]
        if day["close"] is not None:
            # 收盘：现在才把今天的close加入窗口，生成下一开盘使用的目标。
            history.append(day["close"])
            history = history[-3:]
            if len(history) == 3:
                average = sum(history) / 3
                target = 1 if day["close"] > average else 0
                new_target = target
            phase = "close"
            mark_price = day["close"]

        total_value = cash + shares * mark_price
        if not all(isfinite(value) for value in (cash, total_value)):
            raise ValueError("账本计算超出有限数值范围")
        if average is not None and not isfinite(average):
            raise ValueError("均线计算超出有限数值范围")
        ledger.append({
            "day": day["day"], "phase": phase, "trade": trade,
            "sma": average, "target": new_target,
            "shares": shares, "cash": cash, "total_value": total_value,
        })
    return ledger


def lesson_days():
    """每次返回独立的W10D02虚构价格列表，避免练习改写原示范输入。"""
    return [
        {"day": 6, "open": 53, "close": 57},
        {"day": 7, "open": 58, "close": 60},
        {"day": 8, "open": 59, "close": 57},
        {"day": 9, "open": 56, "close": None},
    ]


def main():
    # 从第6天开盘旧卖单已完成之后开始，不重复执行此前已记过的卖单。
    rows = sma_ledger(98, [57, 54], lesson_days())
    print("data_kind=fictional_teaching; currency=USD; price_unit=USD/share")
    print("start=day6_after_prior_sale; start_cash=98; original_contribution=100")
    print("day phase trade sma target shares cash total_value")
    for row in rows:
        average = "-" if row["sma"] is None else f"{row['sma']:.2f}"
        target = "-" if row["target"] is None else str(row["target"])
        print(f"{row['day']} {row['phase']} {row['trade']:+d} {average} {target} "
              f"{row['shares']} {row['cash']:.2f} {row['total_value']:.2f}")
    print(f"return_from_original_100={rows[-1]['total_value'] / 100 - 1:.2%}")


if __name__ == "__main__":
    main()
