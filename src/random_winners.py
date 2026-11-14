"""W08D04-B：样本长度与筛选随机赢家的两个独立教学实验。

运行：python -X utf8 -B -m src.random_winners
全为合成日收益：每日独立涨/跌1%，各50%；候选之间也假设独立。
报告的是日收益算术均值，不是累计收益，不年化；无费用或实际交易。
参数在首次观察输出前固定；仅标准库，导入不执行实验，无文件/网络读写。
"""

import json
from math import isfinite
from platform import python_version
from random import Random
from statistics import mean


def _positive_int(value, name):
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{name}必须是正整数")


def _generator(seed):
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise ValueError("seed必须是整数")
    return Random(seed)


def _draw_returns(rng, days):
    return [-0.01 if rng.random() < 0.5 else 0.01 for _ in range(days)]


def sample_size_experiment(seed=20261115, repetitions=1000, short_days=10, long_days=100):
    """每次生成long_days，再用同一路径前缀比较两种观察长度。"""
    for name, value in (("repetitions", repetitions), ("short_days", short_days), ("long_days", long_days)):
        _positive_int(value, name)
    if short_days > long_days:
        raise ValueError("short_days不能大于long_days")
    rng = _generator(seed)
    short_means = []
    long_means = []
    for _ in range(repetitions):
        returns = _draw_returns(rng, long_days)
        short_means.append(mean(returns[:short_days]))
        long_means.append(mean(returns))
    return {
        "seed": seed,
        "repetitions": repetitions,
        "short_days": short_days,
        "long_days": long_days,
        "model_daily_mean": 0.0,
        "short_average_distance_from_zero_pp": 100 * mean(abs(x) for x in short_means),
        "long_average_distance_from_zero_pp": 100 * mean(abs(x) for x in long_means),
        "long_farther_from_zero_count": sum(abs(b) > abs(a) for a, b in zip(short_means, long_means)),
        "first_path_daily_means_decimal": [short_means[0], long_means[0]],
    }


def choose_winner(selection_returns):
    """只接收筛选期数据；按日均收益最高选，平局取最小下标。"""
    if not selection_returns or not selection_returns[0]:
        raise ValueError("至少需要一个候选及一个筛选期观测")
    days = len(selection_returns[0])
    for row in selection_returns:
        if len(row) != days or not all(isfinite(value) for value in row):
            raise ValueError("所有候选必须有相同数量的有限筛选期观测")
    averages = [mean(row) for row in selection_returns]
    return max(range(len(averages)), key=averages.__getitem__)


def selection_experiment(seed=20261116, candidates=100, selection_days=20, followup_days=100):
    """先选定并固定冠军，再生成后续数据；不按后续表现改选。"""
    for name, value in (("candidates", candidates), ("selection_days", selection_days), ("followup_days", followup_days)):
        _positive_int(value, name)
    rng = _generator(seed)
    selection = [_draw_returns(rng, selection_days) for _ in range(candidates)]
    winner = choose_winner(selection)
    # 先固定winner，再生成所有候选D(selection_days+1)起的后续收益。
    followup = [_draw_returns(rng, followup_days) for _ in range(candidates)]

    def summary(index):
        return {
            "candidate_id": index + 1,
            "selection_up_days": selection[index].count(0.01),
            "selection_daily_mean_decimal": mean(selection[index]),
            "followup_up_days": followup[index].count(0.01),
            "followup_daily_mean_decimal": mean(followup[index]),
        }

    return {
        "seed": seed,
        "candidates": candidates,
        "selection_days": selection_days,
        "followup_days": followup_days,
        "selection_rule": "highest arithmetic mean; ties: lowest candidate ID",
        "preselected_candidate": summary(0),
        "selected_winner": summary(winner),
    }


def main():
    result = {
        "data_kind": "SIMULATED_EDUCATIONAL_ONLY",
        "python_version": python_version(),
        "model": "independent equal up/down 1% daily; identical candidates; theoretical daily mean 0%",
        "generator": "local random.Random; random()<0.5 gives -0.01, otherwise +0.01",
        "metric": "arithmetic daily mean; decimal returns; distance explicitly in percentage points; not annualized",
        "sample_size": sample_size_experiment(),
        "selection": selection_experiment(),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
