"""Naive baseline: price at hour h tomorrow = price at hour h today (lag-24)."""

import json
from pathlib import Path

import pandas as pd

METRICS_PATH = Path("metrics.json")


def main() -> None:
    df = pd.read_parquet("data/raw/prices.parquet")
    error = (df["price"] - df["price"].shift(24)).dropna()
    metrics = {
        "model": "naive-lag24",
        "mae": round(float(error.abs().mean()), 2),
        "rmse": round(float((error**2).mean() ** 0.5), 2),
    }
    METRICS_PATH.write_text(json.dumps(metrics, indent=2) + "\n")
    print(metrics)


if __name__ == "__main__":
    main()
