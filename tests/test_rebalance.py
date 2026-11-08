"""运行：python -B -m unittest discover -s tests -p test_rebalance.py -v。"""

import unittest

from src.rebalance import rebalance


class RebalanceTests(unittest.TestCase):
    def test_exercise_cash_and_holdings_match_hand_calculation(self):
        result = rebalance(80, 40, 100, 100, 3000, 0.50, 0.40)
        expected = {
            "total_before": 15000, "stock_trade": -500, "bond_trade": 2000,
            "stock_shares_after": 75, "bond_shares_after": 60,
            "cash_after": 1500, "total_after": 15000,
        }
        for key, value in expected.items():
            self.assertAlmostEqual(result[key], value)
        for actual, expected_weight in zip(result["weights_after"], (0.5, 0.4, 0.1)):
            self.assertAlmostEqual(actual, expected_weight)

    def test_different_prices_and_sale_proceeds_left_in_cash(self):
        result = rebalance(60, 30, 150, 100, 1000, 0.60, 0.30)
        self.assertEqual(result["stock_trade"], -1200)
        self.assertEqual(result["bond_trade"], 900)
        self.assertEqual(result["stock_shares_after"], 52)
        self.assertEqual(result["bond_shares_after"], 39)
        self.assertEqual(result["cash_after"], 1300)
        self.assertEqual(result["total_after"], 13000)

    def test_buy_stock_and_sell_bond_reverses_cash_flows(self):
        result = rebalance(40, 80, 100, 100, 3000, 0.50, 0.40)
        self.assertEqual(result["stock_trade"], 3500)
        self.assertEqual(result["bond_trade"], -2000)
        self.assertEqual(result["cash_after"], 1500)
        self.assertEqual(result["total_after"], 15000)

    def test_already_at_target_needs_no_trades(self):
        result = rebalance(75, 60, 100, 100, 1500, 0.50, 0.40)
        self.assertEqual(result["stock_trade"], 0)
        self.assertEqual(result["bond_trade"], 0)
        self.assertEqual(result["cash_after"], 1500)

    def test_all_cash_target_sells_both_holdings(self):
        result = rebalance(80, 40, 100, 100, 3000, 0, 0)
        self.assertEqual(result["stock_shares_after"], 0)
        self.assertEqual(result["bond_shares_after"], 0)
        self.assertEqual(result["cash_after"], 15000)
        self.assertEqual(result["weights_after"], (0, 0, 1))

    def test_all_cash_start_and_zero_cash_target(self):
        result = rebalance(0, 0, 100, 100, 1000, 0.60, 0.40)
        self.assertEqual(result["stock_shares_after"], 6)
        self.assertEqual(result["bond_shares_after"], 4)
        self.assertEqual(result["cash_after"], 0)
        self.assertEqual(result["total_after"], 1000)

    def test_invalid_inputs_are_rejected(self):
        base = dict(stock_shares=80, bond_shares=40, stock_price=100,
                    bond_price=100, cash=3000, stock_weight=0.5, bond_weight=0.4)
        overrides = [
            {"stock_shares": -1}, {"bond_shares": -1}, {"cash": -1},
            {"stock_price": 0}, {"bond_price": -100},
            {"stock_weight": -0.1}, {"bond_weight": -0.1},
            {"stock_weight": 0.7, "bond_weight": 0.4},
            {"cash": float("nan")}, {"stock_price": float("inf")},
            {"stock_shares": 0, "bond_shares": 0, "cash": 0},
        ]
        for changes in overrides:
            with self.subTest(changes=changes):
                with self.assertRaises(ValueError):
                    rebalance(**(base | changes))


if __name__ == "__main__":
    unittest.main()
