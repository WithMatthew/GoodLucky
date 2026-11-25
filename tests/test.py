import pandas as pd

prices = pd.DataFrame(
    {
        "SPY": [100.0, 110.0, 99.0],
        "TLT": [100.0, 98.0, 102.9],
    },
    index=["D1", "D2", "D3"],
)

returns = prices.pct_change()
print(returns)
