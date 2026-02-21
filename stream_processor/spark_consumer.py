import os

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json

from ml.anomaly_detector import detect_anomalies
from stream_processor.schema import SENSOR_SCHEMA

KAFKA_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "iot-sensor-data")
PG_URL = "jdbc:postgresql://{}:{}/{}".format(
    os.getenv("POSTGRES_HOST", "localhost"),
    os.getenv("POSTGRES_PORT", "5432"),
    os.getenv("POSTGRES_DB", "iot_pipeline"),
)
PG_USER = os.getenv("POSTGRES_USER", "pipeline_user")
PG_PASSWORD = os.getenv("POSTGRES_PASSWORD", "pipeline_pass")

CHECKPOINT_DIR = "/tmp/spark-checkpoints/iot-pipeline"


def create_spark_session():
    return (
        SparkSession.builder
        .appName("IoT-Sensor-Pipeline")
        .master("local[*]")
        .config(
            "spark.jars.packages",
            "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.5,"
            "org.postgresql:postgresql:42.7.3",
        )
        .config("spark.sql.streaming.forceDeleteTempCheckpointLocation", "true")
        .getOrCreate()
    )


def process_batch(batch_df, batch_id):
    if batch_df.rdd.isEmpty():
        return

    pdf = batch_df.toPandas()
    pdf = detect_anomalies(pdf)
    pdf = pdf.drop(columns=["is_injected_anomaly"], errors="ignore")

    spark = batch_df.sparkSession
    result_df = spark.createDataFrame(pdf)

    (
        result_df.write
        .format("jdbc")
        .option("url", PG_URL)
        .option("dbtable", "sensor_readings")
        .option("user", PG_USER)
        .option("password", PG_PASSWORD)
        .option("driver", "org.postgresql.Driver")
        .mode("append")
        .save()
    )

    anomaly_count = pdf["is_anomaly"].sum()
    print(f"Batch {batch_id}: {len(pdf)} readings, {anomaly_count} anomalies detected")


def main():
    spark = create_spark_session()
    spark.sparkContext.setLogLevel("WARN")

    raw_stream = (
        spark.readStream
        .format("kafka")
        .option("kafka.bootstrap.servers", KAFKA_SERVERS)
        .option("subscribe", KAFKA_TOPIC)
        .option("startingOffsets", "latest")
        .load()
    )

    parsed = (
        raw_stream
        .selectExpr("CAST(value AS STRING) as json_str")
        .select(from_json(col("json_str"), SENSOR_SCHEMA).alias("data"))
        .select("data.*")
    )

    query = (
        parsed.writeStream
        .foreachBatch(process_batch)
        .option("checkpointLocation", CHECKPOINT_DIR)
        .trigger(processingTime="5 seconds")
        .start()
    )

    print("Stream processor started. Waiting for data...")
    query.awaitTermination()


if __name__ == "__main__":
    main()
