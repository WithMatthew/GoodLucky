"""参考基准的确定性检查；不读取任何行情或连接账户。"""

from copy import deepcopy
from datetime import date, timedelta
import json
from math import sqrt
from pathlib import Path
import tempfile
import unittest

from src.buy_hold_baseline import (
    guarded_development_path, normalize_adjusted_path, summarize_path, validate_scope,
)


def observations(values):
    return [{"date": date(2020, 1, 2) + timedelta(days=i), "adj_close": value}
            for i, value in enumerate(values)]


class BuyHoldBaselineTests(unittest.TestCase):
    def test_b1_hand_result_and_no_input_mutation(self):
        rows = observations([80, 84, 82.32])
        original = deepcopy(rows)
        path = normalize_adjusted_path(rows)
        self.assertEqual(rows, original)
        self.assertIsNone(path[0]["period_return"])
        for row, normalized in zip(path, [1, 1.05, 1.029]):
            self.assertAlmostEqual(row["normalized_value"], normalized)
        self.assertAlmostEqual(path[-1]["model_value"], 1029)
        self.assertAlmostEqual(path[-1]["cumulative_return"], .029)
        self.assertAlmostEqual(path[1]["period_return"], .05)
        self.assertAlmostEqual(path[2]["period_return"], -.02)

    def test_display_scale_does_not_change_returns(self):
        first = normalize_adjusted_path(observations([50, 55, 52.25]), 1000)
        second = normalize_adjusted_path(observations([50, 55, 52.25]), 2000)
        for a, b in zip(first, second):
            self.assertEqual(a["normalized_value"], b["normalized_value"])
            self.assertEqual(a["period_return"], b["period_return"])
            self.assertEqual(2 * a["model_value"], b["model_value"])

    def test_first_missing_return_is_distinct_from_observed_zero(self):
        path = normalize_adjusted_path(observations([100, 100, 110]))
        self.assertIsNone(path[0]["period_return"])
        self.assertEqual(path[0]["cumulative_return"], 0)
        self.assertEqual(path[1]["period_return"], 0)
        summary = summarize_path(path)
        self.assertEqual(summary["return_intervals"], 2)
        self.assertAlmostEqual(summary["annualized_volatility"], .1 / sqrt(2) * sqrt(252))
        self.assertAlmostEqual(summary["sharpe_rf_zero"], sqrt(126))

    def test_drawdown_only_uses_preceding_peaks(self):
        summary = summarize_path(normalize_adjusted_path(observations([100, 80, 120, 108])))
        self.assertAlmostEqual(summary["maximum_drawdown"], .2)
        self.assertAlmostEqual(summary["cumulative_return"], .08)
        self.assertIsNone(summary["executed_trade_count"])
        self.assertIsNone(summary["executed_turnover"])

    def test_single_observation_has_no_return_sample(self):
        summary = summarize_path(normalize_adjusted_path(observations([80])))
        self.assertEqual(summary["return_intervals"], 0)
        self.assertEqual(summary["cumulative_return"], 0)
        self.assertEqual(summary["maximum_drawdown"], 0)
        self.assertIsNone(summary["annualized_volatility"])
        self.assertIsNone(summary["sharpe_rf_zero"])

    def test_constant_curve_has_zero_volatility_and_undefined_sharpe(self):
        summary = summarize_path(normalize_adjusted_path(observations([80, 80, 80])))
        self.assertEqual(summary["annualized_volatility"], 0)
        self.assertIsNone(summary["sharpe_rf_zero"])

    def test_invalid_prices_are_rejected_without_filling(self):
        for value in [None, 0, -1, float("nan"), float("inf"), True, "80"]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                normalize_adjusted_path(observations([80, value]))
        with self.assertRaises(ValueError):
            normalize_adjusted_path([])
        with self.assertRaises(KeyError):
            normalize_adjusted_path([{"date": date(2020, 1, 2)}])

    def test_invalid_display_values_are_rejected(self):
        for value in [0, -1, None, True, float("inf")]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                normalize_adjusted_path(observations([80]), value)

    def test_duplicate_reversed_and_unparsed_dates_are_rejected(self):
        rows = observations([80, 84])
        for invalid in [[rows[0], rows[0]], rows[::-1],
                        [{"date": "2020-01-02", "adj_close": 80}]]:
            with self.subTest(rows=invalid), self.assertRaises(ValueError):
                normalize_adjusted_path(invalid)

    def test_sealed_and_redirected_paths_are_rejected_before_reading(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            relative = "data/derived/etf-research-v1/development/SPY.csv"
            entry = {"partition": "development", "symbol": "SPY", "derived": {"path": relative}}
            self.assertEqual(guarded_development_path(root, "SPY", entry), (root / relative).resolve())
            for wrong in ["data/sealed/etf-research-v1/SPY.csv", "../SPY.csv", "D:/SPY.csv"]:
                changed = deepcopy(entry)
                changed["derived"]["path"] = wrong
                with self.subTest(path=wrong), self.assertRaises(ValueError):
                    guarded_development_path(root, "SPY", changed)
            changed = deepcopy(entry)
            changed["partition"] = "final_test"
            with self.assertRaises(ValueError):
                guarded_development_path(root, "SPY", changed)

    def test_scope_changes_cannot_enable_final_test_or_other_method(self):
        root = Path(__file__).resolve().parents[1]
        settings = json.loads((root / "configs/buy-hold-baseline-v1.json").read_text(encoding="utf-8"))
        plan = {"study_id": "etf-research-v1", "symbols": ["SPY", "DIA", "QQQ"],
                "development": {"start": "2020-01-01", "end": "2024-12-31"},
                "interval": "1d", "timezone": "America/New_York", "currency": "USD"}
        validate_scope(settings, plan)
        for key, value in [("development", {"start": "2025-01-01", "end": "2025-12-31"}),
                           ("field", "close"), ("cash_weight", .5), ("symbols", ["QQQ"])]:
            changed = deepcopy(settings)
            changed[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate_scope(changed, plan)
        changed_plan = deepcopy(plan)
        changed_plan["development"]["end"] = "2025-12-31"
        with self.assertRaises(ValueError):
            validate_scope(settings, changed_plan)


if __name__ == "__main__":
    unittest.main()
