from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.api.repositories.simulation_repository import SimulationRepository
from backend.api.services.simulation_service import SimulationService
from backend.middleware.auth_middleware import get_current_user

router = APIRouter(
    prefix="/api/scheduler",
    tags=["Resource Scheduler"]
)

class SchedulerSelectRequest(BaseModel):
    name: str = Field(..., description="Scheduler algorithm name: 'round_robin', 'random', 'energy_aware', or 'ml'")

def get_sim_service(db: Session = Depends(get_db)) -> SimulationService:
    repo = SimulationRepository(db)
    return SimulationService(repo)

@router.get("/active", response_model=Dict[str, Any])
def get_active_scheduler(sim_service: SimulationService = Depends(get_sim_service)):
    """
    Get the currently active scheduling algorithm strategy and config parameters.
    """
    active_name = getattr(sim_service.simulator, "active_scheduler_name", "round_robin")
    return {
        "active_scheduler": active_name,
        "supported_schedulers": ["round_robin", "random", "energy_aware", "ml"]
    }

@router.post("/select", response_model=Dict[str, Any])
def select_scheduler(
    payload: SchedulerSelectRequest,
    sim_service: SimulationService = Depends(get_sim_service),
    current_user: Any = Depends(get_current_user)
):
    """
    Switch active scheduler strategy algorithm.
    """
    try:
        sim_service.set_scheduler(payload.name)
        sim_service.simulator.active_scheduler_name = payload.name.lower()
        return {
            "status": "success",
            "active_scheduler": payload.name.lower(),
            "message": f"Successfully set active scheduler strategy to: '{payload.name}'"
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/consolidate", response_model=Dict[str, Any])
def trigger_vm_consolidation(
    sim_service: SimulationService = Depends(get_sim_service),
    current_user: Any = Depends(get_current_user)
):
    """
    Manually trigger VM consolidation pass across physical hosts to minimize energy consumption.
    """
    from backend.simulation.scheduler import EnergyAwareScheduler
    sim_service._sync_load()
    
    hosts_list = list(sim_service.simulator.hosts.values())
    ea_scheduler = EnergyAwareScheduler()
    sleep_count = ea_scheduler.consolidate(hosts_list)
    sim_service._sync_save()

    return {
        "status": "success",
        "hosts_transitioned_to_sleep": sleep_count,
        "message": f"VM consolidation complete. Transitioned {sleep_count} idle hosts to SLEEP mode."
    }
