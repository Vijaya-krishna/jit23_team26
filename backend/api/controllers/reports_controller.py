import csv
import io
from typing import Dict, Any
from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.api.repositories.simulation_repository import SimulationRepository
from backend.api.services.simulation_service import SimulationService

router = APIRouter(
    prefix="/api/reports",
    tags=["Reports & Analytics Exporter"]
)

def get_sim_service(db: Session = Depends(get_db)) -> SimulationService:
    repo = SimulationRepository(db)
    return SimulationService(repo)

@router.get("/summary", response_model=Dict[str, Any])
def get_executive_summary(sim_service: SimulationService = Depends(get_sim_service)):
    """
    Get aggregated executive summary metrics for auditing and reporting.
    """
    telemetry = sim_service.get_telemetry_status()
    tasks = sim_service.get_tasks()

    total_tasks = len(tasks)
    completed_tasks = sum(1 for t in tasks if t.status == "COMPLETED")
    failed_tasks = sum(1 for t in tasks if t.status == "FAILED")
    running_tasks = sum(1 for t in tasks if t.status == "RUNNING")
    waiting_tasks = sum(1 for t in tasks if t.status == "WAITING")

    sla_breach_rate = (failed_tasks / total_tasks * 100.0) if total_tasks > 0 else 0.0
    completion_rate = (completed_tasks / total_tasks * 100.0) if total_tasks > 0 else 0.0

    # Baseline unoptimized energy estimation vs actual energy consumed
    baseline_energy_kwh = telemetry.get("total_energy_kwh", 0.0) * 1.35
    energy_saved_kwh = max(0.0, baseline_energy_kwh - telemetry.get("total_energy_kwh", 0.0))
    carbon_avoided_kg = energy_saved_kwh * 0.475  # 0.475 kg CO2 per kWh

    pue_history = getattr(sim_service.simulator, "pue_history", [])
    avg_pue = sum(p["pue"] for p in pue_history) / max(1, len(pue_history)) if pue_history else 1.35

    return {
        "clock_ticks": telemetry.get("tick", 0),
        "total_hosts": telemetry.get("total_hosts", 0),
        "active_hosts": telemetry.get("active_hosts", 0),
        "total_vms": telemetry.get("total_vms", 0),
        "total_energy_kwh": round(telemetry.get("total_energy_kwh", 0.0), 4),
        "energy_saved_kwh": round(energy_saved_kwh, 4),
        "carbon_emissions_kg": round(telemetry.get("carbon_emissions_kg", 0.0), 4),
        "carbon_avoided_kg": round(carbon_avoided_kg, 4),
        "average_pue": round(avg_pue, 3),
        "task_metrics": {
            "total": total_tasks,
            "completed": completed_tasks,
            "failed": failed_tasks,
            "running": running_tasks,
            "waiting": waiting_tasks,
            "completion_rate_pct": round(completion_rate, 2),
            "sla_breach_rate_pct": round(sla_breach_rate, 2)
        }
    }

@router.get("/export/csv")
def export_telemetry_csv(sim_service: SimulationService = Depends(get_sim_service)):
    """
    Export global telemetry history logs as a downloadable CSV file.
    """
    logs = sim_service.get_global_logs(limit=1000)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Tick", "CPU_Util", "RAM_Util", "Storage_Util", "Bandwidth_Util",
        "IT_Power_W", "Cooling_Power_W", "Total_Power_W",
        "Total_Energy_kWh", "Carbon_Emissions_kg", "PUE"
    ])

    for log in logs:
        writer.writerow([
            log.tick,
            round(log.cpu_utilization, 4),
            round(log.ram_utilization, 4),
            round(log.storage_utilization, 4),
            round(log.bandwidth_utilization, 4),
            round(log.it_power_w, 2),
            round(log.cooling_power_w, 2),
            round(log.total_power_w, 2),
            round(log.total_energy_kwh, 6),
            round(log.carbon_emissions_kg, 6),
            round(log.pue, 3)
        ])

    csv_data = output.getvalue()
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=simulation_telemetry_report.csv"}
    )

@router.get("/export/json")
def export_telemetry_json(sim_service: SimulationService = Depends(get_sim_service)):
    """
    Export full simulation state and logs snapshot as JSON.
    """
    telemetry = sim_service.get_telemetry_status()
    summary = get_executive_summary(sim_service)
    logs = sim_service.get_global_logs(limit=1000)

    export_data = {
        "summary": summary,
        "current_telemetry": telemetry,
        "telemetry_history": [
            {
                "tick": log.tick,
                "cpu_utilization": log.cpu_utilization,
                "ram_utilization": log.ram_utilization,
                "total_power_w": log.total_power_w,
                "total_energy_kwh": log.total_energy_kwh,
                "pue": log.pue
            }
            for log in logs
        ]
    }
    return export_data
