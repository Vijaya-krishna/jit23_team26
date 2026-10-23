"""
First Come First Served (FCFS) Baseline Scheduler.
Assigns pending tasks in arrival order to the first available feasible server.
"""

from typing import List, Optional
from src.algorithms.base_scheduler import BaseScheduler
from src.models.task import Task
from src.models.server import Server


class FCFSScheduler(BaseScheduler):
    """
    Standard FCFS heuristic: tasks are processed in arrival order and placed onto the first
    feasible server encountered in the static server list.
    """
    def __init__(self):
        super().__init__(
            name="FCFS",
            description="First Come First Served: Dispatches tasks in arrival order to the first feasible server."
        )

    def select_server(self, task: Task, servers: List[Server], current_time: float) -> Optional[Server]:
        feasible = self.get_feasible_servers(task, servers)
        if not feasible:
            return None
        # First Come First Served places task on first feasible server in static list order
        return feasible[0]
