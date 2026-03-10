FROM python:3.11.11-slim-bookworm

WORKDIR /app

ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY etl_main.py .
COPY warehouse_conn_example.env .

CMD ["python", "etl_main.py"]