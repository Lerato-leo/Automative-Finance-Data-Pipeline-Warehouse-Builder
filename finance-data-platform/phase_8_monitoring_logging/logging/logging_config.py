"""Shared logging helpers for the automotive finance pipeline."""

from __future__ import annotations

import logging
import os
import sys
from typing import Any


class PipelineContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.pipeline_name = getattr(record, "pipeline_name", "automotive_finance_pipeline")
        record.dag_id = getattr(record, "dag_id", os.getenv("AIRFLOW_CTX_DAG_ID", "local"))
        record.task_id = getattr(record, "task_id", os.getenv("AIRFLOW_CTX_TASK_ID", "standalone"))
        return True


def configure_pipeline_logger(name: str, level: str | int = "INFO") -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | dag=%(dag_id)s | task=%(task_id)s | pipeline=%(pipeline_name)s | %(message)s"
        )
    )
    handler.addFilter(PipelineContextFilter())

    logger.handlers.clear()
    logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False
    return logger


def log_quality_metrics(
    logger: logging.Logger,
    *,
    file_name: str,
    file_type: str,
    table_name: str,
    metrics: dict[str, Any],
) -> None:
    logger.info(
        "Data quality metrics | file_name=%s | file_type=%s | table_name=%s | row_count=%s | total_null_values=%s | duplicate_records=%s | schema_valid=%s | missing_required_columns=%s | validation_errors=%s",
        file_name,
        file_type,
        table_name,
        metrics.get("row_count", 0),
        metrics.get("total_null_values", 0),
        metrics.get("duplicate_records", 0),
        metrics.get("schema_validation", {}).get("is_valid", False),
        metrics.get("schema_validation", {}).get("missing_required_columns", []),
        metrics.get("validation_errors", []),
    )