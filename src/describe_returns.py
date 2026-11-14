"""W08D03-A：用标准库核对虚构日收益率，仅做描述统计。

从仓库根目录运行：python -X utf8 -B -m src.describe_returns
输入收益率用小数（1%=0.01），方差输出为小数尺度的平方。
分位数采用R7/inclusive，方差除以观测个数n，不年化。
仅使用Python标准库；实际验证版本记录在docs/lessons/week-08.md。
不读取行情、连接账户或生成随机数；导入模块没有执行副作用。
"""

from math import isfinite
from statistics import mean, median, pvariance, quantiles


def describe_returns(returns):
    """概括至少两个有限收益率；保留原输入顺序，不填补缺失。

    这里只检查长度和有限数值，不能自动判断单位、日期或来源是否正确。
    方法是描述给定观测组，不估计未知总体或预测未来。
    """
    values = list(returns)
    if len(values) < 2:
        raise ValueError("本教学入口至少需要两个观测")
    if not all(isfinite(value) for value in values):
        raise ValueError("收益率必须是有限数值；请先检查缺失或无穷值")

    q25, q50, q75 = quantiles(values, n=4, method="inclusive")
    return {
        "count": len(values),
        "mean": mean(values),
        "median": median(values),
        "q25": q25,
        "q50": q50,
        "q75": q75,
        "variance": pvariance(values),
    }


def main():
    print("data_kind=fictional_teaching; frequency=daily")
    print("return_unit=decimal; variance_unit=decimal_squared")
    print("quantile_method=R7_inclusive; variance_divisor=count; annualized=false")
    examples = {
        "W08D02_A": [0.03, -0.04, 0.12, 0.01, -0.02],
        "W08D02_B_ding": [-0.02, 0.04, -0.02, 0.04],
    }
    for label, returns in examples.items():
        print(f"[{label}]")
        for name, value in describe_returns(returns).items():
            if name == "count":
                print(f"{name}={value}")
            else:
                print(f"{name}={value:.8f}")


if __name__ == "__main__":
    main()
