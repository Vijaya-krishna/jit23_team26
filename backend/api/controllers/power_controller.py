"""
Power Consumption Engine — REST API Controller
Exposes endpoints for real-time power profiles, PUE, and per-server breakdowns.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.api.repositories.simulation_repository import SimulationRepository
from backend.api.services.simulation_service import SimulationService
from backend.middleware.auth_middleware import get_current_user

router = APIRouter(
    prefix="/api/simulation/power",
    tags=["Power Consumption Engine"],
    dependencies=[Depends(get_current_user)],
)


def get_sim_service(db: Session = Depends(get_db)) -> SimulationService:
    repo = SimulationRepository(db)
    return SimulationService(repo)


@router.get("/profile")
def get_power_profile(sim_service: SimulationService = Depends(get_sim_service)):
    """
    Return the real-time power consumption profile for all hosts and
    facility-level PUE, IT/cooling/standby breakdown, and PUE history.
    """
    return sim_service.get_power_profile_data()


@router.get("/summary")
def get_power_summary(sim_service: SimulationService = Depends(get_sim_service)):
    """
    Return only the aggregate facility-level power summary (PUE, IT, cooling, total).
    """
    profile = sim_service.get_power_profile_data()
    return profile["summary"]


@router.get("/pue-history")
def get_pue_history(sim_service: SimulationService = Depends(get_sim_service)):
    """
    Return the in-memory PUE history as a time-series list [{tick, pue}].
    Falls back to global telemetry logs if in-memory history is empty (after restart).
    """
    profile = sim_service.get_power_profile_data()
    pue_history = profile.get("pue_history", [])

    # Fallback: reconstruct from database logs if simulator was restarted
    if not pue_history:
        logs = sim_service.get_global_logs(limit=200)
        pue_history = [{"tick": log.tick, "pue": log.pue} for log in logs]

    return pue_history
