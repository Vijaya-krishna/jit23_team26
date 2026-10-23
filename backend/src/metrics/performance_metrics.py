"""
Performance Metrics Calculator for the Energy-Aware Dynamic Task Scheduling Framework.
Implements standardized evaluation formulas for energy savings, latencies, deadlines, and throughput.
"""

from typing import List, Dict, Any, Optional
import numpy as np
from src.simulation.engine import SimulationResult
from src.models.task import Task, TaskState
from src.models.server import Server


class PerformanceMetrics:
    """
    Computes rigorous statistical and operational metrics from simulation results.
    """

    @staticmethod
    def calculate_metrics(result: SimulationResult) -> Dict[str, Any]:
        """
        Calculates all core performance and energy metrics for a single simulation result.
        """
        completed = result.completed_tasks
        failed = result.failed_tasks
        total_tasks = len(result.tasks)

        # Completion times (turnaround times)
        turnarounds = [t.turnaround_time for t in completed if t.turnaround_time is not None]
        waitings = [t.waiting_time for t in completed if t.waiting_time is not None]

        avg_completion_time = float(np.mean(turnarounds)) if turnarounds else 0.0
        median_completion_time = float(np.median(turnarounds)) if turnarounds else 0.0
        p95_completion_time = float(np.percentile(turnarounds, 95)) if turnarounds else 0.0
        min_completion_time = float(np.min(turnarounds)) if turnarounds else 0.0
        max_completion_time = float(np.max(turnarounds)) if turnarounds else 0.0

        avg_waiting_time = float(np.mean(waitings)) if waitings else 0.0

        # Makespan: observation horizon
        duration = max(0.001, result.end_time - result.start_time)
        makespan = result.makespan

        # Throughput: completed tasks per simulated second
        throughput = len(completed) / duration if duration > 0 else 0.0

        # Deadlines
        tasks_with_deadlines = [t for t in result.tasks if t.deadline is not None]
        deadline_misses = [t for t in tasks_with_deadlines if t.is_deadline_missed]
        if tasks_with_deadlines:
            deadline_miss_rate = (len(deadline_misses) / len(tasks_with_deadlines)) * 100.0
            deadline_satisfaction_rate = 100.0 - deadline_miss_rate
        else:
            deadline_miss_rate = None
            deadline_satisfaction_rate = None

        # Server-level aggregations
        total_state_transitions = sum(s.state_transitions_count for s in result.servers)
        total_wake_ups = sum(s.total_wake_ups for s in result.servers)

        # Average server utilizations
        fleet_history = result.energy_calculator.history
        if fleet_history:
            avg_active_servers = float(np.mean([h["active_servers"] for h in fleet_history]))
        else:
            avg_active_servers = 0.0

        # Energy metrics
        fleet_breakdown = result.energy_calculator.get_fleet_breakdown()

        return {
            "scheduler": result.scheduler_name,
            "total_tasks": total_tasks,
            "completed_tasks": len(completed),
            "failed_tasks": len(failed),
            "pending_tasks": len(result.pending_tasks),
            "failure_rate_pct": (len(failed) / total_tasks * 100.0) if total_tasks > 0 else 0.0,
            "makespan_seconds": round(makespan, 2),
            "throughput_tasks_per_sec": round(throughput, 4),
            "avg_completion_time_sec": round(avg_completion_time, 2),
            "median_completion_time_sec": round(median_completion_time, 2),
            "p95_completion_time_sec": round(p95_completion_time, 2),
            "min_completion_time_sec": round(min_completion_time, 2),
            "max_completion_time_sec": round(max_completion_time, 2),
            "avg_waiting_time_sec": round(avg_waiting_time, 2),
            "tasks_with_deadlines": len(tasks_with_deadlines),
            "deadline_misses": len(deadline_misses),
            "deadline_miss_rate_pct": round(deadline_miss_rate, 2) if deadline_miss_rate is not None else "N/A",
            "deadline_satisfaction_rate_pct": round(deadline_satisfaction_rate, 2) if deadline_satisfaction_rate is not None else "N/A",
            "total_energy_wh": round(fleet_breakdown["total_energy_wh"], 4),
            "total_energy_joules": round(fleet_breakdown["total_energy_joules"], 2),
            "active_energy_wh": round(fleet_breakdown["active_energy_wh"], 4),
            "idle_energy_wh": round(fleet_breakdown["idle_energy_wh"], 4),
            "sleep_energy_wh": round(fleet_breakdown["sleep_energy_wh"], 4),
            "wakeup_overhead_wh": round(fleet_breakdown["wakeup_overhead_wh"], 4),
            "total_state_transitions": total_state_transitions,
            "total_wake_ups": total_wake_ups,
            "avg_active_servers": round(avg_active_servers, 2),
            "total_servers": len(result.servers)
        }

    @staticmethod
    def calculate_energy_savings(baseline_wh: float, proposed_wh: float) -> Optional[float]:
        """
        Calculates percentage energy saved relative to baseline:
        Savings (%) = ((E_baseline - E_proposed) / E_baseline) * 100
        Safely handles division by zero or invalid baselines.
        """
        if baseline_wh is None or baseline_wh <= 0.0:
            return None
        savings = ((baseline_wh - proposed_wh) / baseline_wh) * 100.0
        return round(savings, 2)

    @staticmethod
    def compare_multiple_results(
        results: List[SimulationResult],
        baseline_name: str = "FCFS"
    ) -> List[Dict[str, Any]]:
        """
        Generates comparison matrix comparing all scheduled algorithms against a designated baseline.
        """
        metrics_list = [PerformanceMetrics.calculate_metrics(r) for r in results]
        
        # Locate baseline result
        baseline_metric = next((m for m in metrics_list if m["scheduler"] == baseline_name), None)
        baseline_energy = baseline_metric["total_energy_wh"] if baseline_metric else None

        for m in metrics_list:
            if baseline_energy is not None:
                m["energy_savings_vs_baseline_pct"] = PerformanceMetrics.calculate_energy_savings(
                    baseline_energy, m["total_energy_wh"]
                )
            else:
                m["energy_savings_vs_baseline_pct"] = None

        return metrics_list
