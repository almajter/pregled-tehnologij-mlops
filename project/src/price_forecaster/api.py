"""FastAPI service: forecast tomorrow's 24 hourly day-ahead prices for SI."""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import mlflow
import pandas as pd
from fastapi import FastAPI

from price_forecaster.features import build_features
from price_forecaster.ingest import fetch_prices

TZ = ZoneInfo("Europe/Ljubljana")
MODEL_NAME = "price-forecaster"
FORECAST_LOG = Path("data/forecasts.jsonl")

# the server presigns download URLs against minio's in-network hostname,
# which the host can't resolve — keep downloads proxied through the server
os.environ.setdefault("MLFLOW_ENABLE_PROXY_MULTIPART_DOWNLOAD", "false")
mlflow.set_tracking_uri(os.environ.get("MLFLOW_TRACKING_URI", "http://localhost:5001"))
model = mlflow.pyfunc.load_model(f"models:/{MODEL_NAME}@production")
model_version = (
    mlflow.MlflowClient().get_model_version_by_alias(MODEL_NAME, "production").version
)

app = FastAPI(title=MODEL_NAME)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "model_version": model_version}


@app.get("/forecast")
def forecast() -> dict:
    today = datetime.now(TZ).date()
    hours = pd.date_range(
        str(today + timedelta(days=1)), periods=24, freq="1h", tz=TZ
    ).tz_convert("UTC")

    # today's prices were published yesterday, so lag-24 is known for tomorrow
    history = fetch_prices(str(today - timedelta(days=9)), str(today))
    frame = pd.concat([history, pd.DataFrame(index=hours)])
    features = build_features(frame).loc[hours].drop(columns="price")

    result = {
        "date": str(today + timedelta(days=1)),
        "unit": "EUR/MWh",
        "model_version": model_version,
        "prices": {
            h.isoformat(): round(float(p), 2)
            for h, p in zip(hours, model.predict(features), strict=True)
        },
    }
    with FORECAST_LOG.open("a") as f:
        f.write(json.dumps(result) + "\n")
    return result
