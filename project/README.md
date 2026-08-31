# price-forecaster

Day-ahead electricity price forecasting for the Slovenian bidding zone (SI).
The MLOps pipeline artifact for the thesis in `../thesis`.

## Setup

```sh
uv sync
docker compose up -d   # MLflow + Postgres + MinIO + the serving API
```

MLflow UI: <http://localhost:5001> (5001 because macOS AirPlay sits on 5000).
MinIO console: <http://localhost:9001> (minio / minio123). MLflow stores runs
in Postgres and artifacts in the MinIO `mlflow` bucket; DVC pushes data and
models to the `dvc` bucket; everything stays in Docker volumes.

## Pipeline

DVC pipeline with three stages, see `dvc.yaml`:

```sh
uv run dvc repro
uv run dvc push   # upload data + model to the MinIO remote
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
  90 days, saves `models/model.pkl` and writes `metrics.json`; each model is
  logged as an MLflow run in the `price-forecaster` experiment (override the
  server with `MLFLOW_TRACKING_URI`); the LightGBM model is registered as
  `price-forecaster` and promoted to the `production` alias

## Serving

The `api` service in the compose stack serves on <http://localhost:8000>; it
loads `models:/price-forecaster@production` from the registry at startup, so
it needs a trained model (`dvc repro`) before its first start. For local
development run it outside Docker:

```sh
uv run uvicorn price_forecaster.api:app --port 8000
```

- `GET /forecast` — tomorrow's 24 hourly prices (EUR/MWh); features are built
  from live Energy-Charts data, every response is appended to
  `data/forecasts.jsonl` for later predictions-vs-actuals evaluation
- `GET /health` — status + served model version

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
