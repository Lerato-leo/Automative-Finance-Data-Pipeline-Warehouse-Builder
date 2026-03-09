FROM apache/airflow:2.7.3-python3.11

USER root

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && apt-get clean

USER airflow

# Copy and install Python requirements
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --user -r /tmp/requirements.txt

# Ensure psycopg2-binary is installed
RUN pip install --no-cache-dir --user psycopg2-binary==2.9.9
