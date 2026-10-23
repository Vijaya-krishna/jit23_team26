"""
Server model for the Energy-Aware Dynamic Task Scheduling Framework.
Represents a heterogeneous physical or virtual server host in the data center.
"""

from enum import Enum
from typing import Dict, Optional, Any, List
from src.models.task import Task
from src.utils.exceptions import ResourceConstraintViolation, ValidationError, InvalidStateTransitionError


class ServerState(str, Enum):
    ACTIVE = "active"          # Has running tasks
    IDLE = "idle"              # Powered on, zero running tasks
    SLEEPING = "sleeping"      # Low-power sleep state (minimal energy)
    WAKING = "waking"          # Transitioning from sleeping to active (consuming wake-up overhead)
    UNAVAILABLE = "unavailable"# Offline or undergoing maintenance


class Server:
    """
    Simulated server node with configurable resource capacity and power characteristics.
    """
    def __init__(
        self,
        server_id: str,
        cpu_capacity: float,
        memory_capacity: float,
        idle_power: float,
        max_power: float,
        sleep_power: float = 10.0,
        wake_up_energy: float = 500.0, # Joules
        wake_up_delay: float = 5.0,    # Simulated seconds
        alpha: float = 1.5,
        idle_timeout_to_sleep: float = 15.0, # seconds of idle before auto-sleeping
        initial_state: ServerState = ServerState.IDLE
    ):
        if not server_id or not str(server_id).strip():
            raise ValidationError("Server ID cannot be empty.")
        if cpu_capacity <= 0.0 or memory_capacity <= 0.0:
            raise ValidationError("Server CPU and Memory capacities must be strictly positive.")
        if idle_power < 0.0 or max_power < 0.0:
            raise ValidationError("Server power parameters cannot be negative.")
        if idle_power > max_power:
            raise ValidationError(
                f"Server {server_id}: Idle power ({idle_power}W) cannot exceed maximum power ({max_power}W)."
            )
        if sleep_power < 0.0:
            raise ValidationError(f"Server {server_id}: Sleep power cannot be negative.")
        if sleep_power > idle_power:
            raise ValidationError(
                f"Server {server_id}: Sleep power ({sleep_power}W) should not exceed idle power ({idle_power}W)."
            )
        if wake_up_energy < 0.0 or wake_up_delay < 0.0:
            raise ValidationError("Server wake up energy and delay must be non-negative.")
        if alpha < 1.0:
            raise ValidationError(f"Server power exponent alpha must be >= 1.0 (got {alpha}).")

        self.server_id = str(server_id).strip()
        self.cpu_capacity = float(cpu_capacity)
        self.memory_capacity = float(memory_capacity)
        self.idle_power = float(idle_power)
        self.max_power = float(max_power)
        self.sleep_power = float(sleep_power)
        self.wake_up_energy = float(wake_up_energy)  # Joules
        self.wake_up_delay = float(wake_up_delay)    # Seconds
        self.alpha = float(alpha)
        self.idle_timeout_to_sleep = float(idle_timeout_to_sleep)

        # Dynamic state
        self.state: ServerState = ServerState(initial_state)
        self.active_tasks: Dict[str, Task] = {}
        self.allocated_cpu: float = 0.0
        self.allocated_memory: float = 0.0
        self.last_state_change_time: float = 0.0
        self.idle_since_time: Optional[float] = 0.0 if self.state == ServerState.IDLE else None
        self.state_transitions_count: int = 0
        self.total_wake_ups: int = 0
        self.waking_until_time: Optional[float] = None

    @property
    def cpu_utilization(self) -> float:
        """Normalized CPU utilization between 0.0 and 1.0."""
        if self.cpu_capacity <= 0.0:
            return 0.0
        return min(1.0, max(0.0, self.allocated_cpu / self.cpu_capacity))

    @property
    def memory_utilization(self) -> float:
        """Normalized Memory utilization between 0.0 and 1.0."""
        if self.memory_capacity <= 0.0:
            return 0.0
        return min(1.0, max(0.0, self.allocated_memory / self.memory_capacity))

    @property
    def remaining_cpu(self) -> float:
        """Remaining free CPU units."""
        return max(0.0, self.cpu_capacity - self.allocated_cpu)

    @property
    def remaining_memory(self) -> float:
        """Remaining free Memory units."""
        return max(0.0, self.memory_capacity - self.allocated_memory)

    def can_accommodate(self, cpu_demand: float, memory_demand: float) -> bool:
        """Checks if server has sufficient remaining capacity and is available."""
        if self.state == ServerState.UNAVAILABLE:
            return False
        # Precision buffer for floating point comparisons
        return (self.remaining_cpu >= (cpu_demand - 1e-6)) and (self.remaining_memory >= (memory_demand - 1e-6))

    def allocate_task(self, task: Task, current_time: float):
        """Allocates resources for a task and updates server state."""
        if not self.can_accommodate(task.cpu_demand, task.memory_demand):
            raise ResourceConstraintViolation(
                f"Server {self.server_id} cannot accommodate Task {task.task_id} "
                f"(Needed: CPU={task.cpu_demand}, Mem={task.memory_demand} | "
                f"Available: CPU={self.remaining_cpu:.2f}, Mem={self.remaining_memory:.2f})."
            )
        if task.task_id in self.active_tasks:
            raise ResourceConstraintViolation(
                f"Task {task.task_id} is already allocated on Server {self.server_id}."
            )

        self.active_tasks[task.task_id] = task
        self.allocated_cpu += task.cpu_demand
        self.allocated_memory += task.memory_demand

        # State transition: if IDLE -> ACTIVE (if WAKING, remains WAKING until wake delay finishes)
        if self.state == ServerState.IDLE:
            self.set_state(ServerState.ACTIVE, current_time)
        self.idle_since_time = None

    def release_task(self, task_id: str, current_time: float) -> Optional[Task]:
        """Releases task resources and updates server state to IDLE if empty."""
        task = self.active_tasks.pop(task_id, None)
        if task is None:
            return None

        self.allocated_cpu = max(0.0, self.allocated_cpu - task.cpu_demand)
        self.allocated_memory = max(0.0, self.allocated_memory - task.memory_demand)

        # If all tasks finished, server becomes IDLE
        if len(self.active_tasks) == 0:
            self.allocated_cpu = 0.0
            self.allocated_memory = 0.0
            self.set_state(ServerState.IDLE, current_time)
            self.idle_since_time = current_time

        return task

    def set_state(self, new_state: ServerState, current_time: float):
        """Sets operating state with transition counting and logging."""
        if self.state != new_state:
            # Wake-up accounting
            if self.state == ServerState.SLEEPING and new_state in (ServerState.ACTIVE, ServerState.WAKING):
                self.total_wake_ups += 1
            self.state = new_state
            self.last_state_change_time = current_time
            self.state_transitions_count += 1
            if new_state == ServerState.IDLE:
                self.idle_since_time = current_time
            else:
                self.idle_since_time = None

    def reset(self, initial_state: ServerState = ServerState.IDLE):
        """Resets server state for repeated multi-scheduler experiments."""
        self.active_tasks.clear()
        self.allocated_cpu = 0.0
        self.allocated_memory = 0.0
        self.state = ServerState(initial_state)
        self.last_state_change_time = 0.0
        self.idle_since_time = 0.0 if self.state == ServerState.IDLE else None
        self.state_transitions_count = 0
        self.total_wake_ups = 0
        self.waking_until_time = None

    def to_dict(self) -> Dict[str, Any]:
        """Returns server metadata and current status."""
        return {
            "server_id": self.server_id,
            "cpu_capacity": self.cpu_capacity,
            "memory_capacity": self.memory_capacity,
            "allocated_cpu": self.allocated_cpu,
            "allocated_memory": self.allocated_memory,
            "cpu_utilization": self.cpu_utilization,
            "memory_utilization": self.memory_utilization,
            "idle_power": self.idle_power,
            "max_power": self.max_power,
            "sleep_power": self.sleep_power,
            "wake_up_energy": self.wake_up_energy,
            "wake_up_delay": self.wake_up_delay,
            "alpha": self.alpha,
            "state": self.state.value,
            "active_tasks_count": len(self.active_tasks),
            "state_transitions": self.state_transitions_count,
            "total_wake_ups": self.total_wake_ups
        }

    def __repr__(self) -> str:
        return f"<Server id={self.server_id} state={self.state.value} CPU={self.allocated_cpu:.1f}/{self.cpu_capacity:.1f} Mem={self.allocated_memory:.1f}/{self.memory_capacity:.1f}>"
