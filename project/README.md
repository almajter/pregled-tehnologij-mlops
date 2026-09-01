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
in Postgres and artifacts in the MinIO `mlflow` bucket; DVC pushes data to the
`dvc` bucket; everything stays in Docker volumes.

## Pipeline

DVC pipeline with three stages, see `dvc.yaml`:

```sh
uv run dvc repro
uv run dvc push   # upload data to the MinIO remote
```

- **ingest** — fetches ~3 years of SI day-ahead prices from the ENTSO-E
  Transparency API (`ENTSOE_API_TOKEN`) and writes `data/raw/prices.parquet`
  (UTC index, hourly EUR/MWh; 15-minute data since the SDAC switch is
  resampled to hourly means)
- **features** — calendar features (hour, day-of-week, month, weekend, SI
  holidays; local time) plus lagged prices (lag-24, lag-168, 7-day rolling
  mean), writes `data/features.parquet`
- **train** — trains Ridge and LightGBM, scores them and the naive lag-24
  baseline (price tomorrow at hour h = price today at hour h) on the last
  90 days and writes `metrics.json`; each model is logged as an MLflow run in
  the `price-forecaster` experiment (override the server with
  `MLFLOW_TRACKING_URI`); the LightGBM model is registered as
  `price-forecaster` and promoted to the `production` alias

Current numbers live in `metrics.json` and in MLflow.

## Serving

The `api` service in the compose stack serves on <http://localhost:8000>; it
loads `models:/price-forecaster@production` from the registry at startup, so
it needs a trained model (`dvc repro`) before its first start. For local
development run it outside Docker:

```sh
uv run uvicorn price_forecaster.api:app --port 8000
```

- `GET /forecast` — tomorrow's 24 hourly prices (EUR/MWh); features are built
  from live ENTSO-E data, every response is appended to `data/forecasts.jsonl`
  for later predictions-vs-actuals evaluation
- `GET /health` — status + served model version

Stages can also run standalone, e.g. `uv run python -m price_forecaster.train`.

## Deployment

On the homelab the platform (mlops-01) runs `docker compose up -d postgres
minio minio-init mlflow` from this compose file with its credentials in a
`.env` next to it — see `.env.example`. Runbooks live in the homelab wiki.

The API (forecast-01) deploys from CI and keeps no repo, compose file or
secrets on the host: a push to `main` is mirrored to GitLab, where
`.gitlab-ci.yml` builds the api image, pushes it to `registry.alters.si` and
sshes a forced command to forecast-01 with the job token, `ENTSOE_API_TOKEN`
and `MLFLOW_TRACKING_URI` on stdin; the command pulls the image and
`docker run`s it with those in its environment, then CI checks `/health`.
