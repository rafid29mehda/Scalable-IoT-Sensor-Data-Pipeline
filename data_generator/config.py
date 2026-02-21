import os

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "iot-sensor-data")

CITY_ZONES = ["zone-north", "zone-south", "zone-east", "zone-west", "zone-central"]

SENSOR_CONFIGS = {
    "temperature": {
        "unit": "celsius",
        "normal_range": (15.0, 35.0),
        "anomaly_range": (-10.0, 55.0),
        "noise_std": 0.5,
    },
    "humidity": {
        "unit": "percent",
        "normal_range": (30.0, 70.0),
        "anomaly_range": (0.0, 100.0),
        "noise_std": 1.0,
    },
    "air_quality": {
        "unit": "aqi",
        "normal_range": (20.0, 100.0),
        "anomaly_range": (150.0, 500.0),
        "noise_std": 3.0,
    },
    "traffic": {
        "unit": "vehicles_per_min",
        "normal_range": (5.0, 60.0),
        "anomaly_range": (0.0, 200.0),
        "noise_std": 2.0,
    },
}

ANOMALY_PROBABILITY = 0.05
NUM_SENSORS_PER_TYPE = 3
GENERATION_INTERVAL_SEC = 0.5
