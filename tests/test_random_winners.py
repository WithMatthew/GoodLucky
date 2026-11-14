"""固定输入检查筛选方向、时间隔离与样本长度，不做随机显著性断言。"""

import random
import unittest

from src.random_winners import choose_winner, sample_size_experiment, selection_experiment


class RandomWinnerTests(unittest.TestCase):
    def test_selection_rule_and_tie(self):
        training = [[-0.01, -0.01], [0.01, 0.01], [0.01, 0.01]]
        self.assertEqual(choose_winner(training), 1)
        self.assertEqual(training[0], [-0.01, -0.01])

    def test_future_horizon_cannot_change_selection(self):
        short = selection_experiment(seed=17, candidates=8, selection_days=10, followup_days=1)
        long = selection_experiment(seed=17, candidates=8, selection_days=10, followup_days=50)
        for key in ("candidate_id", "selection_up_days", "selection_daily_mean_decimal"):
            self.assertEqual(short["selected_winner"][key], long["selected_winner"][key])
        self.assertGreaterEqual(
            short["selected_winner"]["selection_daily_mean_decimal"],
            short["preselected_candidate"]["selection_daily_mean_decimal"],
        )

    def test_one_observation_distance_and_equal_windows(self):
        result = sample_size_experiment(seed=7, repetitions=8, short_days=1, long_days=1)
        self.assertEqual(result["short_average_distance_from_zero_pp"], 1.0)
        self.assertEqual(result["long_average_distance_from_zero_pp"], 1.0)
        self.assertEqual(result["long_farther_from_zero_count"], 0)

    def test_reproducible_and_global_state_unchanged(self):
        before = random.getstate()
        self.assertEqual(sample_size_experiment(8, 10, 2, 10), sample_size_experiment(8, 10, 2, 10))
        self.assertEqual(selection_experiment(8, 10, 2, 10), selection_experiment(8, 10, 2, 10))
        self.assertEqual(before, random.getstate())

    def test_invalid_inputs(self):
        for data in ([], [[]], [[0.01], []], [[float("nan")]], [[float("inf")]]):
            with self.subTest(data=data), self.assertRaises(ValueError):
                choose_winner(data)
        for kwargs in ({"repetitions": 0}, {"short_days": 11, "long_days": 10}, {"seed": None}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                sample_size_experiment(**kwargs)
        for kwargs in ({"candidates": True}, {"followup_days": 0}, {"selection_days": 1.5}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                selection_experiment(**kwargs)


if __name__ == "__main__":
    unittest.main()
