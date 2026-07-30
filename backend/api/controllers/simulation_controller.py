from typing import List, Dict, Any
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.database.schemas.simulation_schema import (
    PhysicalServerResponse,
    PhysicalServerCreate,
    VirtualMachineResponse,
    VirtualMachineCreate,
    HostPowerStateUpdate,
    TelemetryResponse,
    TaskResponse,
    WorkloadGenerateRequest
)
from backend.database.schemas.monitoring_schema import GlobalTelemetryLogResponse, HostTelemetryLogResponse
from backend.api.repositories.simulation_repository import SimulationRepository
from backend.api.services.simulation_service import SimulationService
from backend.middleware.auth_middleware import get_current_user
from backend.database.models.user_model import UserModel

router = APIRouter(
    prefix="/api/simulation",
    tags=["Data Center Simulator"],
    dependencies=[Depends(get_current_user)]  # Secure all simulation routes
)

def get_sim_service(db: Session = Depends(get_db)) -> SimulationService:
    """
    Dependency injection builder for SimulationService.
    """
    repo = SimulationRepository(db)
    return SimulationService(repo)


@router.get("/servers", response_model=List[PhysicalServerResponse])
def get_servers(sim_service: SimulationService = Depends(get_sim_service)):
    """
    Get detailed telemetry status of all physical servers in the datacenter.
    """
    return sim_service.get_servers_status()

# Public endpoint (no auth) for retrieving physical servers status
@router.get("/servers/public", response_model=List[PhysicalServerResponse])
def get_servers_public(sim_service: SimulationService = Depends(get_sim_service)):
    """
    Public access to physical servers telemetry without authentication.
    """
    return sim_service.get_servers_status()


@router.get("/vms", response_model=List[VirtualMachineResponse])
def get_vms(sim_service: SimulationService = Depends(get_sim_service)):
    """
    Get a list of all active Virtual Machines.
    """
    return sim_service.get_vms_status()


@router.post("/servers/{host_id}/power", response_model=PhysicalServerResponse)
def update_power_state(
    host_id: int,
    payload: HostPowerStateUpdate,
    sim_service: SimulationService = Depends(get_sim_service)
):
    """
    Change power state of a specific physical server (ACTIVE, SLEEP, or OFF).
    """
    return sim_service.update_host_power_state(host_id, payload.power_state)


@router.post("/servers/{host_id}/deploy-vm", response_model=VirtualMachineResponse, status_code=status.HTTP_201_CREATED)
def deploy_virtual_machine(
    host_id: int,
    vm_data: VirtualMachineCreate,
    sim_service: SimulationService = Depends(get_sim_service)
):
    """
    Manually provision and deploy a VM on a physical server (validating hardware capacities).
    """
    return sim_service.deploy_vm(host_id, vm_data)


@router.delete("/vms/{vm_id}", status_code=status.HTTP_200_OK)
def destroy_virtual_machine(
    vm_id: int,
    sim_service: SimulationService = Depends(get_sim_service)
):
    """
    Tear down a virtual machine and deallocate its computing footprints.
    """
    sim_service.destroy_vm(vm_id)
    return {"status": "success", "message": f"Virtual machine {vm_id} successfully decommissioned."}


@router.post("/tick", response_model=TelemetryResponse)
def trigger_simulation_tick(sim_service: SimulationService = Depends(get_sim_service)):
    """
    Progress the simulation by one clock step. Updates power draws, cooling costs, and thermal indexes.
    """
    return sim_service.trigger_tick()


@router.post("/servers", response_model=PhysicalServerResponse, status_code=status.HTTP_201_CREATED)
def provision_physical_server(
    server_data: PhysicalServerCreate,
    sim_service: SimulationService = Depends(get_sim_service)
):
    """
    Provision and register a new physical server into the datacenter.
    """
    return sim_service.register_host(server_data)


@router.get("/telemetry", response_model=TelemetryResponse)
def get_telemetry(sim_service: SimulationService = Depends(get_sim_service)):
    """
    Get current aggregated simulation telemetry parameters (ticks, total energy, power, cooling, carbon).
    """
    return sim_service.get_telemetry_status()


@router.post("/workload/generate", response_model=List[TaskResponse], status_code=status.HTTP_201_CREATED)
def generate_workload_tasks(
    req: WorkloadGenerateRequest,
    sim_service: SimulationService = Depends(get_sim_service),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Generate synthetic workload tasks and queue them in WAITING state.
    """
    return sim_service.generate_workload(req.count)


@router.get("/tasks", response_model=List[TaskResponse])
def get_all_tasks(
    sim_service: SimulationService = Depends(get_sim_service),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Retrieve all tasks in the system (waiting, running, completed, failed).
    """
    return sim_service.get_tasks()


@router.get("/monitoring/global", response_model=List[GlobalTelemetryLogResponse])
def get_global_telemetry_logs(
    limit: int = Query(default=200, ge=1, le=1000),
    sim_service: SimulationService = Depends(get_sim_service)
):
    """
    Retrieve global aggregated telemetry history logs ordered by tick (for time-series charting).
    """
    return sim_service.get_global_logs(limit)


@router.get("/monitoring/hosts/{host_id}", response_model=List[HostTelemetryLogResponse])
def get_host_telemetry_logs(
    host_id: int,
    limit: int = Query(default=200, ge=1, le=1000),
    sim_service: SimulationService = Depends(get_sim_service)
):
    """
    Retrieve per-host telemetry history logs ordered by tick (for time-series charting).
    """
    return sim_service.get_host_logs(host_id, limit)
