"""
Energy Calculator for the Energy-Aware Dynamic Task Scheduling Framework.
Integrates power over time intervals and tracks active, idle, sleep, and wake-up energy across the fleet.
"""

from typing import List, Dict, Any, Optional
from src.models.server import Server, ServerState
from src.energy.power_model import PowerModel


class EnergyCalculator:
    """
    Maintains energy ledger for individual servers and the aggregate fleet over the simulation lifecycle.
    """
    def __init__(self, servers: List[Server]):
        self.servers = servers
        # Energy metrics stored in Watt-hours (Wh)
        self.server_energy: Dict[str, Dict[str, float]] = {
            s.server_id: {
                "active_wh": 0.0,
                "idle_wh": 0.0,
                "sleep_wh": 0.0,
                "wakeup_wh": 0.0,
                "total_wh": 0.0
            }
            for s in servers
        }
        # Time-series log for plotting power and cumulative energy over time
        self.history: List[Dict[str, Any]] = []

    def record_interval(self, current_time: float, delta_time: float):
        """
        Integrates power consumption for all servers over the interval delta_time (in seconds).
        Energy (Wh) = Power (W) * (delta_time / 3600.0)
        """
        if delta_time <= 0.0:
            return

        interval_hours = delta_time / 3600.0
        fleet_power = 0.0
        fleet_active_count = 0
        fleet_idle_count = 0
        fleet_sleep_count = 0

        for server in self.servers:
            power = PowerModel.calculate_power(server)
            fleet_power += power
            interval_energy = power * interval_hours
            ledger = self.server_energy[server.server_id]

            if server.state == ServerState.ACTIVE:
                # Apportion between base idle and active dynamic load
                base_idle_energy = server.idle_power * interval_hours
                dynamic_energy = max(0.0, interval_energy - base_idle_energy)
                ledger["active_wh"] += dynamic_energy
                ledger["idle_wh"] += base_idle_energy
                fleet_active_count += 1
            elif server.state == ServerState.IDLE:
                ledger["idle_wh"] += interval_energy
                fleet_idle_count += 1
            elif server.state == ServerState.SLEEPING:
                ledger["sleep_wh"] += interval_energy
                fleet_sleep_count += 1
            elif server.state == ServerState.WAKING:
                ledger["idle_wh"] += interval_energy
                fleet_active_count += 1

            ledger["total_wh"] = (
                ledger["active_wh"]
                + ledger["idle_wh"]
                + ledger["sleep_wh"]
                + ledger["wakeup_wh"]
            )

        # Record snapshot in history
        total_fleet_energy_wh = sum(l["total_wh"] for l in self.server_energy.values())
        self.history.append({
            "timestamp": current_time,
            "fleet_power_w": fleet_power,
            "fleet_energy_wh": total_fleet_energy_wh,
            "fleet_energy_joules": total_fleet_energy_wh * 3600.0,
            "active_servers": fleet_active_count,
            "idle_servers": fleet_idle_count,
            "sleeping_servers": fleet_sleep_count,
        })

    def record_wakeup(self, server: Server):
        """
        Records the wake-up overhead penalty when a server transitions from SLEEPING to ACTIVE/WAKING.
        Overhead energy in Joules converted to Wh: 1 Wh = 3600 J.
        """
        wakeup_wh = server.wake_up_energy / 3600.0
        self.server_energy[server.server_id]["wakeup_wh"] += wakeup_wh
        self.server_energy[server.server_id]["total_wh"] += wakeup_wh

    @property
    def total_fleet_energy_wh(self) -> float:
        """Returns the total energy consumed by the entire simulated server fleet in Wh."""
        return sum(l["total_wh"] for l in self.server_energy.values())

    @property
    def total_fleet_energy_joules(self) -> float:
        """Returns total fleet energy in Joules (1 Wh = 3600 J)."""
        return self.total_fleet_energy_wh * 3600.0

    def get_server_breakdown(self, server_id: str) -> Dict[str, float]:
        """Returns detailed energy breakdown for a specific server."""
        return self.server_energy.get(server_id, {
            "active_wh": 0.0, "idle_wh": 0.0, "sleep_wh": 0.0, "wakeup_wh": 0.0, "total_wh": 0.0
        })

    def get_fleet_breakdown(self) -> Dict[str, float]:
        """Returns total fleet energy grouped by active, idle, sleep, and wakeup components."""
        active_sum = sum(l["active_wh"] for l in self.server_energy.values())
        idle_sum = sum(l["idle_wh"] for l in self.server_energy.values())
        sleep_sum = sum(l["sleep_wh"] for l in self.server_energy.values())
        wakeup_sum = sum(l["wakeup_wh"] for l in self.server_energy.values())
        total_sum = active_sum + idle_sum + sleep_sum + wakeup_sum

        return {
            "active_energy_wh": active_sum,
            "idle_energy_wh": idle_sum,
            "sleep_energy_wh": sleep_sum,
            "wakeup_overhead_wh": wakeup_sum,
            "total_energy_wh": total_sum,
            "total_energy_joules": total_sum * 3600.0
        }

    def reset(self):
        """Resets all energy ledgers and history."""
        for s_id in self.server_energy:
            self.server_energy[s_id] = {
                "active_wh": 0.0,
                "idle_wh": 0.0,
                "sleep_wh": 0.0,
                "wakeup_wh": 0.0,
                "total_wh": 0.0
            }
        self.history.clear()
