export interface VirtualMachine {
  id: number;
  cpu_cores: number;
  ram_mb: number;
  storage_gb: number;
  bandwidth_mbps: number;
  cpu_utilization: number;
  ram_utilization: number;
  host_id: number | null;
}

export interface PhysicalServer {
  id: number;
  cpu_cores: number;
  cpu_frequency_ghz: number;
  ram_mb: number;
  storage_gb: number;
  bandwidth_mbps: number;
  power_state: 'ACTIVE' | 'SLEEP' | 'OFF';
  temperature: number;
  cpu_utilization: number;
  ram_utilization: number;
  storage_utilization: number;
  bandwidth_utilization: number;
  power_consumption: number;
  vms: VirtualMachine[];
}

export interface Telemetry {
  tick: number;
  total_hosts: number;
  active_hosts: number;
  sleeping_hosts: number;
  off_hosts: number;
  total_vms: number;
  it_power_w: number;
  cooling_power_w: number;
  total_power_w: number;
  total_energy_kwh: number;
  energy_cost_usd: number;
  cooling_cost_usd: number;
  carbon_emissions_kg: number;
  average_cpu_utilization: number;
  average_ram_utilization: number;
}

export interface Task {
  id: number;
  cpu_requirement: number;
  ram_requirement: number;
  storage_requirement: number;
  bandwidth_requirement: number;
  priority: 'HIGH' | 'MEDIUM' | 'LOW';
  execution_time: number; // remaining ticks
  deadline: number;
  arrival_time: number;
  status: 'WAITING' | 'RUNNING' | 'COMPLETED' | 'FAILED';
  vm_id: number | null;
}
