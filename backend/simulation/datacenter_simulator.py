from typing import Dict, Any, List, Optional
from backend.simulation.host import PhysicalHost
from backend.simulation.scheduler import BaseScheduler
from backend.simulation.vm import VirtualMachine

class DataCenterSimulator:
    """
    Main simulator orchestration engine.
    Manages in-memory hardware states, processes execution ticks, and gathers data center metrics.
    """
    def __init__(self, cooling_overhead_pct: float = 0.35):
        self.hosts: Dict[int, PhysicalHost] = {}
        self.vms: Dict[int, VirtualMachine] = {}
        self.cooling_overhead_pct = cooling_overhead_pct
        self.scheduler: BaseScheduler | None = None

        # Historical metrics tracker
        self.total_energy_kwh = 0.0
        self.tick_counter = 0

        # PUE history (one entry per tick)
        self.pue_history: list = []  # [{tick, pue}]

    def set_scheduler(self, scheduler: BaseScheduler) -> None:
        """Assign a scheduler instance to the simulator."""
        self.scheduler = scheduler

    def add_host(self, host: PhysicalHost) -> None:
        """
        Register a physical host in the datacenter.
        """
        self.hosts[host.host_id] = host

    def get_host(self, host_id: int) -> Optional[PhysicalHost]:
        """
        Retrieve a physical host by ID.
        """
        return self.hosts.get(host_id)

    def register_vm(self, vm: VirtualMachine, host_id: int) -> bool:
        """
        Attempt to register and place a VM on a specific host.
        """
        host = self.hosts.get(host_id)
        if not host:
            return False
            
        if host.add_vm(vm):
            self.vms[vm.vm_id] = vm
            return True
        return False

    def unregister_vm(self, vm_id: int) -> bool:
        """
        Find and delete a VM from its physical host.
        """
        vm = self.vms.get(vm_id)
        if not vm:
            return False
            
        if vm.host_id is not None:
            host = self.hosts.get(vm.host_id)
            if host:
                host.remove_vm(vm_id)
        self.vms.pop(vm_id, None)
        return True

    def tick(self) -> None:
        """
        Advance the clock of the entire datacenter by one step.
        Executes hardware checks, power draw updates, and accumulates dynamic metrics.
        """
        # Apply scheduling before ticking hosts
        if self.scheduler:
            self.scheduler.schedule(list(self.hosts.values()), list(self.vms.values()))
        total_it_power_watts = 0.0

        for host in self.hosts.values():
            host.tick()
            total_it_power_watts += host.get_power_consumption()

        self.tick_counter += 1

        # Accumulate energy consumption: kWh = W * 1s / 3_600_000
        self.total_energy_kwh += (total_it_power_watts * 1.0) / 3_600_000.0

        # Compute and record PUE for this tick
        # PUE = Total Facility Power / IT Equipment Power  (must be >= 1.0)
        cooling_power = total_it_power_watts * self.cooling_overhead_pct
        total_facility_power = total_it_power_watts + cooling_power
        pue = (total_facility_power / total_it_power_watts) if total_it_power_watts > 0 else 1.0
        self.pue_history.append({"tick": self.tick_counter, "pue": round(pue, 4)})

    def get_telemetry(self) -> Dict[str, Any]:
        """
        Collect aggregate data center performance, power, and environmental telemetry metrics.
        """
        total_hosts = len(self.hosts)
        active_hosts = sum(1 for h in self.hosts.values() if h.power_state == "ACTIVE")
        sleeping_hosts = sum(1 for h in self.hosts.values() if h.power_state == "SLEEP")
        off_hosts = sum(1 for h in self.hosts.values() if h.power_state == "OFF")

        total_it_power = sum(h.get_power_consumption() for h in self.hosts.values())
        cooling_power = total_it_power * self.cooling_overhead_pct
        total_power = total_it_power + cooling_power

        # Resource aggregates (averaged across ACTIVE hosts)
        active_server_list = [h for h in self.hosts.values() if h.power_state == "ACTIVE"]
        avg_cpu_util = sum(h.cpu_utilization for h in active_server_list) / len(active_server_list) if active_server_list else 0.0
        avg_ram_util = sum(h.ram_utilization for h in active_server_list) / len(active_server_list) if active_server_list else 0.0

        # Carbon Emissions estimation: Standard grid multiplier (e.g. 0.4 kg CO2 per kWh)
        carbon_emissions_kg = self.total_energy_kwh * 0.4
        
        # Cooling cost estimation: Standard utility electricity rate (e.g. $0.12 per kWh)
        energy_cost_usd = self.total_energy_kwh * 0.12
        cooling_cost_usd = (self.total_energy_kwh * self.cooling_overhead_pct) * 0.12

        return {
            "tick": self.tick_counter,
            "total_hosts": total_hosts,
            "active_hosts": active_hosts,
            "sleeping_hosts": sleeping_hosts,
            "off_hosts": off_hosts,
            "total_vms": len(self.vms),
            "it_power_w": total_it_power,
            "cooling_power_w": cooling_power,
            "total_power_w": total_power,
            "total_energy_kwh": self.total_energy_kwh,
            "energy_cost_usd": energy_cost_usd,
            "cooling_cost_usd": cooling_cost_usd,
            "carbon_emissions_kg": carbon_emissions_kg,
            "average_cpu_utilization": avg_cpu_util,
            "average_ram_utilization": avg_ram_util,
        }

    def get_power_profile(self) -> Dict[str, Any]:
        """
        Return detailed real-time power consumption profile for each host
        and an aggregated facility-level summary including PUE.
        """
        host_profiles = []
        total_it_w = 0.0
        total_standby_w = 0.0

        for host in self.hosts.values():
            current_w = host.get_power_consumption()
            total_it_w += current_w

            # Introspect power model metadata
            pm = host.power_model
            model_name = getattr(pm, 'model_name', 'Linear')
            idle_w = getattr(pm, 'idle_power', 80.0)
            peak_w = getattr(pm, 'peak_power', 250.0)
            standby_w = getattr(pm, 'standby_power_w', 5.0)

            if host.power_state == "OFF":
                total_standby_w += current_w

            host_profiles.append({
                "host_id": host.host_id,
                "power_state": host.power_state,
                "model_name": model_name,
                "idle_power_w": idle_w,
                "peak_power_w": peak_w,
                "standby_power_w": standby_w,
                "current_power_w": round(current_w, 3),
                "cpu_utilization": round(host.cpu_utilization, 4),
                "efficiency_pct": round((current_w / peak_w * 100) if peak_w > 0 else 0, 1),
            })

        cooling_w = total_it_w * self.cooling_overhead_pct
        total_facility_w = total_it_w + cooling_w
        pue = (total_facility_w / total_it_w) if total_it_w > 0 else 1.0

        # PUE rating string based on industry thresholds
        if pue <= 1.2:
            pue_rating = "Excellent (Green)"
        elif pue <= 1.5:
            pue_rating = "Good (Efficient)"
        elif pue <= 1.8:
            pue_rating = "Average (Industry)"
        else:
            pue_rating = "Poor (Inefficient)"

        return {
            "summary": {
                "pue": round(pue, 4),
                "pue_rating": pue_rating,
                "it_power_w": round(total_it_w, 3),
                "cooling_power_w": round(cooling_w, 3),
                "standby_power_w": round(total_standby_w, 3),
                "total_facility_w": round(total_facility_w, 3),
                "cooling_overhead_pct": self.cooling_overhead_pct * 100,
            },
            "hosts": host_profiles,
            "pue_history": self.pue_history[-100:],  # Last 100 ticks
        }
