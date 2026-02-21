JAVA_HOME := $(shell /usr/libexec/java_home -v 17 2>/dev/null)
export JAVA_HOME

.PHONY: up down generate stream train dashboard clean

up:
	docker compose up -d

down:
	docker compose down

train:
	python -m ml.train_model

generate:
	python -m data_generator.sensor_simulator

stream:
	python -m stream_processor.spark_consumer

dashboard:
	streamlit run dashboard/app.py

test:
	pytest tests/ -v

clean:
	docker compose down -v
	rm -rf /tmp/spark-checkpoints/iot-pipeline
