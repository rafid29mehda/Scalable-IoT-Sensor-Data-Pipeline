import json
import math
import random
import signal
import sys
import time
from datetime import datetime, timezone

from confluent_kafka import Producer

from data_generator.config import (
    ANOMALY_PROBABILITY,
    CITY_ZONES,
    GENERATION_INTERVAL_SEC,
    KAFKA_BOOTSTRAP_SERVERS,
    KAFKA_TOPIC,
    NUM_SENSORS_PER_TYPE,
    SENSOR_CONFIGS,
)

running = True


def handle_shutdown(signum, frame):
    global running
    running = False
    print("\nShutting down sensor simulator...")


def build_sensor_registry():
    sensors = []
    for sensor_type, config in SENSOR_CONFIGS.items():
        for i in range(NUM_SENSORS_PER_TYPE):
            zone = CITY_ZONES[i % len(CITY_ZONES)]
            sensor_id = f"{sensor_type[:4]}-{zone}-{i+1:03d}"
            sensors.append({
                "sensor_id": sensor_id,
                "sensor_type": sensor_type,
                "unit": config["unit"],
                "city_zone": zone,
                "config": config,
                "phase_offset": random.uniform(0, 2 * math.pi),
            })
    return sensors


def generate_reading(sensor, now):
    config = sensor["config"]
    lo, hi = config["normal_range"]
    midpoint = (lo + hi) / 2
    amplitude = (hi - lo) / 2

    hour_fraction = now.hour + now.minute / 60
    daily_cycle = math.sin(2 * math.pi * hour_fraction / 24 + sensor["phase_offset"])
    base_value = midpoint + amplitude * 0.6 * daily_cycle
    noise = random.gauss(0, config["noise_std"])
    value = base_value + noise

    is_anomaly = random.random() < ANOMALY_PROBABILITY
    if is_anomaly:
        ano_lo, ano_hi = config["anomaly_range"]
        value = random.uniform(ano_lo, ano_hi)

    return {
        "sensor_id": sensor["sensor_id"],
        "sensor_type": sensor["sensor_type"],
        "value": round(value, 2),
        "unit": sensor["unit"],
        "timestamp": now.isoformat(),
        "city_zone": sensor["city_zone"],
        "is_injected_anomaly": is_anomaly,
    }


def delivery_callback(err, msg):
    if err:
        print(f"Delivery failed: {err}")


def main():
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)

    producer = Producer({
        "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
        "client.id": "iot-sensor-simulator",
    })

    sensors = build_sensor_registry()
    print(f"Starting simulator with {len(sensors)} sensors")
    print(f"Publishing to topic '{KAFKA_TOPIC}' at {KAFKA_BOOTSTRAP_SERVERS}")
    print(f"Anomaly injection rate: {ANOMALY_PROBABILITY*100:.0f}%")

    msg_count = 0
    while running:
        now = datetime.now(timezone.utc)
        for sensor in sensors:
            reading = generate_reading(sensor, now)
            producer.produce(
                KAFKA_TOPIC,
                key=sensor["sensor_id"],
                value=json.dumps(reading).encode("utf-8"),
                callback=delivery_callback,
            )
            msg_count += 1

        producer.poll(0)

        if msg_count % 100 == 0:
            print(f"Published {msg_count} messages")

        time.sleep(GENERATION_INTERVAL_SEC)

    producer.flush(timeout=5)
    print(f"Simulator stopped. Total messages sent: {msg_count}")


if __name__ == "__main__":
    main()
