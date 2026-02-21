import os
import math

import numpy as np
from sklearn.ensemble import IsolationForest
import joblib

from data_generator.config import SENSOR_CONFIGS

MODEL_DIR = os.path.join(os.path.dirname(__file__), "model")

SENSOR_TYPE_INDEX = {name: i for i, name in enumerate(SENSOR_CONFIGS)}


def generate_normal_samples(sensor_type, config, n_samples=5000):
    lo, hi = config["normal_range"]
    midpoint = (lo + hi) / 2
    std = (hi - lo) / 6

    values = np.random.normal(midpoint, std, n_samples)
    hours = np.random.uniform(0, 24, n_samples)
    rate_of_change = np.random.normal(0, config["noise_std"] * 0.5, n_samples)

    return np.column_stack([values, hours, rate_of_change])


def train_models():
    os.makedirs(MODEL_DIR, exist_ok=True)

    for sensor_type, config in SENSOR_CONFIGS.items():
        X = generate_normal_samples(sensor_type, config)

        model = IsolationForest(
            n_estimators=100,
            contamination=0.05,
            random_state=42,
        )
        model.fit(X)

        path = os.path.join(MODEL_DIR, f"{sensor_type}_isolation_forest.joblib")
        joblib.dump(model, path)
        print(f"Trained and saved model for '{sensor_type}' -> {path}")

    print("All models trained successfully.")


if __name__ == "__main__":
    train_models()
