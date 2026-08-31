"""Train Ridge and LightGBM, compare against the naive lag-24 baseline on a holdout."""

import json
from pathlib import Path

import joblib
import pandas as pd
from lightgbm import LGBMRegressor
from sklearn.linear_model import Ridge

TEST_DAYS = 90
MODEL_PATH = Path("models/model.pkl")
METRICS_PATH = Path("metrics.json")


def score(pred, actual) -> dict:
    error = actual - pred
    return {
        "mae": round(float(error.abs().mean()), 2),
        "rmse": round(float((error**2).mean() ** 0.5), 2),
    }


def main() -> None:
    df = pd.read_parquet("data/features.parquet")
    split = len(df) - TEST_DAYS * 24
    train, test = df.iloc[:split], df.iloc[split:]
    X_train, y_train = train.drop(columns="price"), train["price"]
    X_test, y_test = test.drop(columns="price"), test["price"]

    metrics = {"naive-lag24": score(test["lag_24"], y_test)}

    ridge = Ridge().fit(X_train, y_train)
    metrics["ridge"] = score(ridge.predict(X_test), y_test)

    lgbm = LGBMRegressor(n_estimators=500, learning_rate=0.05, verbose=-1)
    lgbm.fit(X_train, y_train)
    metrics["lightgbm"] = score(lgbm.predict(X_test), y_test)

    MODEL_PATH.parent.mkdir(exist_ok=True)
    joblib.dump(lgbm, MODEL_PATH)
    METRICS_PATH.write_text(json.dumps(metrics, indent=2) + "\n")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
