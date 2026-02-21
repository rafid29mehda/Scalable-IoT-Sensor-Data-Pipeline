from pyspark.sql.types import (
    BooleanType,
    DoubleType,
    StringType,
    StructField,
    StructType,
)

SENSOR_SCHEMA = StructType([
    StructField("sensor_id", StringType(), False),
    StructField("sensor_type", StringType(), False),
    StructField("value", DoubleType(), False),
    StructField("unit", StringType(), False),
    StructField("timestamp", StringType(), False),
    StructField("city_zone", StringType(), False),
    StructField("is_injected_anomaly", BooleanType(), True),
])
