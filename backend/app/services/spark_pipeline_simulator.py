from __future__ import annotations

from datetime import datetime, timezone


class SparkPipelineSimulator:
    """Storytelling-friendly big-data mode simulator for hackathon demos."""

    def simulate(self, documents: list[dict]) -> dict:
        partitions = max(2, min(8, len(documents)))
        return {
            "engine": "spark-simulator",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "job_status": "completed",
            "partitions": partitions,
            "delta_tables": [
                {"table": "bronze_documents", "rows": len(documents)},
                {"table": "silver_extractions", "rows": len(documents)},
                {"table": "gold_credit_features", "rows": max(1, len(documents) // 2)},
            ],
            "execution_log": [
                "Initialized mock Databricks session",
                "Loaded raw borrower documents into bronze layer",
                "Applied extraction and normalization into silver layer",
                "Built feature vectors and compliance joins into gold layer",
            ],
        }
