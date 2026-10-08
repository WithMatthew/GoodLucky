"""运行：python -m unittest discover -s tests -v；不依赖行情、网络或账户。"""

import unittest

from src.asset_paths import total_asset_path


class TotalAssetPathTests(unittest.TestCase):
    def test_lesson_paths_match_hand_calculations(self):
        cases = [
            ([800, 1040], [20, 20], [820, 1080], 0.08),
            ([980, 1020], [30, 30], [1010, 1080], 0.08),
            ([1000, 1000], [0, 0], [1000, 1000], 0),
        ]
        for values, incomes, expected, expected_return in cases:
            with self.subTest(values=values, incomes=incomes):
                totals = total_asset_path(values, incomes)
                self.assertEqual(totals, expected)
                self.assertAlmostEqual((totals[-1] - 1000) / 1000, expected_return)

    def test_zero_income_does_not_add_past_asset_values(self):
        self.assertEqual(total_asset_path([100, 80, 90], [0, 0, 0]), [100, 80, 90])

    def test_cash_remains_in_later_periods_without_new_income(self):
        self.assertEqual(total_asset_path([100, 80, 90], [7, 0, 0]), [107, 87, 97])

    def test_mismatched_periods_are_rejected(self):
        for values, incomes in [([100, 110], [5]), ([100], [5, 5])]:
            with self.subTest(values=values, incomes=incomes):
                with self.assertRaises(ValueError):
                    total_asset_path(values, incomes)

    def test_no_periods_returns_no_observations(self):
        self.assertEqual(total_asset_path([], []), [])


if __name__ == "__main__":
    unittest.main()
