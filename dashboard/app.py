import os
import time

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import psycopg2
import streamlit as st

st.set_page_config(page_title="IoT Sensor Pipeline", layout="wide")


@st.cache_resource
def get_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        dbname=os.getenv("POSTGRES_DB", "iot_pipeline"),
        user=os.getenv("POSTGRES_USER", "pipeline_user"),
        password=os.getenv("POSTGRES_PASSWORD", "pipeline_pass"),
    )


def fetch_recent_data(conn, minutes=5):
    query = """
        SELECT sensor_id, sensor_type, value, unit, timestamp,
               city_zone, is_anomaly, anomaly_score
        FROM sensor_readings
        WHERE timestamp > NOW() - INTERVAL '%s minutes'
        ORDER BY timestamp DESC
    """
    return pd.read_sql(query, conn, params=(minutes,))


def fetch_anomaly_summary(conn):
    query = """
        SELECT sensor_type, city_zone, COUNT(*) as count
        FROM sensor_readings
        WHERE is_anomaly = TRUE
          AND timestamp > NOW() - INTERVAL '10 minutes'
        GROUP BY sensor_type, city_zone
    """
    return pd.read_sql(query, conn)


st.title("Smart City IoT Sensor Dashboard")

refresh = st.sidebar.slider("Refresh interval (seconds)", 2, 30, 5)
window = st.sidebar.slider("Time window (minutes)", 1, 30, 5)

placeholder = st.empty()

while True:
    with placeholder.container():
        try:
            conn = get_connection()
            df = fetch_recent_data(conn, window)
        except Exception as e:
            st.error(f"Database connection failed: {e}")
            st.cache_resource.clear()
            time.sleep(refresh)
            continue

        if df.empty:
            st.info("No data yet. Make sure the pipeline is running.")
            time.sleep(refresh)
            continue

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Readings", f"{len(df):,}")
        col2.metric("Anomalies Detected", int(df["is_anomaly"].sum()))
        col3.metric("Anomaly Rate", f"{df['is_anomaly'].mean() * 100:.1f}%")
        col4.metric("Active Sensors", df["sensor_id"].nunique())

        st.divider()

        sensor_types = ["temperature", "humidity", "air_quality", "traffic"]
        unit_labels = {
            "temperature": "Celsius",
            "humidity": "Percent",
            "air_quality": "AQI",
            "traffic": "Vehicles/min",
        }

        left, right = st.columns(2)
        for i, sensor_type in enumerate(sensor_types):
            subset = df[df["sensor_type"] == sensor_type].copy()
            if subset.empty:
                continue

            subset["status"] = subset["is_anomaly"].map({True: "Anomaly", False: "Normal"})

            fig = px.scatter(
                subset,
                x="timestamp",
                y="value",
                color="status",
                color_discrete_map={"Normal": "#636EFA", "Anomaly": "#EF553B"},
                title=sensor_type.replace("_", " ").title(),
                labels={"value": unit_labels.get(sensor_type, ""), "timestamp": ""},
            )
            fig.update_layout(height=300, margin=dict(t=40, b=20))

            target = left if i % 2 == 0 else right
            target.plotly_chart(fig, use_container_width=True)

        st.divider()

        col_left, col_right = st.columns(2)

        with col_left:
            st.subheader("Recent Anomalies")
            anomalies = df[df["is_anomaly"]].head(15)
            if not anomalies.empty:
                st.dataframe(
                    anomalies[["timestamp", "sensor_id", "sensor_type", "value", "city_zone", "anomaly_score"]],
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.info("No anomalies in current window.")

        with col_right:
            st.subheader("Anomaly Heatmap")
            summary = fetch_anomaly_summary(conn)
            if not summary.empty:
                pivot = summary.pivot_table(index="sensor_type", columns="city_zone", values="count", fill_value=0)
                fig = px.imshow(
                    pivot,
                    color_continuous_scale="Reds",
                    title="Anomalies by Sensor Type & Zone (last 10 min)",
                )
                fig.update_layout(height=300, margin=dict(t=40, b=20))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No anomaly data for heatmap yet.")

    time.sleep(refresh)
