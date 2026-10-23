"""
Energy-Aware Dynamic Task Scheduling Framework - Backend REST API Service
FastAPI REST API exposing discrete-event simulation, energy calculations,
and multi-algorithm benchmarking for cloud/data center task scheduling.
"""

import os
import sys
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Ensure local backend packages are importable
_current_dir = os.path.dirname(os.path.abspath(__file__))
if _current_dir not in sys.path:
    sys.path.insert(0, _current_dir)

from src.models.server import Server
from src.models.task import Task
from src.algorithms.fcfs import FCFSScheduler
from src.algorithms.round_robin import RoundRobinScheduler
from src.algorithms.load_balancing import LoadBalancingScheduler
from src.algorithms.eadcs import EADCSScheduler
from src.simulation.engine import SimulationEngine, SimulationResult
from src.simulation.workload_generator import WorkloadGenerator, WorkloadCategory
from src.metrics.performance_metrics import PerformanceMetrics
from src.reporting.report_generator import ReportGenerator

app = FastAPI(
    title="Energy-Aware Dynamic Task Scheduling Framework API",
    description=(
        "Research-grade REST API for energy-aware big data task scheduling, "
        "discrete-event data center simulation, and multi-objective optimization."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for local dashboards and external consumers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Request & Response Models ---

class ServerConfigModel(BaseModel):
    server_id: str
    total_cpu_cores: int = Field(..., gt=0)
    total_ram_gb: float = Field(..., gt=0)
    p_idle_watts: float = Field(default=100.0, ge=0)
    p_max_watts: float = Field(default=350.0, gt=0)
    alpha: float = Field(default=1.4, ge=1.0)
    sleep_power_watts: float = Field(default=10.0, ge=0)


class TaskConfigModel(BaseModel):
    task_id: str
    cpu_cores_required: int = Field(..., gt=0)
    ram_gb_required: float = Field(..., gt=0)
    duration_seconds: float = Field(..., gt=0)
    arrival_time_seconds: float = Field(default=0.0, ge=0)
    deadline_seconds: Optional[float] = None
    priority: int = Field(default=1, ge=1, le=5)


class SimulationRequest(BaseModel):
    algorithm: str = Field(default="eadcs", description="Algorithm: eadcs, fcfs, round_robin, load_balancing")
    alpha_energy_weight: float = Field(default=0.6, ge=0.0, le=1.0)
    beta_makespan_weight: float = Field(default=0.4, ge=0.0, le=1.0)
    servers: Optional[List[ServerConfigModel]] = None
    tasks: Optional[List[TaskConfigModel]] = None
    workload_type: Optional[str] = Field(default=None, description="synthetic workload category: low, medium, bursty")
    workload_tasks_count: Optional[int] = Field(default=50, ge=10, le=500)


class BenchmarkRequest(BaseModel):
    workload_type: str = Field(default="medium", description="low, medium, or bursty")
    task_count: int = Field(default=60, ge=10, le=300)
    server_count: int = Field(default=6, ge=2, le=32)


# --- Helper Functions ---

def _build_default_fleet(count: int = 6) -> List[Server]:
    fleet = []
    for i in range(count):
        if i % 2 == 0:
            fleet.append(Server(
                server_id=f"srv-{i+1}",
                total_cpu_cores=16,
                total_ram_gb=64.0,
                p_idle_watts=95.0,
                p_max_watts=320.0,
                alpha=1.4,
                sleep_power_watts=10.0
            ))
        else:
            fleet.append(Server(
                server_id=f"srv-{i+1}",
                total_cpu_cores=32,
                total_ram_gb=128.0,
                p_idle_watts=140.0,
                p_max_watts=480.0,
                alpha=1.5,
                sleep_power_watts=15.0
            ))
    return fleet


def _get_scheduler_instance(alg: str, alpha: float = 0.6, beta: float = 0.4):
    alg_clean = alg.strip().lower()
    if alg_clean == "eadcs":
        return EADCSScheduler(alpha=alpha, beta=beta)
    elif alg_clean == "fcfs":
        return FCFSScheduler()
    elif alg_clean in ("round_robin", "rr"):
        return RoundRobinScheduler()
    elif alg_clean in ("load_balancing", "lb"):
        return LoadBalancingScheduler()
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown algorithm: '{alg}'. Supported: 'eadcs', 'fcfs', 'round_robin', 'load_balancing'."
        )


from fastapi.responses import FileResponse

# Static Frontend Path
_frontend_dir = os.path.abspath(os.path.join(_current_dir, "..", "frontend"))

# --- API Endpoints ---

@app.get("/", include_in_schema=False)
def root():
    index_path = os.path.join(_frontend_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {
        "status": "online",
        "service": "Energy-Aware Dynamic Task Scheduling Framework Backend",
        "version": "1.0.0",
        "docs": "/docs",
        "supported_algorithms": ["eadcs", "fcfs", "round_robin", "load_balancing"]
    }

@app.get("/style.css", include_in_schema=False)
def serve_css():
    css_path = os.path.join(_frontend_dir, "style.css")
    if os.path.exists(css_path):
        return FileResponse(css_path, media_type="text/css")
    raise HTTPException(status_code=404, detail="style.css not found")

@app.get("/app.js", include_in_schema=False)
def serve_js():
    js_path = os.path.join(_frontend_dir, "app.js")
    if os.path.exists(js_path):
        return FileResponse(js_path, media_type="application/javascript")
    raise HTTPException(status_code=404, detail="app.js not found")


@app.get("/api/v1/health")
def health_check():
    return {
        "status": "healthy",
        "service": "eadcs-scheduler-backend",
        "simulation_engine": "ready"
    }


@app.get("/api/v1/algorithms")
def list_algorithms():
    return {
        "algorithms": [
            {
                "id": "eadcs",
                "name": "Energy-Aware Dynamic Cost Scheduling (Proposed)",
                "description": (
                    "Multi-objective optimization algorithm balancing dynamic power delta, "
                    "idle sleep transitions, wake penalty amortization, and makespan impact."
                ),
                "is_proposed": True,
                "parameters": {"alpha_energy": "float [0-1]", "beta_makespan": "float [0-1]"}
            },
            {
                "id": "fcfs",
                "name": "First-Come First-Served (Baseline)",
                "description": "Allocates tasks sequentially to the first available host with sufficient capacity.",
                "is_proposed": False
            },
            {
                "id": "round_robin",
                "name": "Round Robin (Baseline)",
                "description": "Cyclic assignment across hosts without considering power models or task profiles.",
                "is_proposed": False
            },
            {
                "id": "load_balancing",
                "name": "Greedy Load Balancing (Baseline)",
                "description": "Assigns tasks to minimize current host utilization disparity.",
                "is_proposed": False
            }
        ]
    }


@app.get("/api/v1/workloads")
def list_workloads():
    return {
        "categories": [
            {
                "type": "low",
                "description": "Light steady workload, tests energy savings via idle server sleep states",
                "default_tasks": 40
            },
            {
                "type": "medium",
                "description": "Balanced mixed-priority big data compute and memory workload",
                "default_tasks": 60
            },
            {
                "type": "bursty",
                "description": "Spike-heavy arrival batches, tests dynamic responsiveness and queue stability",
                "default_tasks": 80
            }
        ]
    }


@app.post("/api/v1/simulate")
def run_simulation(req: SimulationRequest):
    # Prepare servers
    if req.servers and len(req.servers) > 0:
        servers = [
            Server(
                server_id=s.server_id,
                total_cpu_cores=s.total_cpu_cores,
                total_ram_gb=s.total_ram_gb,
                p_idle_watts=s.p_idle_watts,
                p_max_watts=s.p_max_watts,
                alpha=s.alpha,
                sleep_power_watts=s.sleep_power_watts
            )
            for s in req.servers
        ]
    else:
        servers = _build_default_fleet(6)

    # Prepare tasks
    if req.tasks and len(req.tasks) > 0:
        tasks = [
            Task(
                task_id=t.task_id,
                cpu_cores_required=t.cpu_cores_required,
                ram_gb_required=t.ram_gb_required,
                duration_seconds=t.duration_seconds,
                arrival_time_seconds=t.arrival_time_seconds,
                deadline_seconds=t.deadline_seconds,
                priority=t.priority
            )
            for t in req.tasks
        ]
    else:
        cat_map = {
            "low": WorkloadCategory.LOW,
            "bursty": WorkloadCategory.BURSTY,
            "medium": WorkloadCategory.MEDIUM
        }
        chosen_cat = cat_map.get((req.workload_type or "medium").lower(), WorkloadCategory.MEDIUM)
        generator = WorkloadGenerator(seed=42)
        tasks = generator.generate_synthetic(category=chosen_cat, count=req.workload_tasks_count or 50)

    scheduler = _get_scheduler_instance(req.algorithm, req.alpha_energy_weight, req.beta_makespan_weight)
    engine = SimulationEngine(servers=servers, scheduler=scheduler)
    result: SimulationResult = engine.run(tasks)

    return {
        "status": "success",
        "algorithm": result.algorithm_name,
        "metrics": {
            "total_energy_kwh": result.total_energy_kwh,
            "total_energy_joules": result.total_energy_joules,
            "carbon_emission_kg": result.carbon_emission_kg,
            "makespan_seconds": result.makespan_seconds,
            "average_turnaround_time_seconds": result.average_turnaround_time_seconds,
            "average_waiting_time_seconds": result.average_waiting_time_seconds,
            "average_cpu_utilization_percent": result.average_cpu_utilization_percent,
            "average_ram_utilization_percent": result.average_ram_utilization_percent,
            "sla_violation_rate_percent": result.sla_violation_rate_percent,
            "tasks_completed": result.tasks_completed,
            "tasks_failed": result.tasks_failed
        },
        "server_summaries": [
            {
                "server_id": s.server_id,
                "tasks_processed": s.tasks_processed,
                "energy_kwh": round(s.total_energy_consumed_joules / 3.6e6, 4),
                "active_time_s": s.total_active_time_seconds,
                "sleep_time_s": s.total_sleep_time_seconds,
                "state_transitions": s.state_transition_count
            }
            for s in engine.servers
        ]
    }


@app.post("/api/v1/benchmark")
def run_benchmark(req: BenchmarkRequest):
    cat_map = {
        "low": WorkloadCategory.LOW,
        "bursty": WorkloadCategory.BURSTY,
        "medium": WorkloadCategory.MEDIUM
    }
    cat = cat_map.get(req.workload_type.lower(), WorkloadCategory.MEDIUM)
    generator = WorkloadGenerator(seed=100)
    tasks = generator.generate_synthetic(category=cat, count=req.task_count)

    algorithms = [
        ("EADCS (Proposed)", EADCSScheduler(alpha=0.6, beta=0.4)),
        ("FCFS", FCFSScheduler()),
        ("Round Robin", RoundRobinScheduler()),
        ("Load Balancing", LoadBalancingScheduler())
    ]

    results = []
    base_energy = None

    for name, scheduler in algorithms:
        fleet = _build_default_fleet(req.server_count)
        # Deepcopy tasks
        workload_copy = [
            Task(
                task_id=t.task_id,
                cpu_cores_required=t.cpu_cores_required,
                ram_gb_required=t.ram_gb_required,
                duration_seconds=t.duration_seconds,
                arrival_time_seconds=t.arrival_time_seconds,
                deadline_seconds=t.deadline_seconds,
                priority=t.priority
            )
            for t in tasks
        ]
        engine = SimulationEngine(servers=fleet, scheduler=scheduler)
        sim_res = engine.run(workload_copy)

        if name == "FCFS":
            base_energy = sim_res.total_energy_kwh

        results.append({
            "algorithm": name,
            "energy_kwh": sim_res.total_energy_kwh,
            "carbon_kg": sim_res.carbon_emission_kg,
            "makespan_s": sim_res.makespan_seconds,
            "avg_wait_s": sim_res.average_waiting_time_seconds,
            "avg_turnaround_s": sim_res.average_turnaround_time_seconds,
            "cpu_util_pct": sim_res.average_cpu_utilization_percent,
            "sla_violations_pct": sim_res.sla_violation_rate_percent,
            "tasks_completed": sim_res.tasks_completed
        })

    # Calculate savings compared to FCFS baseline
    if base_energy and base_energy > 0:
        for r in results:
            diff = base_energy - r["energy_kwh"]
            r["energy_savings_vs_fcfs_pct"] = round((diff / base_energy) * 100.0, 2)

    return {
        "status": "success",
        "workload": req.workload_type,
        "total_tasks": req.task_count,
        "total_servers": req.server_count,
        "benchmark_results": results
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
