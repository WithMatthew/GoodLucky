import pandas as pd

total = pd.Series(
    [100, 100, 100, 102, 99], index=["D1", "D2", "D3", "D4", "D5"], name="total"
)
r = total.pct_change().rename("r")

nav = (1 + r).cumprod().rename("nav")

cum_ret = (nav - 1).rename("cum_ret")

print(nav.loc["D5"], total.loc["D5"] / total.loc["D1"])
