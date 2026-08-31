"""Build the feature table: calendar features + lagged prices."""

from pathlib import Path

import holidays
import pandas as pd

OUT_PATH = Path("data/features.parquet")


def main() -> None:
    df = pd.read_parquet("data/raw/prices.parquet")
    local = df.index.tz_convert("Europe/Ljubljana")
    si_holidays = holidays.SI()

    df["hour"] = local.hour
    df["dayofweek"] = local.dayofweek
    df["month"] = local.month
    df["is_weekend"] = (local.dayofweek >= 5).astype(int)
    df["is_holiday"] = [int(d in si_holidays) for d in local.date]
    df["lag_24"] = df["price"].shift(24)
    df["lag_168"] = df["price"].shift(168)
    df["roll_7d_mean"] = df["price"].shift(24).rolling(168).mean()

    df = df.dropna()
    df.to_parquet(OUT_PATH)
    print(f"{len(df)} rows, {df.shape[1] - 1} features -> {OUT_PATH}")


if __name__ == "__main__":
    main()
