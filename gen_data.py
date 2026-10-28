"""Generates SIMULATED hourly campus electricity data -> data.csv (say this is simulated in the demo)."""
import numpy as np, pandas as pd
rng = np.random.default_rng(42)
hours = pd.date_range("2026-09-01", periods=30*24, freq="h")
rows = []
for b in ["Library", "Hostel", "Lab Block", "Canteen"]:
    for t in hours:
        h, wd = t.hour, t.weekday()
        weekend = wd >= 5
        if b == "Library":
            base = 4 + (22 if (8 <= h <= 20 and not weekend) else 0)
            if weekend and 8 <= h <= 20: base += 14          # weekend waste: AC/lights on
        elif b == "Hostel":
            base = 10 + (14 if (18 <= h <= 23 or 5 <= h <= 8) else 0)
        elif b == "Lab Block":
            base = 6 + (35 if (9 <= h <= 17 and not weekend) else 0)
            if h >= 22 or h <= 5: base += 16                  # night waste: equipment/AC left on
        else:  # Canteen
            base = 5 + (18 if (7 <= h <= 20) else 0)
        v = base * rng.normal(1, 0.06)
        if b == "Canteen" and t.day == 17 and 13 <= h <= 15: v *= 2.6   # spike
        if b == "Library" and t.day == 9 and 2 <= h <= 4: v += 28       # spike
        rows.append((t, b, round(max(v, 0.5), 2)))
pd.DataFrame(rows, columns=["timestamp", "building", "kwh"]).to_csv("data.csv", index=False)
print("data.csv created:", len(rows), "rows")
