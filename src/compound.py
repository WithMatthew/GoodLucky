"""第 1 周第 3 天：用虚构收益率演示复利，不连接行情或账户。

在仓库根目录运行：python src/compound.py
仅使用 Python 标准库，已验证环境为 Python 3.11.9。
"""


def compound_value(principal, returns):
    """按期更新金额，返回最后一期结束时的价值。

    principal：期初本金，单位为元。
    returns：按时间先后排列的各期收益率，例如 0.10 表示上涨 10%。

    教学条件：没有追加或取出资金、费用与分红，全部资金留在投资中。
    输入约定：本金为有限的非负数，各期收益率为有限数且不低于 -1；
    本入门示例不额外检查输入。空收益率序列表示尚未经历任何一期。
    使用浮点数计算，展示时才保留两位小数，不作为精确货币结算工具。
    """
    value = principal
    for rate in returns:
        value = value * (1 + rate)
    return value


if __name__ == "__main__":
    scenarios = {"A": [0.10, -0.10], "B": [-0.20, 0.25]}
    for label, rates in scenarios.items():
        final_value = compound_value(1000, rates)
        print(f"{label}: {final_value:.2f}")
