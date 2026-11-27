"""W11D02-B 验收测试：小样本手算数据，离线、确定性。不要为通过测试而修改本文件。"""

import unittest

import numpy as np
import pandas as pd

from src.cross_asset_checks import flag_big_moves, monthly_to_daily_rf, ohlc_violations


class OhlcViolationsTest(unittest.TestCase):
    def setUp(self):
        self.frame = pd.DataFrame({
            'open':  [10.0, 10.0, 10.0, 10.0],
            'high':  [11.0, 10.5,  9.8, 10.0],
            'low':   [ 9.0, 10.2,  9.5, 10.0],
            'close': [10.5, 10.4,  9.6, 10.0],
        }, index=pd.to_datetime(['2008-01-02', '2008-01-03', '2008-01-04', '2008-01-07']))

    def test_flags(self):
        result = ohlc_violations(self.frame)
        # 第 2 行 low=10.2 > min(open,close)=10.0；第 3 行 high=9.8 < max=10.0；第 4 行全相等合法
        self.assertEqual(result.tolist(), [False, True, True, False])
        self.assertEqual(result.name, 'ohlc_violation')
        self.assertTrue(result.index.equals(self.frame.index))

    def test_input_unchanged(self):
        before = self.frame.copy()
        ohlc_violations(self.frame)
        pd.testing.assert_frame_equal(self.frame, before)


class FlagBigMovesTest(unittest.TestCase):
    def test_threshold_and_sign(self):
        prices = pd.Series([100.0, 112.0, 99.68, 104.664, 104.664],
                           index=pd.to_datetime(['2020-03-09', '2020-03-10', '2020-03-11',
                                                 '2020-03-12', '2020-03-13']))
        # 收益：NaN, +12%, -11%, +5%, 0%（均离阈值足够远，避开浮点边界）
        result = flag_big_moves(prices, 0.115)
        self.assertEqual([d.strftime('%Y-%m-%d') for d in result.index], ['2020-03-10'])
        self.assertAlmostEqual(result.iloc[0], 0.12)
        result = flag_big_moves(prices, 0.10)
        self.assertEqual(len(result), 2)
        self.assertAlmostEqual(result.loc['2020-03-11'], -0.11)
        self.assertFalse(result.isna().any())
        self.assertEqual(len(flag_big_moves(prices, 0.03)), 3)


class MonthlyToDailyRfTest(unittest.TestCase):
    def setUp(self):
        self.rf_m = pd.Series([0.0021, 0.0010],
                              index=pd.PeriodIndex(['2023-01', '2023-02'], freq='M'))
        self.dates = pd.to_datetime(['2023-01-30', '2023-01-31', '2023-02-01',
                                     '2023-02-02', '2023-02-03'])

    def test_values(self):
        rf = monthly_to_daily_rf(self.rf_m, self.dates)
        self.assertTrue(rf.index.equals(self.dates))
        self.assertEqual(rf.name, 'rf')
        self.assertAlmostEqual(rf.iloc[0], 1.0021 ** (1 / 2) - 1, places=12)
        self.assertAlmostEqual(rf.iloc[2], 1.0010 ** (1 / 3) - 1, places=12)

    def test_compounds_back_to_month(self):
        rf = monthly_to_daily_rf(self.rf_m, self.dates)
        by_month = (1 + rf).groupby(rf.index.to_period('M')).prod() - 1
        np.testing.assert_allclose(by_month.to_numpy(), [0.0021, 0.0010], rtol=0, atol=1e-15)

    def test_missing_month_raises(self):
        dates = self.dates.append(pd.to_datetime(['2023-03-01']))
        with self.assertRaises(ValueError):
            monthly_to_daily_rf(self.rf_m, dates)


if __name__ == '__main__':
    unittest.main()
