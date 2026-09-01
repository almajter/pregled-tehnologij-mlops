"""Fetch SI day-ahead prices from ENTSO-E, resample to hourly, store as parquet."""

import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pandas as pd
from entsoe import EntsoePandasClient

OUT_PATH = Path("data/raw/prices.parquet")
BACKFILL_YEARS = 3


def fetch_prices(start: str, end: str) -> pd.DataFrame:
    """Prices for [start, end] as hourly means with a UTC datetime index."""
    client = EntsoePandasClient(api_key=os.environ["ENTSOE_API_TOKEN"])
    series = client.query_day_ahead_prices(
        "SI",
        start=pd.Timestamp(start, tz="Europe/Ljubljana"),
        end=pd.Timestamp(end, tz="Europe/Ljubljana") + pd.Timedelta(days=1),
    )
    df = series.rename("price").tz_convert("UTC").to_frame()
    df.index = df.index.rename("time")
    # 15-minute resolution since the SDAC switch; hourly rows pass through unchanged
    return df.resample("1h").mean().dropna()


def main() -> None:
    end = datetime.now(UTC).date() - timedelta(days=1)
    start = end.replace(year=end.year - BACKFILL_YEARS)
    df = fetch_prices(str(start), str(end))
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUT_PATH)
    print(f"{len(df)} hourly prices, {df.index[0]} .. {df.index[-1]} -> {OUT_PATH}")


if __name__ == "__main__":
    main()
