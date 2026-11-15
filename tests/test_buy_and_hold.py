"""确定性账本测试：无文件、网络、行情或账户依赖。"""

from copy import deepcopy
import unittest

from src.buy_and_hold import buy_and_hold_ledger


class BuyAndHoldTests(unittest.TestCase):
    def test_lesson_hand_ledger_and_input_unchanged(self):
        periods = [
            {"price": 49, "dividend_per_share": 1, "cash_rate": 0},
            {"price": 52, "dividend_per_share": 0, "cash_rate": 0.01},
        ]
        original = deepcopy(periods)
        rows = buy_and_hold_ledger(1000, 10, 50, periods)
        self.assertEqual(periods, original)
        self.assertEqual(len(rows), 3)
        for row, cash, market_value, total, net_value, ret in zip(
            rows, [500, 510, 515.1], [500, 490, 520], [1000, 1000, 1035.1],
            [1, 1, 1.0351], [0, 0, 0.0351]
        ):
            self.assertEqual(row["shares"], 10)
            self.assertAlmostEqual(row["cash"], cash)
            self.assertAlmostEqual(row["market_value"], market_value)
            self.assertAlmostEqual(row["total_value"], total)
            self.assertAlmostEqual(row["normalized_value"], net_value)
            self.assertAlmostEqual(row["cumulative_return"], ret)
        self.assertAlmostEqual(rows[2]["interest"], 5.1)
        self.assertAlmostEqual(rows[1]["dividend_cash"], 10)

    def test_end_period_dividend_does_not_earn_same_period_interest(self):
        rows = buy_and_hold_ledger(1000, 10, 50, [
            {"price": 49, "dividend_per_share": 1, "cash_rate": 0.01},
        ])
        self.assertAlmostEqual(rows[-1]["interest"], 5)
        self.assertAlmostEqual(rows[-1]["cash"], 515)
        self.assertAlmostEqual(rows[-1]["total_value"], 1005)

    def test_empty_periods_preserves_initial_wealth_and_cash_remainder(self):
        rows = buy_and_hold_ledger(1000, 3, 300, [])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["cash"], 100)
        self.assertEqual(rows[0]["total_value"], 1000)
        self.assertEqual(rows[0]["cumulative_return"], 0)

    def test_cash_only_does_not_receive_dividends(self):
        row = buy_and_hold_ledger(200, 0, 50, [
            {"price": 70, "dividend_per_share": 3, "cash_rate": 0.05},
        ])[-1]
        self.assertEqual(row["dividend_cash"], 0)
        self.assertEqual(row["market_value"], 0)
        self.assertAlmostEqual(row["total_value"], 210)

    def test_negative_cash_return_reduces_cash_without_selling_shares(self):
        row = buy_and_hold_ledger(1000, 10, 50, [
            {"price": 50, "dividend_per_share": 0, "cash_rate": -0.1},
        ])[-1]
        self.assertEqual(row["cash"], 450)
        self.assertEqual(row["shares"], 10)
        self.assertEqual(row["total_value"], 950)

    def test_rejects_borrowing_invalid_capital_prices_and_share_counts(self):
        cases = [(100, 3, 50), (0, 0, 50), (1000, -1, 50),
                 (1000, 1.5, 50), (1000, True, 50), (1000, 10, 0),
                 (float("nan"), 0, 50), (1000, 0, float("inf"))]
        for cash, shares, price in cases:
            with self.subTest(cash=cash, shares=shares, price=price):
                with self.assertRaises(ValueError):
                    buy_and_hold_ledger(cash, shares, price, [])

    def test_missing_invalid_period_values_are_not_filled(self):
        valid = {"price": 50, "dividend_per_share": 0, "cash_rate": 0}
        for key, value in [("price", None), ("price", 0), ("price", float("nan")),
                           ("dividend_per_share", -1), ("cash_rate", -1.01),
                           ("cash_rate", float("inf"))]:
            with self.subTest(key=key, value=value):
                with self.assertRaises(ValueError):
                    buy_and_hold_ledger(1000, 10, 50, [{**valid, key: value}])
        with self.assertRaises(KeyError):
            buy_and_hold_ledger(1000, 10, 50, [{"price": 50, "cash_rate": 0}])


if __name__ == "__main__":
    unittest.main()
