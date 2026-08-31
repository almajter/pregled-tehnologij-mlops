"""Fetch SI day-ahead prices from Energy-Charts, resample to hourly, store as parquet."""

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pandas as pd
import requests

API_URL = "https://api.energy-charts.info/price"
OUT_PATH = Path("data/raw/prices.parquet")
BACKFILL_YEARS = 3


def fetch_prices(start: str, end: str) -> pd.DataFrame:
    """Prices for [start, end] as hourly means with a UTC datetime index."""
    resp = requests.get(API_URL, params={"bzn": "SI", "start": start, "end": end}, timeout=120)
    resp.raise_for_status()
    data = resp.json()
    index = pd.to_datetime(data["unix_seconds"], unit="s", utc=True).rename("time")
    df = pd.DataFrame({"price": data["price"]}, index=index)
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
