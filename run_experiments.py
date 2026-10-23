"""
Automated Experiment Benchmark Runner for the Energy-Aware Task Scheduling Framework.
Executes reproducible evaluations across Low, Medium, and Bursty workloads for all algorithms,
saves metrics to reports/, and generates HTML and Markdown reports with real simulation data.
"""

import os
import json
from src.models.server import Server
from src.algorithms.fcfs import FCFSScheduler
from src.algorithms.round_robin import RoundRobinScheduler
from src.algorithms.load_balancing import LoadBalancingScheduler
from src.algorithms.eadcs import EADCSScheduler
from src.simulation.engine import SimulationEngine
from src.simulation.workload_generator import WorkloadGenerator, WorkloadCategory
from src.metrics.performance_metrics import PerformanceMetrics
from src.reporting.exporter import Exporter
from src.reporting.report_generator import ReportGenerator


def create_standard_fleet(num_servers: int = 8):
    """Creates a standard heterogeneous simulated data center fleet."""
    fleet = []
    for i in range(num_servers):
        if i % 2 == 0:
            # Standard compute node
            fleet.append(Server(
                server_id=f"Host_{i+1:02d}",
                cpu_capacity=16.0,
                memory_capacity=64.0,
                idle_power=120.0,
                max_power=300.0,
                sleep_power=12.0,
                wake_up_energy=600.0,
                wake_up_delay=4.0,
                alpha=1.5,
                idle_timeout_to_sleep=15.0
            ))
        else:
            # High-memory node
            fleet.append(Server(
                server_id=f"Host_{i+1:02d}",
                cpu_capacity=32.0,
                memory_capacity=128.0,
                idle_power=180.0,
                max_power=450.0,
                sleep_power=18.0,
                wake_up_energy=900.0,
                wake_up_delay=5.0,
                alpha=1.6,
                idle_timeout_to_sleep=20.0
            ))
    return fleet


def run_benchmark():
    print("=" * 80)
    print("ENERGY-AWARE TASK SCHEDULING FRAMEWORK: BENCHMARK SUITE")
    print("=" * 80)

    scenarios = [
        {"name": "Low-Load Workload", "category": WorkloadCategory.LOW, "tasks": 80, "seed": 101},
        {"name": "Medium-Load Workload", "category": WorkloadCategory.MEDIUM, "tasks": 120, "seed": 202},
        {"name": "Bursty Workload", "category": WorkloadCategory.BURSTY, "tasks": 160, "seed": 303},
    ]

    schedulers = [
        FCFSScheduler(),
        RoundRobinScheduler(),
        LoadBalancingScheduler(),
        EADCSScheduler()
    ]

    os.makedirs("reports", exist_ok=True)
    all_scenario_summaries = {}

    for sc in scenarios:
        print(f"\n>>> Running Scenario: {sc['name']} ({sc['tasks']} tasks, seed={sc['seed']})")
        tasks = WorkloadGenerator.generate_workload(
            num_tasks=sc["tasks"],
            category=sc["category"],
            seed=sc["seed"]
        )

        results = []
        for sched in schedulers:
            fleet = create_standard_fleet(num_servers=8)
            engine = SimulationEngine(
                scheduler=sched,
                servers=fleet,
                tasks=tasks,
                enable_sleep_state=True,
                idle_sleep_timeout=15.0
            )
            sim_res = engine.run()
            results.append(sim_res)

        comparison = PerformanceMetrics.compare_multiple_results(results, baseline_name="FCFS")
        all_scenario_summaries[sc["name"]] = comparison

        # Print terminal summary
        print(f"{'Algorithm':<16} | {'Energy (Wh)':<12} | {'Savings %':<10} | {'Makespan (s)':<12} | {'Avg Latency':<12} | {'Active Hosts':<12}")
        print("-" * 85)
        for m in comparison:
            sav = m.get("energy_savings_vs_baseline_pct")
            sav_str = f"{sav:+.2f}%" if sav is not None else "0.00% (Base)"
            print(f"{m['scheduler']:<16} | {m['total_energy_wh']:<12.3f} | {sav_str:<10} | {m['makespan_seconds']:<12.1f} | {m['avg_completion_time_sec']:<12.2f} | {m['avg_active_servers']:<12.1f}")

        # Export scenario artifacts
        slug = sc["name"].lower().replace(" ", "_").replace("-", "_")
        Exporter.export_metrics_to_csv(comparison, f"reports/{slug}_metrics.csv")
        Exporter.export_metrics_to_json(comparison, f"reports/{slug}_metrics.json")

    # Generate overarching report for the Medium scenario
    medium_comp = all_scenario_summaries["Medium-Load Workload"]
    ReportGenerator.generate_html_report(
        metrics_comparison=medium_comp,
        workload_info={"total_tasks": 120, "category": "medium", "seed": 202},
        datacenter_info={"num_servers": 8, "idle_sleep_timeout": 15.0},
        output_path="reports/experiment_report.html"
    )
    ReportGenerator.generate_markdown_report(
        metrics_comparison=medium_comp,
        workload_info={"total_tasks": 120, "category": "medium", "seed": 202},
        datacenter_info={"num_servers": 8, "idle_sleep_timeout": 15.0},
        output_path="reports/experiment_report.md"
    )

    print("\n" + "=" * 80)
    print("Benchmark complete! Reports and CSV metrics generated in reports/")
    print("=" * 80)


if __name__ == "__main__":
    run_benchmark()
