"""
Unit tests for PerformanceMetrics calculations, formulas, and edge cases.
Covers requirement 20.
"""

import pytest
from src.metrics.performance_metrics import PerformanceMetrics
from src.models.task import Task
from src.models.server import Server
from src.energy.energy_calculator import EnergyCalculator
from src.simulation.engine import SimulationResult


class TestPerformanceMetrics:
    def test_energy_savings_formula(self):
        """Test 20: Verified calculation of energy savings percentage."""
        # Baseline = 100 Wh, Proposed = 80 Wh => 20% savings
        savings = PerformanceMetrics.calculate_energy_savings(baseline_wh=100.0, proposed_wh=80.0)
        assert savings == 20.0

        # Baseline = 100 Wh, Proposed = 110 Wh => -10% savings
        neg_savings = PerformanceMetrics.calculate_energy_savings(baseline_wh=100.0, proposed_wh=110.0)
        assert neg_savings == -10.0

    def test_energy_savings_division_by_zero_safety(self):
        """Test safe handling of zero or negative baseline energy."""
        assert PerformanceMetrics.calculate_energy_savings(baseline_wh=0.0, proposed_wh=50.0) is None
        assert PerformanceMetrics.calculate_energy_savings(baseline_wh=None, proposed_wh=50.0) is None
        assert PerformanceMetrics.calculate_energy_savings(baseline_wh=-10.0, proposed_wh=50.0) is None

    def test_metrics_calculation(self):
        """Test full metrics dictionary computation from SimulationResult."""
        server = Server("S1", 16.0, 32.0, 100.0, 250.0)
        calc = EnergyCalculator([server])
        calc.record_interval(current_time=100.0, delta_time=100.0)

        t1 = Task("T1", "J1", arrival_time=0.0, cpu_demand=2.0, memory_demand=4.0, duration=20.0, deadline=30.0)
        t1.mark_running(start_time=0.0, server_id="S1")
        t1.mark_completed(completion_time=20.0, energy=0.1)

        t2 = Task("T2", "J2", arrival_time=10.0, cpu_demand=2.0, memory_demand=4.0, duration=40.0, deadline=40.0)
        t2.mark_running(start_time=10.0, server_id="S1")
        t2.mark_completed(completion_time=50.0, energy=0.2) # Missed deadline: 50 > 40

        res = SimulationResult(
            scheduler_name="TestSched",
            tasks=[t1, t2],
            servers=[server],
            energy_calculator=calc,
            start_time=0.0,
            end_time=100.0
        )

        metrics = PerformanceMetrics.calculate_metrics(res)
        assert metrics["total_tasks"] == 2
        assert metrics["completed_tasks"] == 2
        assert metrics["failed_tasks"] == 0
        assert metrics["makespan_seconds"] == 100.0
        assert metrics["throughput_tasks_per_sec"] == 0.02 # 2 tasks / 100 s
        assert metrics["deadline_misses"] == 1
        assert metrics["deadline_miss_rate_pct"] == 50.0
        assert metrics["deadline_satisfaction_rate_pct"] == 50.0
        assert metrics["avg_completion_time_sec"] == 30.0 # ((20-0) + (50-10)) / 2 = 60 / 2 = 30.0
