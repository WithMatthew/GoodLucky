"""仅使用虚构数据检查复现、时间对齐及复利，不访问账户或行情。"""

import random
import unittest

from src.simulate_returns import simulate_path


class SimulatedPathTests(unittest.TestCase):
    def test_fixed_seed_reference_and_reproducibility(self):
        first = simulate_path(days=5, seed=42)
        self.assertEqual(first, simulate_path(days=5, seed=42))
        self.assertEqual(first["returns"], [0.01, -0.01, -0.01, -0.01, 0.01])
        self.assertEqual(len(first["prices"]), 6)
        self.assertAlmostEqual(first["prices"][-1], 98.98020099)

    def test_compounding_and_initial_price_scaling(self):
        base = simulate_path(initial_price=100, days=2, seed=42)
        doubled = simulate_path(initial_price=200, days=2, seed=42)
        self.assertEqual(base["returns"], doubled["returns"])
        for actual, expected in zip(base["prices"], [100, 101, 99.99]):
            self.assertAlmostEqual(actual, expected)
        for first, second in zip(base["prices"], doubled["prices"]):
            self.assertAlmostEqual(second, 2 * first)

    def test_local_generator_does_not_change_global_state(self):
        before = random.getstate()
        simulate_path()
        self.assertEqual(random.getstate(), before)

    def test_zero_days_preserves_initial_observation(self):
        result = simulate_path(initial_price=80, days=0, seed=0)
        self.assertEqual(result["returns"], [])
        self.assertEqual(result["draws"], [])
        self.assertEqual(result["prices"], [80])

    def test_invalid_inputs(self):
        invalid = [
            {"days": -1}, {"days": 1.5}, {"days": True},
            {"seed": None}, {"seed": 1.5}, {"seed": True},
            {"initial_price": 0}, {"initial_price": -100},
            {"initial_price": float("nan")},
            {"initial_price": float("inf")}, {"initial_price": True},
        ]
        for kwargs in invalid:
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                simulate_path(**kwargs)


if __name__ == "__main__":
    unittest.main()
