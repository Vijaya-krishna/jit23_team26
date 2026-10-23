"""
Exporter module for the Energy-Aware Dynamic Task Scheduling Framework.
Exports simulation results, task details, and fleet metrics to CSV and JSON formats.
"""

import os
import json
import pandas as pd
from typing import List, Dict, Any
from src.simulation.engine import SimulationResult
from src.metrics.performance_metrics import PerformanceMetrics
from src.utils.exceptions import ReportingError


class Exporter:
    """
    Handles file export of simulation datasets, task lifecycles, and comparison summaries.
    """

    @staticmethod
    def export_tasks_to_csv(result: SimulationResult, output_path: str) -> str:
        """Exports all task lifecycles of a simulation run to CSV."""
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            records = [t.to_dict() for t in result.tasks]
            df = pd.DataFrame(records)
            df.to_csv(output_path, index=False)
            return output_path
        except Exception as e:
            raise ReportingError(f"Failed to export tasks to CSV at '{output_path}': {str(e)}")

    @staticmethod
    def export_metrics_to_json(metrics: List[Dict[str, Any]], output_path: str) -> str:
        """Exports experiment comparison metrics to JSON format."""
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(metrics, f, indent=2)
            return output_path
        except Exception as e:
            raise ReportingError(f"Failed to export metrics to JSON at '{output_path}': {str(e)}")

    @staticmethod
    def export_metrics_to_csv(metrics: List[Dict[str, Any]], output_path: str) -> str:
        """Exports experiment comparison metrics to CSV format."""
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            df = pd.DataFrame(metrics)
            df.to_csv(output_path, index=False)
            return output_path
        except Exception as e:
            raise ReportingError(f"Failed to export metrics to CSV at '{output_path}': {str(e)}")

    @staticmethod
    def export_timeseries_to_csv(result: SimulationResult, output_path: str) -> str:
        """Exports power and energy time series data to CSV."""
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            history = result.energy_calculator.history
            df = pd.DataFrame(history)
            df.to_csv(output_path, index=False)
            return output_path
        except Exception as e:
            raise ReportingError(f"Failed to export time series to CSV at '{output_path}': {str(e)}")
