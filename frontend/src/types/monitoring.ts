// Telemetry log types for the Resource Monitor / Analytics dashboard

export interface GlobalTelemetryLog {
  id: number;
  tick: number;
  cpu_utilization: number;
  ram_utilization: number;
  storage_utilization: number;
  bandwidth_utilization: number;
  it_power_w: number;
  cooling_power_w: number;
  total_power_w: number;
  total_energy_kwh: number;
  carbon_emissions_kg: number;
  pue: number;
  timestamp: string;
}

export interface HostTelemetryLog {
  id: number;
  tick: number;
  host_id: number;
  cpu_utilization: number;
  ram_utilization: number;
  storage_utilization: number;
  bandwidth_utilization: number;
  temperature: number;
  power_consumption_w: number;
}

// ─── Power Consumption Engine types ────────────────────────────────────────────

export interface HostPowerProfile {
  host_id: number;
  power_state: string;
  model_name: string;
  idle_power_w: number;
  peak_power_w: number;
  standby_power_w: number;
  current_power_w: number;
  cpu_utilization: number;
  efficiency_pct: number;
}

export interface PowerSummary {
  pue: number;
  pue_rating: string;
  it_power_w: number;
  cooling_power_w: number;
  standby_power_w: number;
  total_facility_w: number;
  cooling_overhead_pct: number;
}

export interface PUEHistoryPoint {
  tick: number;
  pue: number;
}

export interface DataCenterPowerProfile {
  summary: PowerSummary;
  hosts: HostPowerProfile[];
  pue_history: PUEHistoryPoint[];
}

