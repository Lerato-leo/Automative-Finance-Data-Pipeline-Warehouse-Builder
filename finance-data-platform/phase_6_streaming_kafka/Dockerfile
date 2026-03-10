FROM python:3.11.11-slim-bookworm

WORKDIR /app

ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY kafka_producer.py kafka_consumer.py orchestrator.py trigger_dag_manually.py README.md ./

CMD ["python", "orchestrator.py"]