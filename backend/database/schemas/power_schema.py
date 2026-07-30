from pydantic import BaseModel
from typing import List


class HostPowerProfileResponse(BaseModel):
    """Per-host real-time power consumption profile."""
    host_id: int
    power_state: str
    model_name: str
    idle_power_w: float
    peak_power_w: float
    standby_power_w: float
    current_power_w: float
    cpu_utilization: float
    efficiency_pct: float

    class Config:
        from_attributes = True


class PowerSummaryResponse(BaseModel):
    """Aggregate facility-level power and PUE snapshot."""
    pue: float
    pue_rating: str
    it_power_w: float
    cooling_power_w: float
    standby_power_w: float
    total_facility_w: float
    cooling_overhead_pct: float

    class Config:
        from_attributes = True


class PUEHistoryPoint(BaseModel):
    """Single PUE reading at a specific simulation tick."""
    tick: int
    pue: float

    class Config:
        from_attributes = True


class DataCenterPowerProfileResponse(BaseModel):
    """Complete power profile response including summary, per-host breakdown, and PUE history."""
    summary: PowerSummaryResponse
    hosts: List[HostPowerProfileResponse]
    pue_history: List[PUEHistoryPoint]

    class Config:
        from_attributes = True
