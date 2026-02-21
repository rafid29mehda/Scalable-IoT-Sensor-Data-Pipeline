import os
import numpy as np
import pandas as pd
import pytest

from ml.train_model import train_models, MODEL_DIR
from ml.anomaly_detector import detect_anomalies


@pytest.fixture(scope="module", autouse=True)
def ensure_models_exist():
    if not os.path.exists(os.path.join(MODEL_DIR, "temperature_isolation_forest.joblib")):
        train_models()


def make_test_df(sensor_type, values):
    return pd.DataFrame({
        "sensor_id": [f"test-001"] * len(values),
        "sensor_type": [sensor_type] * len(values),
        "value": values,
        "unit": ["test"] * len(values),
        "timestamp": pd.date_range("2026-01-01 12:00", periods=len(values), freq="s"),
        "city_zone": ["zone-north"] * len(values),
    })


def test_normal_temperature_not_flagged():
    df = make_test_df("temperature", [22.0, 23.5, 24.0, 25.1, 22.8])
    result = detect_anomalies(df)
    assert result["is_anomaly"].sum() <= 1


def test_extreme_temperature_flagged():
    df = make_test_df("temperature", [55.0, -10.0, 50.0, -5.0])
    result = detect_anomalies(df)
    assert result["is_anomaly"].sum() >= 2


def test_output_has_required_columns():
    df = make_test_df("humidity", [50.0, 51.0, 49.0])
    result = detect_anomalies(df)
    assert "is_anomaly" in result.columns
    assert "anomaly_score" in result.columns
