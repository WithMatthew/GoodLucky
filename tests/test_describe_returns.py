"""运行：python -X utf8 -B -m unittest discover -s tests -p test_describe_returns.py -v。"""

import unittest

from src.describe_returns import describe_returns


class DescribeReturnsTests(unittest.TestCase):
    def test_five_observations_match_hand_calculated_r7(self):
        values = [0.03, -0.04, 0.12, 0.01, -0.02]
        original = values.copy()
        result = describe_returns(values)
        self.assertEqual(result["count"], 5)
        for name, expected in {
            "mean": 0.02, "median": 0.01, "q25": -0.02,
            "q50": 0.01, "q75": 0.03, "variance": 0.00308,
        }.items():
            self.assertAlmostEqual(result[name], expected)
        self.assertEqual(values, original)

    def test_same_mean_different_variances_use_n_denominator(self):
        bing = describe_returns([0.0, 0.02, 0.0, 0.02])
        ding = describe_returns([-0.02, 0.04, -0.02, 0.04])
        self.assertAlmostEqual(bing["mean"], 0.01)
        self.assertAlmostEqual(ding["mean"], 0.01)
        self.assertAlmostEqual(bing["variance"], 0.0001)
        self.assertAlmostEqual(ding["variance"], 0.0009)
        self.assertAlmostEqual(bing["variance"] * 10000, 1.0)
        self.assertAlmostEqual(ding["variance"] * 10000, 9.0)

    def test_constant_nonzero_returns_have_zero_variance(self):
        result = describe_returns([0.01] * 4)
        self.assertEqual(result["variance"], 0)
        self.assertEqual(result["mean"], 0.01)

    def test_two_values_use_linear_interpolation(self):
        result = describe_returns([0.0, 0.04])
        for name, expected in {
            "q25": 0.01, "q50": 0.02, "q75": 0.03, "variance": 0.0004,
        }.items():
            self.assertAlmostEqual(result[name], expected)

    def test_short_or_nonfinite_inputs_are_rejected(self):
        for values in ([], [0.01], [0.0, float("nan")],
                       [0.0, float("inf")], [float("-inf"), 0.0]):
            with self.subTest(values=values):
                with self.assertRaises(ValueError):
                    describe_returns(values)


if __name__ == "__main__":
    unittest.main()
