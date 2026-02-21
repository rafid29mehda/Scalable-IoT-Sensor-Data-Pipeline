import os

import joblib
import numpy as np
import pandas as pd

MODEL_DIR = os.path.join(os.path.dirname(__file__), "model")

_model_cache = {}


def _get_model(sensor_type):
    if sensor_type not in _model_cache:
        path = os.path.join(MODEL_DIR, f"{sensor_type}_isolation_forest.joblib")
        _model_cache[sensor_type] = joblib.load(path)
    return _model_cache[sensor_type]


def detect_anomalies(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["is_anomaly"] = False
    df["anomaly_score"] = 0.0

    timestamps = pd.to_datetime(df["timestamp"])
    hour = timestamps.dt.hour + timestamps.dt.minute / 60

    for sensor_type in df["sensor_type"].unique():
        mask = df["sensor_type"] == sensor_type
        subset = df.loc[mask].copy()

        if subset.empty:
            continue

        model = _get_model(sensor_type)

        subset = subset.sort_values("timestamp")
        values = subset["value"].values
        hours = hour[subset.index].values

        if len(values) > 1:
            diffs = np.diff(values, prepend=values[0])
            rate_of_change = diffs * 0.3
        else:
            rate_of_change = np.zeros(len(values))

        features = np.column_stack([values, hours, rate_of_change])

        predictions = model.predict(features)
        scores = model.decision_function(features)

        df.loc[subset.index, "is_anomaly"] = predictions == -1
        df.loc[subset.index, "anomaly_score"] = scores

    return df
