from typing import List, Optional
from pydantic import BaseModel, Field

class VirtualMachineBase(BaseModel):
    cpu_cores: int = Field(..., gt=0, description="Allocated CPU cores")
    ram_mb: float = Field(..., gt=0, description="Allocated memory in MB")
    storage_gb: float = Field(..., gt=0, description="Allocated disk size in GB")
    bandwidth_mbps: float = Field(..., gt=0, description="Allocated bandwidth in Mbps")

class VirtualMachineCreate(VirtualMachineBase):
    pass

class VirtualMachineResponse(VirtualMachineBase):
    id: int
    cpu_utilization: float
    ram_utilization: float
    host_id: Optional[int] = None

    class Config:
        from_attributes = True


class PhysicalServerBase(BaseModel):
    cpu_cores: int = Field(..., gt=0, description="Physical CPU cores count")
    cpu_frequency_ghz: float = Field(..., gt=0, description="Frequency of CPU in GHz")
    ram_mb: float = Field(..., gt=0, description="System RAM in MB")
    storage_gb: float = Field(..., gt=0, description="Local Storage capacity in GB")
    bandwidth_mbps: float = Field(..., gt=0, description="Total Bandwidth in Mbps")

class PhysicalServerCreate(PhysicalServerBase):
    pass

class PhysicalServerResponse(PhysicalServerBase):
    id: int
    power_state: str
    temperature: float
    cpu_utilization: float
    ram_utilization: float
    storage_utilization: float
    bandwidth_utilization: float
    power_consumption: float
    vms: List[VirtualMachineResponse] = []

    class Config:
        from_attributes = True


class HostPowerStateUpdate(BaseModel):
    power_state: str = Field(..., description="Target power state: ACTIVE, SLEEP, or OFF")


class TelemetryResponse(BaseModel):
    tick: int
    total_hosts: int
    active_hosts: int
    sleeping_hosts: int
    off_hosts: int
    total_vms: int
    it_power_w: float
    cooling_power_w: float
    total_power_w: float
    total_energy_kwh: float
    energy_cost_usd: float
    cooling_cost_usd: float
    carbon_emissions_kg: float
    average_cpu_utilization: float
    average_ram_utilization: float


class TaskResponse(BaseModel):
    id: int
    cpu_requirement: float
    ram_requirement: float
    storage_requirement: float
    bandwidth_requirement: float
    priority: str
    execution_time: int
    deadline: int
    arrival_time: int
    status: str
    vm_id: Optional[int] = None

    class Config:
        from_attributes = True


class WorkloadGenerateRequest(BaseModel):
    count: int = Field(default=10, ge=1, le=200, description="Number of synthetic tasks to generate")
