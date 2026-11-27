"""W11D02-B：跨资产数据质量检查与 RF 口径转换（学习者编写）。

只使用 pandas / numpy。三个函数都不修改输入、不填补、不删行——只“发现并报告”。
写完后运行：
    .venv\\Scripts\\python.exe -X utf8 -B -m unittest tests.test_cross_asset_checks -v
"""

import pandas as pd


def ohlc_violations(frame: pd.DataFrame) -> pd.Series:
    """逐行检查 OHLC 价格关系是否自洽。

    输入：含 open/high/low/close 列的 DataFrame（索引为日期）。
    输出：与 frame 同索引的布尔 Series，名为 'ohlc_violation'；
          某行出现以下任一情况即为 True：
          - low  > min(open, close)
          - high < max(open, close)
    """
    open_close_min = frame[["open", "close"]].min(axis=1)
    open_close_max = frame[["open", "close"]].max(axis=1)
    mask = (frame["low"] > open_close_min) | (frame["high"] < open_close_max)

    ret = pd.Series(mask)
    ret = ret.rename("ohlc_violation")
    return ret


def flag_big_moves(adj_close: pd.Series, threshold: float) -> pd.Series:
    """找出单日简单收益率绝对值严格大于 threshold 的交易日。

    输入：复权收盘价 Series（索引为日期）；threshold 为小数，如 0.10 表示 10%。
    输出：只包含被标记日期的收益率 Series（保留正负号），不含 NaN。
    """
    pct_value = adj_close.pct_change()
    valid_pct_value = pct_value.dropna()
    ret = pd.Series(valid_pct_value[valid_pct_value.abs() > threshold])
    return ret


def monthly_to_daily_rf(
    rf_monthly: pd.Series, trading_dates: pd.DatetimeIndex
) -> pd.Series:
    """把月度无风险收益拆成当月每个交易日的日收益。

    输入：
      rf_monthly    —— 索引为 PeriodIndex(freq='M')，值为当月收益（小数/月，如 0.0040）
      trading_dates —— 实际交易日 DatetimeIndex
    规则：若某月有 n 个交易日、月收益为 r_m，则该月每个交易日
          r_d = (1 + r_m) ** (1 / n) - 1，保证当月日收益连乘恰好还原 1 + r_m。
    输出：索引为 trading_dates 的 Series，名为 'rf'。
    若某个交易日所在月份在 rf_monthly 中缺失，抛出 ValueError（不得静默填 0）。
    """
    months = trading_dates.to_period("M")
    if not months.isin(rf_monthly.index).all():
        raise ValueError("部分交易日所在月份在 rf_monthly 中缺失")
    counts = months.value_counts()
    trade_monthly_daily = pd.Series(months).map(counts).to_numpy()
    rf_monthly_for_daily = rf_monthly.reindex(months).to_numpy()
    per_month = (1 + rf_monthly_for_daily) ** (1 / trade_monthly_daily) - 1
    ret = pd.Series(per_month, index=trading_dates, name="rf")
    return ret
