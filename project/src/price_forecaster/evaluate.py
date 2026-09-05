"""Walk-forward comparison: train up to month M, score month M+1, slide forward.

Writes metrics.json with MAE/RMSE per candidate, MAE relative to the lag-24
naive, and the name of the best trainable candidate for the train stage.
"""

import json
import os
from pathlib import Path

import mlflow
import pandas as pd

from price_forecaster.train import MODEL_NAME, candidates

MIN_TRAIN_MONTHS = 12
METRICS_PATH = Path("metrics.json")


def score(pred, actual) -> dict:
    error = actual - pred
    return {
        "mae": round(float(error.abs().mean()), 2),
        "rmse": round(float((error**2).mean() ** 0.5), 2),
    }


def main() -> None:
    mlflow.set_tracking_uri(
        os.environ.get("MLFLOW_TRACKING_URI", "http://localhost:5001")
    )
    mlflow.set_experiment(MODEL_NAME)

    df = pd.read_parquet("data/features.parquet")
    months = pd.Index(df.index.strftime("%Y-%m"))
    folds = months.unique()[MIN_TRAIN_MONTHS:]
    test = df[months >= folds[0]]
    test_months = months[months >= folds[0]]
    actual = test["price"]

    predictions = {"naive-lag24": test["lag_24"], "naive-lag168": test["lag_168"]}
    for name, model in candidates().items():
        preds = []
        for month in folds:
            train, fold = df[months < month], df[months == month]
            model.fit(train.drop(columns="price"), train["price"])
            preds.append(
                pd.Series(model.predict(fold.drop(columns="price")), fold.index)
            )
        predictions[name] = pd.concat(preds)

    metrics = {}
    for name, pred in predictions.items():
        metrics[name] = score(pred, actual)
        with mlflow.start_run(run_name=f"eval-{name}"):
            mlflow.log_metrics(metrics[name])
            for i, month in enumerate(folds):
                fold = test_months == month
                mlflow.log_metric(
                    "fold_mae", score(pred[fold], actual[fold])["mae"], step=i
                )

    naive_mae = metrics["naive-lag24"]["mae"]
    for m in metrics.values():
        m["relative_mae"] = round(m["mae"] / naive_mae, 3)
    metrics["best"] = min(candidates(), key=lambda n: metrics[n]["mae"])
    metrics["folds"] = len(folds)

    METRICS_PATH.write_text(json.dumps(metrics, indent=2) + "\n")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
