"""虚构均线账本的独立手算和边界检查，不依赖行情、账户或网络。"""

from copy import deepcopy
import unittest

from src.moving_average import lesson_days, sma_ledger


class MovingAverageTests(unittest.TestCase):
    def test_hand_ledger_and_input_preserved(self):
        days = lesson_days()
        history = [57, 54]
        original = deepcopy(days)
        rows = sma_ledger(98, history, days)
        expected = [
            (6, "close", 0, 56, 1, 0, 98, 98),
            (7, "close", 1, 57, 1, 1, 40, 100),
            (8, "close", 0, 58, 0, 1, 40, 97),
            (9, "open", -1, None, None, 0, 96, 96),
        ]
        keys = ("day", "phase", "trade", "sma", "target", "shares", "cash", "total_value")
        self.assertEqual([tuple(row[key] for key in keys) for row in rows], expected)
        self.assertEqual(days, original)
        self.assertEqual(history, [57, 54])
        self.assertAlmostEqual(rows[-1]["total_value"] / 100 - 1, -0.04)

    def test_warmup_and_last_close_do_not_create_an_early_fill(self):
        days = [
            {"day": 1, "open": 10, "close": 10},
            {"day": 2, "open": 10, "close": 11},
            {"day": 3, "open": 11, "close": 12},
        ]
        rows = sma_ledger(100, [], days)
        self.assertEqual([row["sma"] for row in rows], [None, None, 11])
        self.assertEqual([row["target"] for row in rows], [None, None, 1])
        self.assertEqual([row["shares"] for row in rows], [0, 0, 0])
        self.assertEqual(rows[-1]["cash"], 100)

    def test_equal_close_and_average_targets_zero_then_sells_next_open(self):
        rows = sma_ledger(100, [8, 9], [
            {"day": 3, "open": 10, "close": 10},
            {"day": 4, "open": 11, "close": 9.5},
            {"day": 5, "open": 9, "close": None},
        ])
        self.assertEqual(rows[1]["sma"], 9.5)
        self.assertEqual(rows[1]["target"], 0)
        self.assertEqual(rows[1]["shares"], 1)
        self.assertEqual(rows[1]["cash"], 89)
        self.assertEqual(rows[2]["trade"], -1)
        self.assertEqual(rows[2]["cash"], 98)

    def test_open_gap_checks_cash_and_exact_cash_is_allowed(self):
        days = [
            {"day": 3, "open": 10, "close": 10},
            {"day": 4, "open": 101, "close": None},
        ]
        with self.assertRaisesRegex(ValueError, "资金不足"):
            sma_ledger(100, [8, 9], days)
        days[1]["open"] = 100
        row = sma_ledger(100, [8, 9], days)[-1]
        self.assertEqual((row["cash"], row["shares"], row["total_value"]), (0, 1, 100))

    def test_future_close_cannot_change_earlier_rows_or_same_open_trade(self):
        days = lesson_days()
        baseline = sma_ledger(98, [57, 54], days)
        self.assertEqual(sma_ledger(98, [57, 54], days[:2]), baseline[:2])
        days[2]["close"] = 77
        changed = sma_ledger(98, [57, 54], days)
        self.assertEqual(changed[:2], baseline[:2])
        for key in ("trade", "shares", "cash"):
            self.assertEqual(changed[2][key], baseline[2][key])
        self.assertEqual(changed[2]["target"], 1)
        self.assertEqual(baseline[2]["target"], 0)

    def test_rejects_invalid_values_missing_fields_and_nonconsecutive_days(self):
        for value in (-1, True, float("nan"), float("inf")):
            with self.subTest(cash=value), self.assertRaises(ValueError):
                sma_ledger(value, [], [])
        for field, value in (("open", 0), ("close", float("nan")), ("day", True)):
            days = lesson_days()
            days[0][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                sma_ledger(98, [57, 54], days)
        with self.assertRaises(ValueError):
            sma_ledger(98, [57, 54], [lesson_days()[1], lesson_days()[0]])
        with self.assertRaises(ValueError):
            sma_ledger(98, [57, 54], [lesson_days()[0], lesson_days()[2]])
        days = lesson_days()
        days[0]["close"] = None
        with self.assertRaises(ValueError):
            sma_ledger(98, [57, 54], days)
        with self.assertRaises(KeyError):
            sma_ledger(98, [], [{"day": 1, "open": 50}])
        with self.assertRaises(ValueError):
            sma_ledger(98, [50, 51, 52], [])

    def test_empty_input_and_zero_cash_waiting(self):
        self.assertEqual(sma_ledger(0, [], []), [])
        row = sma_ledger(0, [50, 50], [{"day": 3, "open": 50, "close": 50}])[0]
        self.assertEqual((row["target"], row["trade"], row["cash"]), (0, 0, 0))


if __name__ == "__main__":
    unittest.main()
