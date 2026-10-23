"""
Unit tests for the Exporter and ReportGenerator modules.
Covers requirement 21.
"""

import os
import pytest
from src.models.task import Task
from src.models.server import Server
from src.energy.energy_calculator import EnergyCalculator
from src.simulation.engine import SimulationResult
from src.metrics.performance_metrics import PerformanceMetrics
from src.reporting.exporter import Exporter
from src.reporting.report_generator import ReportGenerator


class TestReporting:
    def test_export_generation(self, tmp_path):
        """Test 21: Task, metrics, and time series export generation."""
        server = Server("S1", 16.0, 32.0, 100.0, 250.0)
        calc = EnergyCalculator([server])
        calc.record_interval(10.0, 10.0)

        t1 = Task("T1", "J1", 0.0, 2.0, 4.0, 10.0)
        t1.mark_running(0.0, "S1")
        t1.mark_completed(10.0, 0.05)

        res = SimulationResult("TestSched", [t1], [server], calc, 0.0, 10.0)
        metrics = [PerformanceMetrics.calculate_metrics(res)]

        # 1. Export tasks to CSV
        tasks_csv = str(tmp_path / "tasks.csv")
        Exporter.export_tasks_to_csv(res, tasks_csv)
        assert os.path.exists(tasks_csv)
        assert os.path.getsize(tasks_csv) > 0

        # 2. Export metrics to JSON
        metrics_json = str(tmp_path / "metrics.json")
        Exporter.export_metrics_to_json(metrics, metrics_json)
        assert os.path.exists(metrics_json)
        assert os.path.getsize(metrics_json) > 0

        # 3. Export metrics to CSV
        metrics_csv = str(tmp_path / "metrics.csv")
        Exporter.export_metrics_to_csv(metrics, metrics_csv)
        assert os.path.exists(metrics_csv)
        assert os.path.getsize(metrics_csv) > 0

        # 4. Export time series
        timeseries_csv = str(tmp_path / "timeseries.csv")
        Exporter.export_timeseries_to_csv(res, timeseries_csv)
        assert os.path.exists(timeseries_csv)
        assert os.path.getsize(timeseries_csv) > 0

    def test_report_generator_html_and_markdown(self, tmp_path):
        """Test 21: HTML and Markdown experiment report generation."""
        metrics = [{
            "scheduler": "FCFS",
            "total_energy_wh": 150.0,
            "makespan_seconds": 120.0,
            "avg_completion_time_sec": 45.0,
            "p95_completion_time_sec": 80.0,
            "throughput_tasks_per_sec": 0.83,
            "deadline_miss_rate_pct": 5.0,
            "avg_active_servers": 4.0,
            "total_servers": 4,
            "total_state_transitions": 8,
            "energy_savings_vs_baseline_pct": 0.0
        }, {
            "scheduler": "EADCS",
            "total_energy_wh": 110.0,
            "makespan_seconds": 125.0,
            "avg_completion_time_sec": 48.0,
            "p95_completion_time_sec": 82.0,
            "throughput_tasks_per_sec": 0.80,
            "deadline_miss_rate_pct": 5.0,
            "avg_active_servers": 2.2,
            "total_servers": 4,
            "total_state_transitions": 12,
            "energy_savings_vs_baseline_pct": 26.67
        }]

        workload_info = {"total_tasks": 100, "category": "medium", "seed": 42}
        datacenter_info = {"num_servers": 4, "idle_sleep_timeout": 15.0}

        html_out = str(tmp_path / "report.html")
        ReportGenerator.generate_html_report(metrics, workload_info, datacenter_info, html_out)
        assert os.path.exists(html_out)
        with open(html_out, "r", encoding="utf-8") as f:
            content = f.read()
            assert "EADCS" in content
            assert "FCFS" in content
            assert "26.67%" in content

        md_out = str(tmp_path / "report.md")
        ReportGenerator.generate_markdown_report(metrics, workload_info, datacenter_info, md_out)
        assert os.path.exists(md_out)
        with open(md_out, "r", encoding="utf-8") as f:
            content = f.read()
            assert "EADCS" in content
            assert "26.67%" in content
