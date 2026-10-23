"""
Mathematical Power Model for simulated data center servers.
Implements the non-linear dynamic power scaling model:
    P(u) = P_idle + (P_max - P_idle) * (u ^ alpha)
"""

from typing import Union
from src.models.server import Server, ServerState


class PowerModel:
    """
    Computes instantaneous power consumption of a server based on utilization and operational state.
    """

    @staticmethod
    def calculate_power(server: Server, custom_utilization: float = None) -> float:
        """
        Calculates instantaneous power in Watts.
        If custom_utilization is provided, evaluates power at that hypothetical load.
        """
        if server.state == ServerState.UNAVAILABLE:
            return 0.0

        if server.state == ServerState.SLEEPING:
            return server.sleep_power

        # For ACTIVE, IDLE, or WAKING states:
        u = server.cpu_utilization if custom_utilization is None else custom_utilization
        u = min(1.0, max(0.0, float(u)))

        # P(u) = P_idle + (P_max - P_idle) * (u ^ alpha)
        dynamic_power = (server.max_power - server.idle_power) * (u ** server.alpha)
        return server.idle_power + dynamic_power

    @staticmethod
    def calculate_marginal_power(server: Server, additional_cpu: float) -> float:
        """
        Calculates the incremental increase in power (Watts) if additional CPU load is assigned.
        Returns Delta P = P(u_new) - P(u_current).
        """
        current_u = server.cpu_utilization
        new_cpu = min(server.cpu_capacity, server.allocated_cpu + additional_cpu)
        new_u = new_cpu / server.cpu_capacity if server.cpu_capacity > 0 else 0.0

        p_current = PowerModel.calculate_power(server, custom_utilization=current_u)
        
        # If server is sleeping, waking it up causes it to consume at least idle power + dynamic power
        if server.state == ServerState.SLEEPING:
            p_hypothetical_active = server.idle_power + (server.max_power - server.idle_power) * (new_u ** server.alpha)
            return p_hypothetical_active - server.sleep_power

        p_new = PowerModel.calculate_power(server, custom_utilization=new_u)
        return max(0.0, p_new - p_current)
