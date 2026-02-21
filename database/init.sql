CREATE TABLE IF NOT EXISTS sensor_readings (
    id              BIGSERIAL PRIMARY KEY,
    sensor_id       VARCHAR(50) NOT NULL,
    sensor_type     VARCHAR(30) NOT NULL,
    value           DOUBLE PRECISION NOT NULL,
    unit            VARCHAR(20) NOT NULL,
    timestamp       TIMESTAMP NOT NULL,
    city_zone       VARCHAR(50) NOT NULL,
    is_anomaly      BOOLEAN DEFAULT FALSE,
    anomaly_score   DOUBLE PRECISION,
    processed_at    TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_readings_timestamp ON sensor_readings (timestamp DESC);
CREATE INDEX idx_readings_anomaly ON sensor_readings (is_anomaly) WHERE is_anomaly = TRUE;
CREATE INDEX idx_readings_type ON sensor_readings (sensor_type);
