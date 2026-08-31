# price-forecaster

Day-ahead electricity price forecasting for the Slovenian bidding zone (SI).
The MLOps pipeline artifact for the thesis in `../thesis`.

## Setup

```sh
uv sync
```

## Pipeline

DVC pipeline with three stages, see `dvc.yaml`:

```sh
uv run dvc repro
```

- **ingest** — fetches ~3 years of SI day-ahead prices from the
  [Energy-Charts API](https://api.energy-charts.info) and writes
  `data/raw/prices.parquet` (UTC index, hourly EUR/MWh; 15-minute data since
  the SDAC switch is resampled to hourly means)
- **features** — calendar features (hour, day-of-week, month, weekend, SI
  holidays; local time) plus lagged prices (lag-24, lag-168, 7-day rolling
  mean), writes `data/features.parquet`
- **train** — trains Ridge and LightGBM, scores them and the naive lag-24
  baseline (price tomorrow at hour h = price today at hour h) on the last
  90 days, saves `models/model.pkl` and writes `metrics.json`

Stages can also run standalone, e.g. `uv run python -m price_forecaster.train`.

## Current results

MAE / RMSE in EUR/MWh on the 90-day holdout:

```json
{
  "naive-lag24": { "mae": 29.95, "rmse": 54.65 },
  "ridge":       { "mae": 25.62, "rmse": 45.47 },
  "lightgbm":    { "mae": 27.54, "rmse": 48.10 }
}
```

Both models beat the naive baseline. LightGBM is untuned and currently loses
to Ridge — tuning comes with experiment tracking.
