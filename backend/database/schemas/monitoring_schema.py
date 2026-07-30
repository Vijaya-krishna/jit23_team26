from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class GlobalTelemetryLogResponse(BaseModel):
    id: int
    tick: int
    cpu_utilization: float
    ram_utilization: float
    storage_utilization: float
    bandwidth_utilization: float
    it_power_w: float
    cooling_power_w: float
    total_power_w: float
    total_energy_kwh: float
    carbon_emissions_kg: float
    pue: float
    timestamp: datetime

    class Config:
        from_attributes = True


class HostTelemetryLogResponse(BaseModel):
    id: int
    tick: int
    host_id: int
    cpu_utilization: float
    ram_utilization: float
    storage_utilization: float
    bandwidth_utilization: float
    temperature: float
    power_consumption_w: float

    class Config:
        from_attributes = True
