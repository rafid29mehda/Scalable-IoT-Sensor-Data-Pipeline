from datetime import datetime, timezone

from data_generator.config import SENSOR_CONFIGS, ANOMALY_PROBABILITY
from data_generator.sensor_simulator import build_sensor_registry, generate_reading


def test_sensor_registry_count():
    sensors = build_sensor_registry()
    expected = len(SENSOR_CONFIGS) * 3
    assert len(sensors) == expected


def test_sensor_registry_fields():
    sensors = build_sensor_registry()
    for s in sensors:
        assert "sensor_id" in s
        assert "sensor_type" in s
        assert s["sensor_type"] in SENSOR_CONFIGS


def test_generate_reading_structure():
    sensors = build_sensor_registry()
    now = datetime.now(timezone.utc)
    reading = generate_reading(sensors[0], now)

    required_keys = {"sensor_id", "sensor_type", "value", "unit", "timestamp", "city_zone", "is_injected_anomaly"}
    assert required_keys == set(reading.keys())
    assert isinstance(reading["value"], float)


def test_readings_within_plausible_range():
    sensors = build_sensor_registry()
    now = datetime.now(timezone.utc)

    for sensor in sensors:
        config = sensor["config"]
        all_bounds = config["normal_range"] + config["anomaly_range"]
        lo = min(all_bounds)
        hi = max(all_bounds)
        for _ in range(100):
            reading = generate_reading(sensor, now)
            assert lo - 20 <= reading["value"] <= hi + 20
