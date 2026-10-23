"""
Base Scheduler abstract interface for the Energy-Aware Dynamic Task Scheduling Framework.
Defines the standard contract, feasibility checks, and safe fallback handling.
"""

from abc import ABC, abstractmethod
from typing import List, Tuple, Optional, Dict, Any
from src.models.task import Task
from src.models.server import Server, ServerState
from src.utils.logging_config import setup_logger, log_diagnostic_event


class BaseScheduler(ABC):
    """
    Abstract base class for all scheduling strategies.
    Ensures identical inputs, resource constraint enforcement, and transparent fallback capabilities.
    """
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.fallback_scheduler: Optional["BaseScheduler"] = None
        self.logger = setup_logger()

    def get_feasible_servers(self, task: Task, servers: List[Server]) -> List[Server]:
        """
        Filters servers that can accommodate the task's CPU and memory demand and are not unavailable.
        """
        feasible = []
        for server in servers:
            if server.state != ServerState.UNAVAILABLE and server.can_accommodate(task.cpu_demand, task.memory_demand):
                feasible.append(server)
        return feasible

    @abstractmethod
    def select_server(self, task: Task, servers: List[Server], current_time: float) -> Optional[Server]:
        """
        Selects the best feasible server for a single task according to the algorithm's strategy.
        Returns None if no feasible server is found.
        """
        pass

    def schedule_tasks(
        self,
        pending_tasks: List[Task],
        servers: List[Server],
        current_time: float
    ) -> List[Tuple[Task, Server]]:
        """
        Schedules a batch of pending tasks.
        Includes automatic self-healing fallback if an unexpected algorithm error occurs.
        """
        allocations: List[Tuple[Task, Server]] = []

        # Sort tasks by arrival time by default for consistent ordering
        sorted_tasks = sorted(pending_tasks, key=lambda t: (t.arrival_time, -t.priority))

        for task in sorted_tasks:
            try:
                chosen_server = self.select_server(task, servers, current_time)
            except Exception as e:
                # Self-healing fallback mechanism
                log_diagnostic_event(
                    event_type="FALLBACK_TRIGGERED",
                    message=f"Scheduler {self.name} encountered error during task {task.task_id} selection: {str(e)}",
                    details={"task_id": task.task_id, "scheduler": self.name, "error": str(e)}
                )
                if self.fallback_scheduler is not None:
                    chosen_server = self.fallback_scheduler.select_server(task, servers, current_time)
                else:
                    # Emergency fallback: pick first feasible server
                    feasible = self.get_feasible_servers(task, servers)
                    chosen_server = feasible[0] if feasible else None

            if chosen_server is not None:
                allocations.append((task, chosen_server))
                # Temporarily reserve resources so next tasks in the same batch observe updated capacity
                chosen_server.allocated_cpu += task.cpu_demand
                chosen_server.allocated_memory += task.memory_demand

        # Release temporary reservations so the simulation engine can perform official allocation
        for task, server in allocations:
            server.allocated_cpu = max(0.0, server.allocated_cpu - task.cpu_demand)
            server.allocated_memory = max(0.0, server.allocated_memory - task.memory_demand)

        return allocations

    def reset(self):
        """Resets any internal scheduler state between experiment runs."""
        pass

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name='{self.name}'>"
