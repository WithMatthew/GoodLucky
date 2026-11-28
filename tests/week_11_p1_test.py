import pandas as pd

total = pd.Series(
    [100, 100, 100, 102, 99], index=["D1", "D2", "D3", "D4", "D5"], name="total"
)
r = total.pct_change().rename("r")

nav = (1 + r).cumprod().rename("nav")

cum_ret = (nav - 1).rename("cum_ret")

print(nav.loc["D5"], total.loc["D5"] / total.loc["D1"])


close = pd.Series(
    [45, 48, 51, 54, 51], index=["D1", "D2", "D3", "D4", "D5"], name="close"
)

ma3 = close.rolling(3).mean()
ma3 = ma3.rename("ma3")
print(ma3)

gap = (close - ma3).rename("gap")
print(gap)

above = close > ma3
target = above.astype(int).rename("target")
print(target)

position = target.shift(1).rename("position")
print(position)
