"""W11D02：用学习者编写的检查函数扫描 cross-asset-dev-v1 开发数据（只读，不写数据文件）。

    python -X utf8 -B -m src.w11d02_run_checks [--snapshot ID] [--threshold 0.10]

只读开发区间（2007-06-01..2024-12-31）；只输出收益率与比值，不输出 adj_close 水平值。
"""

import argparse

import numpy as np
import pandas as pd

from src.cross_asset_checks import flag_big_moves, monthly_to_daily_rf, ohlc_violations
from src.cross_asset_data import load_prices, load_rf_daily_rounded, load_rf_monthly

DEFAULT_SNAPSHOT = '20261127T133633064816Z'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--snapshot', default=DEFAULT_SNAPSHOT)
    parser.add_argument('--threshold', type=float, default=0.10)
    args = parser.parse_args()

    prices = load_prices(args.snapshot)
    dates = prices['SPY'].index
    same = all(frame.index.equals(dates) for frame in prices.values())
    print(f'== 1. 日期对齐：7 只 ETF 日期完全相同 = {same}，共 {len(dates)} 个交易日')

    print('\n== 2. OHLC 违规行数（B1）')
    for symbol, frame in prices.items():
        print(f'  {symbol}: {int(ohlc_violations(frame).sum())}')

    print(f'\n== 3. 单日 |收益| > {args.threshold:.0%} 的日期（B2）')
    for symbol, frame in prices.items():
        moves = flag_big_moves(frame['adj_close'], args.threshold)
        shown = ', '.join(f'{d:%Y-%m-%d} {v:+.1%}' for d, v in moves.items())
        print(f'  {symbol}: {len(moves)} 天  {shown}')

    rf_m = load_rf_monthly(args.snapshot)
    rf_d = monthly_to_daily_rf(rf_m, dates)
    month_back = (1 + rf_d).groupby(rf_d.index.to_period('M')).prod() - 1
    gap = np.abs(month_back.to_numpy() - rf_m.reindex(month_back.index).to_numpy()).max()
    print(f'\n== 4. RF 拆日（B3）：{len(rf_d)} 个交易日；按月连乘还原的最大误差 = {gap:.1e}')

    rounded = load_rf_daily_rounded(args.snapshot)
    bil = prices['BIL']['adj_close'].pct_change().dropna()  # 首日无收益，丢弃而非填 0
    year = dates.year
    table = pd.DataFrame({
        'RF（月频拆日）': (1 + rf_d).groupby(year).prod() - 1,
        'RF（日频四舍五入版）': (1 + rounded).groupby(rounded.index.year).prod() - 1,
        'BIL（adj_close）': (1 + bil).groupby(bil.index.year).prod() - 1,
    })
    table['BIL − RF（百分点）'] = (table['BIL（adj_close）'] - table['RF（月频拆日）']) * 100
    print('\n== 5. 按年复利（2007 年只含 6–12 月）')
    print(table.to_string(float_format=lambda x: f'{x:8.4f}'))

    rf_total = (1 + rf_d).prod() - 1
    bil_total = (1 + bil).prod() - 1
    years = len(dates) / 252
    print(f'\n== 6. 开发期累计：RF {rf_total:.2%}，BIL {bil_total:.2%}，'
          f'差 {(bil_total - rf_total) * 100:.2f} 个百分点；'
          f'年化 RF {(1 + rf_total) ** (1 / years) - 1:.2%}，'
          f'BIL {(1 + bil_total) ** (1 / years) - 1:.2%}（约 {years:.1f} 年）')


if __name__ == '__main__':
    main()
