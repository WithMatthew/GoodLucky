import pandas as pd

close = pd.Series(
    [48, 51, 54, 57, 54], index=["D1", "D2", "D3", "D4", "D5"], name="close"
)

total = close + 45
print(total)

D5_total = total.loc["D5"]
print(D5_total)
