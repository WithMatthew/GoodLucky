"""W08D03-B：固定种子的虚构日收益与价格路径。

从仓库根目录运行：python -X utf8 -B -m src.simulate_returns
模型假设每日独立抽取，涨1%与跌1%各50%；这不是市场估计或预测。
D0为起始时点，D1起每步视为一个虚构交易日，不对应真实交易日历。
收益用小数，价格单位为虚构美元/份；无分红、拆股、费用或资金进出。
不读取文件或行情，不联网，不下单；导入不执行模拟。
"""

from math import isfinite
from platform import python_version
from random import Random

from src.describe_returns import describe_returns


def simulate_path(initial_price=100.0, days=5, seed=42):
    """每次调用新建局部生成器；相同输入与生成规则可重现路径。"""
    if isinstance(days, bool) or not isinstance(days, int) or days < 0:
        raise ValueError("days必须是非负整数")
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise ValueError("本教学入口的seed必须是整数")
    if isinstance(initial_price, bool) or not isfinite(initial_price) or initial_price <= 0:
        raise ValueError("初始价格必须为有限正数")

    rng = Random(seed)
    draws = []
    returns = []
    prices = [float(initial_price)]
    for _ in range(days):
        draw = rng.random()
        daily_return = -0.01 if draw < 0.5 else 0.01
        next_price = prices[-1] * (1 + daily_return)
        if not isfinite(next_price) or next_price <= 0:
            raise ValueError("价格超出本教学程序的浮点数计算范围")
        draws.append(draw)
        returns.append(daily_return)
        prices.append(next_price)

    return {
        "data_kind": "SIMULATED_EDUCATIONAL_ONLY",
        "model": "equal_up_down_1pct_v1",
        "python_version": python_version(),
        "generator": "random.Random; one random() call per day",
        "seed": seed,
        "days": days,
        "initial_price": initial_price,
        "draws": draws,
        "returns": returns,
        "prices": prices,
    }


def main():
    # 在查看结果前固定参数，不按收益筛选种子。
    result = simulate_path(initial_price=100.0, days=5, seed=42)
    repeated = simulate_path(initial_price=100.0, days=5, seed=42)
    print("SIMULATED：纯教学模拟，不是真实行情或预测")
    print("模型：每日独立涨1%/跌1%，各50%；小数收益；价格为虚构美元/份")
    print("D0起始，D1起每日一步；不对应真实日期；无分红/拆股/费用/资金进出")
    print(f"Python={result['python_version']}; seed=42; days=5; initial_price=100")
    print("日次, 随机数(仅显示6位), 日收益率, 价格(仅显示8位)")
    print(f"D0, —, —, {result['prices'][0]:.8f}")
    for day, (draw, daily_return, price) in enumerate(
        zip(result["draws"], result["returns"], result["prices"][1:]), start=1
    ):
        print(f"D{day}, {draw:.6f}, {daily_return:+.2%}, {price:.8f}")
    print(f"新建生成器重复运行，完整结果相同：{result == repeated}")
    stats = describe_returns(result["returns"])
    cumulative_return = result["prices"][-1] / result["prices"][0] - 1
    print(f"日收益算术均值={stats['mean']:.4%}; 小数平方尺度方差={stats['variance']:.8f}")
    print(f"整段累计收益率={cumulative_return:.8%}；以上均不年化")


if __name__ == "__main__":
    main()
