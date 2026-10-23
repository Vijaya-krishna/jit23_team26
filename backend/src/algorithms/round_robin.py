"""
Round Robin (RR) Baseline Scheduler.
Cycles sequentially through the fleet, allocating tasks to consecutive feasible servers.
"""

from typing import List, Optional
from src.algorithms.base_scheduler import BaseScheduler
from src.models.task import Task
from src.models.server import Server


class RoundRobinScheduler(BaseScheduler):
    """
    Round Robin dispatch policy: maintains an active cursor pointing to the last assigned server.
    For each incoming task, it examines servers in circular sequence starting from cursor + 1
    and assigns the task to the first feasible server found, updating the cursor.
    """
    def __init__(self):
        super().__init__(
            name="Round Robin",
            description="Round Robin: Dispatches tasks in circular sequence across the server fleet."
        )
        self.current_index = -1

    def select_server(self, task: Task, servers: List[Server], current_time: float) -> Optional[Server]:
        if not servers:
            return None

        n = len(servers)
        start_index = (self.current_index + 1) % n

        # Check all servers in circular order
        for offset in range(n):
            idx = (start_index + offset) % n
            server = servers[idx]
            if server.can_accommodate(task.cpu_demand, task.memory_demand):
                self.current_index = idx
                return server

        return None

    def reset(self):
        """Resets the circular pointer to initial state."""
        self.current_index = -1
