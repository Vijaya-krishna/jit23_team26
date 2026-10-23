"""
Load-Balancing Baseline Scheduler.
Allocates tasks to the least-utilized feasible server to evenly distribute load across the fleet.
"""

from typing import List, Optional
from src.algorithms.base_scheduler import BaseScheduler
from src.models.task import Task
from src.models.server import Server


class LoadBalancingScheduler(BaseScheduler):
    """
    Load-balancing heuristic: for each pending task, finds all feasible servers and selects
    the server with the minimum current CPU utilization (breaking ties with memory utilization).
    While this minimizes load variance and hotspots, it tends to activate and keep many servers
    running at low utilization, incurring high idle energy penalties.
    """
    def __init__(self):
        super().__init__(
            name="Load Balancing",
            description="Load Balancing: Spreads tasks across the fleet by selecting the least-utilized feasible server."
        )

    def select_server(self, task: Task, servers: List[Server], current_time: float) -> Optional[Server]:
        feasible = self.get_feasible_servers(task, servers)
        if not feasible:
            return None

        # Sort feasible servers by current CPU utilization ascending, then memory utilization ascending
        best_server = min(
            feasible,
            key=lambda s: (s.cpu_utilization, s.memory_utilization, s.server_id)
        )
        return best_server
