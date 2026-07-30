import type { PhysicalServer, VirtualMachine, Telemetry, Task } from '../types/simulation';
import type { GlobalTelemetryLog, HostTelemetryLog, DataCenterPowerProfile, PowerSummary, PUEHistoryPoint } from '../types/monitoring';

const API_BASE_URL = 'http://localhost:8000/api';

class SimulationService {
  /**
   * Helper to retrieve auth headers.
   */
  private getHeaders(): HeadersInit {
    const token = localStorage.getItem('token');
    return {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token || ''}`,
    };
  }

  private async request(url: string, options: RequestInit = {}): Promise<Response> {
    const headers = this.getHeaders();
    const res = await fetch(url, { ...options, headers: { ...headers, ...options.headers } });
    if (res.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('username');
      localStorage.removeItem('role');
      window.location.reload();
      throw new Error('Session expired or unauthorized. Please log in again.');
    }
    return res;
  }

  /** Fetch all physical hosts. */
  async getServers(): Promise<PhysicalServer[]> {
    const response = await this.request(`${API_BASE_URL}/simulation/servers`);
    if (!response.ok) throw new Error('Failed to retrieve physical servers status.');
    return response.json();
  }

  /** Fetch all Virtual Machines. */
  async getVms(): Promise<VirtualMachine[]> {
    const response = await this.request(`${API_BASE_URL}/simulation/vms`);
    if (!response.ok) throw new Error('Failed to retrieve virtual machines list.');
    return response.json();
  }

  /** Update host power state. */
  async updatePowerState(hostId: number, powerState: 'ACTIVE' | 'SLEEP' | 'OFF'): Promise<PhysicalServer> {
    const response = await this.request(`${API_BASE_URL}/simulation/servers/${hostId}/power`, {
      method: 'POST',
      body: JSON.stringify({ power_state: powerState }),
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to update server power state.');
    }
    return response.json();
  }

  /** Deploy VM on host. */
  async deployVm(
    hostId: number,
    vmData: { cpu_cores: number; ram_mb: number; storage_gb: number; bandwidth_mbps: number }
  ): Promise<VirtualMachine> {
    const response = await this.request(`${API_BASE_URL}/simulation/servers/${hostId}/deploy-vm`, {
      method: 'POST',
      body: JSON.stringify(vmData),
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to deploy virtual machine.');
    }
    return response.json();
  }

  /** Decommission/destroy a VM. */
  async destroyVm(vmId: number): Promise<void> {
    const response = await this.request(`${API_BASE_URL}/simulation/vms/${vmId}`, {
      method: 'DELETE',
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to decommission virtual machine.');
    }
  }

  /** Trigger simulation tick loop. */
  async tick(): Promise<Telemetry> {
    const response = await this.request(`${API_BASE_URL}/simulation/tick`, {
      method: 'POST',
    });
    if (!response.ok) throw new Error('Failed to advance simulation step.');
    return response.json();
  }

  /** Fetch current telemetry state. */
  async getTelemetry(): Promise<Telemetry> {
    const response = await this.request(`${API_BASE_URL}/simulation/telemetry`);
    if (!response.ok) throw new Error('Failed to retrieve telemetry stats.');
    return response.json();
  }

  /** Generate synthetic workloads. */
  async generateWorkload(count: number): Promise<Task[]> {
    const response = await this.request(`${API_BASE_URL}/simulation/workload/generate`, {
      method: 'POST',
      body: JSON.stringify({ count }),
    });
    if (!response.ok) throw new Error('Failed to generate workload tasks.');
    return response.json();
  }

  /** Fetch all tasks. */
  async getTasks(): Promise<Task[]> {
    const response = await this.request(`${API_BASE_URL}/simulation/tasks`);
    if (!response.ok) throw new Error('Failed to retrieve task queue.');
    return response.json();
  }

  /** Fetch global time-series telemetry logs for analytics charting. */
  async getGlobalLogs(limit = 200): Promise<GlobalTelemetryLog[]> {
    const response = await this.request(`${API_BASE_URL}/simulation/monitoring/global?limit=${limit}`);
    if (!response.ok) throw new Error('Failed to retrieve global telemetry logs.');
    return response.json();
  }

  /** Fetch per-host time-series telemetry logs for analytics charting. */
  async getHostLogs(hostId: number, limit = 200): Promise<HostTelemetryLog[]> {
    const response = await this.request(`${API_BASE_URL}/simulation/monitoring/hosts/${hostId}?limit=${limit}`);
    if (!response.ok) throw new Error(`Failed to retrieve telemetry logs for host ${hostId}.`);
    return response.json();
  }

  /** Fetch real-time power profile (PUE, per-host breakdown, history). */
  async getPowerProfile(): Promise<DataCenterPowerProfile> {
    const response = await this.request(`${API_BASE_URL}/simulation/power/profile`);
    if (!response.ok) throw new Error('Failed to retrieve power profile.');
    return response.json();
  }

  /** Fetch aggregate power summary only (lighter endpoint). */
  async getPowerSummary(): Promise<PowerSummary> {
    const response = await this.request(`${API_BASE_URL}/simulation/power/summary`);
    if (!response.ok) throw new Error('Failed to retrieve power summary.');
    return response.json();
  }

  /** Fetch PUE history time-series [{tick, pue}]. */
  async getPUEHistory(): Promise<PUEHistoryPoint[]> {
    const response = await this.request(`${API_BASE_URL}/simulation/power/pue-history`);
    if (!response.ok) throw new Error('Failed to retrieve PUE history.');
    return response.json();
  }

  /** Fetch active resource scheduler strategy. */
  async getActiveScheduler(): Promise<{ active_scheduler: string; supported_schedulers: string[] }> {
    const response = await this.request(`${API_BASE_URL}/scheduler/active`);
    if (!response.ok) throw new Error('Failed to retrieve active scheduler state.');
    return response.json();
  }

  /** Switch active resource scheduler strategy. */
  async selectScheduler(name: string): Promise<{ active_scheduler: string; message: string }> {
    const response = await this.request(`${API_BASE_URL}/scheduler/select`, {
      method: 'POST',
      body: JSON.stringify({ name }),
    });
    if (!response.ok) throw new Error('Failed to change scheduler algorithm.');
    return response.json();
  }

  /** Trigger manual VM consolidation pass across hosts. */
  async consolidateVms(): Promise<{ hosts_transitioned_to_sleep: number; message: string }> {
    const response = await this.request(`${API_BASE_URL}/scheduler/consolidate`, {
      method: 'POST',
    });
    if (!response.ok) throw new Error('Failed to run VM consolidation.');
    return response.json();
  }

  /** Fetch executive summary statistics report. */
  async getSummaryReport(): Promise<any> {
    const response = await this.request(`${API_BASE_URL}/reports/summary`);
    if (!response.ok) throw new Error('Failed to load executive summary report.');
    return response.json();
  }

  /** Trigger direct CSV telemetry download. */
  async downloadCsvReport(): Promise<void> {
    const response = await this.request(`${API_BASE_URL}/reports/export/csv`);
    if (!response.ok) throw new Error('Failed to export CSV report.');
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'datacenter_telemetry_report.csv';
    document.body.appendChild(a);
    a.click();
    a.remove();
  }

  /** Trigger direct JSON simulation snapshot download. */
  async downloadJsonReport(): Promise<void> {
    const response = await this.request(`${API_BASE_URL}/reports/export/json`);
    if (!response.ok) throw new Error('Failed to export JSON report.');
    const data = await response.json();
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'datacenter_simulation_snapshot.json';
    document.body.appendChild(a);
    a.click();
    a.remove();
  }
}

export const simulationService = new SimulationService();

