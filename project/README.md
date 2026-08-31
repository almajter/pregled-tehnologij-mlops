# price-forecaster

Day-ahead electricity price forecasting for the Slovenian bidding zone (SI).
The MLOps pipeline artifact for the thesis in `../thesis`.

## Setup

```sh
uv sync
```

## Pipeline

DVC pipeline with two stages, see `dvc.yaml`:

```sh
uv run dvc repro
```

- **ingest** — fetches ~3 years of SI day-ahead prices from the
  [Energy-Charts API](https://api.energy-charts.info) and writes
  `data/raw/prices.parquet` (UTC index, hourly EUR/MWh; 15-minute data since
  the SDAC switch is resampled to hourly means)
- **evaluate** — naive lag-24 baseline (price tomorrow at hour h = price today
  at hour h), writes MAE/RMSE to `metrics.json`

Stages can also run standalone:

```sh
uv run python -m price_forecaster.ingest
uv run python -m price_forecaster.evaluate
```

## Current baseline

```json
{ "model": "naive-lag24", "mae": 25.03, "rmse": 42.5 }
```

Everything that comes later has to beat this.
