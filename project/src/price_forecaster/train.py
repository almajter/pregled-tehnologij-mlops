"""Fit the walk-forward winner from metrics.json on all data and promote it."""

import json
import os
from pathlib import Path

import mlflow
import pandas as pd
from lightgbm import LGBMRegressor
from sklearn.compose import make_column_transformer
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder

MODEL_NAME = "price-forecaster"
CALENDAR = ["hour", "dayofweek", "month"]
LGBM_PARAMS = {"n_estimators": 500, "learning_rate": 0.05}


def candidates() -> dict:
    onehot = make_column_transformer(
        (OneHotEncoder(), CALENDAR), remainder="passthrough"
    )
    return {
        "ridge": make_pipeline(onehot, Ridge()),
        "lightgbm": LGBMRegressor(**LGBM_PARAMS, verbose=-1),
    }


def main() -> None:
    mlflow.set_tracking_uri(
        os.environ.get("MLFLOW_TRACKING_URI", "http://localhost:5001")
    )
    mlflow.set_experiment(MODEL_NAME)

    df = pd.read_parquet("data/features.parquet")
    best = json.loads(Path("metrics.json").read_text())["best"]

    with mlflow.start_run(run_name=f"train-{best}"):
        model = candidates()[best].fit(df.drop(columns="price"), df["price"])
        flavor = mlflow.lightgbm if best == "lightgbm" else mlflow.sklearn
        info = flavor.log_model(model, name="model", registered_model_name=MODEL_NAME)
        mlflow.MlflowClient().set_registered_model_alias(
            MODEL_NAME, "production", info.registered_model_version
        )
    print(f"{best} -> {MODEL_NAME} v{info.registered_model_version} @production")


if __name__ == "__main__":
    main()
