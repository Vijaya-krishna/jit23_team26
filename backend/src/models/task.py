"""
Task model for the Energy-Aware Dynamic Task Scheduling Framework.
Represents a discrete computational unit in big data workloads.
"""

from enum import Enum
from typing import Optional, Dict, Any
from src.utils.exceptions import InvalidStateTransitionError, ValidationError


class TaskState(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Task:
    """
    Represents an atomic task submitted to the data center for execution.
    """
    def __init__(
        self,
        task_id: str,
        name: str,
        arrival_time: float,
        cpu_demand: float,
        memory_demand: float,
        duration: float,
        priority: int = 5,
        deadline: Optional[float] = None,
        state: TaskState = TaskState.PENDING,
        assigned_server_id: Optional[str] = None
    ):
        if not task_id or not str(task_id).strip():
            raise ValidationError("Task ID cannot be empty.")
        if arrival_time < 0.0:
            raise ValidationError(f"Task {task_id}: Arrival time must be non-negative (got {arrival_time}).")
        if cpu_demand <= 0.0:
            raise ValidationError(f"Task {task_id}: CPU demand must be strictly positive (got {cpu_demand}).")
        if memory_demand <= 0.0:
            raise ValidationError(f"Task {task_id}: Memory demand must be strictly positive (got {memory_demand}).")
        if duration <= 0.0:
            raise ValidationError(f"Task {task_id}: Duration must be strictly positive (got {duration}).")
        if deadline is not None and deadline < arrival_time:
            raise ValidationError(
                f"Task {task_id}: Deadline ({deadline}) cannot be earlier than arrival time ({arrival_time})."
            )

        self.task_id = str(task_id).strip()
        self.name = str(name).strip() or f"Task_{self.task_id}"
        self.arrival_time = float(arrival_time)
        self.cpu_demand = float(cpu_demand)
        self.memory_demand = float(memory_demand)
        self.duration = float(duration)
        self.priority = int(priority)
        self.deadline = float(deadline) if deadline is not None else None

        # Dynamic simulation lifecycle state
        self.state: TaskState = TaskState(state)
        self.assigned_server_id: Optional[str] = assigned_server_id
        self.actual_start_time: Optional[float] = None
        self.actual_completion_time: Optional[float] = None
        self.energy_consumed: float = 0.0  # in Watt-hours (Wh)
        self.failure_reason: Optional[str] = None

    @property
    def waiting_time(self) -> Optional[float]:
        """Time spent waiting in queue before starting execution."""
        if self.actual_start_time is not None:
            return max(0.0, self.actual_start_time - self.arrival_time)
        return None

    @property
    def turnaround_time(self) -> Optional[float]:
        """Total time from arrival to completion."""
        if self.actual_completion_time is not None:
            return max(0.0, self.actual_completion_time - self.arrival_time)
        return None

    @property
    def is_deadline_missed(self) -> bool:
        """Determines if the task missed its scheduled deadline."""
        if self.deadline is None:
            return False
        if self.actual_completion_time is not None:
            return self.actual_completion_time > self.deadline
        return False

    def mark_running(self, start_time: float, server_id: str):
        """Transitions task from PENDING to RUNNING."""
        if self.state != TaskState.PENDING:
            raise InvalidStateTransitionError(
                f"Task {self.task_id} cannot transition to RUNNING from state {self.state}."
            )
        if start_time < self.arrival_time:
            raise InvalidStateTransitionError(
                f"Task {self.task_id} start time ({start_time}) cannot be earlier than arrival time ({self.arrival_time})."
            )
        self.state = TaskState.RUNNING
        self.actual_start_time = float(start_time)
        self.assigned_server_id = str(server_id)

    def mark_completed(self, completion_time: float, energy: float = 0.0):
        """Transitions task from RUNNING to COMPLETED."""
        if self.state != TaskState.RUNNING:
            raise InvalidStateTransitionError(
                f"Task {self.task_id} cannot transition to COMPLETED from state {self.state}."
            )
        if self.actual_start_time is not None and completion_time < self.actual_start_time:
            raise InvalidStateTransitionError(
                f"Task {self.task_id} completion time ({completion_time}) cannot be before start time ({self.actual_start_time})."
            )
        self.state = TaskState.COMPLETED
        self.actual_completion_time = float(completion_time)
        self.energy_consumed = float(energy)

    def mark_failed(self, fail_time: float, reason: str = "Allocation failure"):
        """Marks task as FAILED."""
        self.state = TaskState.FAILED
        self.actual_completion_time = float(fail_time)
        self.failure_reason = reason

    def reset(self):
        """Resets dynamic simulation state for reproducible multi-scheduler runs."""
        self.state = TaskState.PENDING
        self.assigned_server_id = None
        self.actual_start_time = None
        self.actual_completion_time = None
        self.energy_consumed = 0.0
        self.failure_reason = None

    def to_dict(self) -> Dict[str, Any]:
        """Serializes task record to dictionary for Pandas / CSV."""
        return {
            "task_id": self.task_id,
            "name": self.name,
            "arrival_time": self.arrival_time,
            "cpu_demand": self.cpu_demand,
            "memory_demand": self.memory_demand,
            "duration": self.duration,
            "priority": self.priority,
            "deadline": self.deadline,
            "state": self.state.value,
            "assigned_server_id": self.assigned_server_id,
            "actual_start_time": self.actual_start_time,
            "actual_completion_time": self.actual_completion_time,
            "waiting_time": self.waiting_time,
            "turnaround_time": self.turnaround_time,
            "energy_consumed_wh": self.energy_consumed,
            "missed_deadline": self.is_deadline_missed,
            "failure_reason": self.failure_reason
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        """Instantiates a Task from a dictionary or CSV row."""
        deadline_raw = data.get("deadline")
        deadline = None
        if deadline_raw is not None and str(deadline_raw).strip() != "" and str(deadline_raw).lower() != "nan":
            deadline = float(deadline_raw)

        return cls(
            task_id=str(data["task_id"]),
            name=str(data.get("name", f"Task_{data['task_id']}")),
            arrival_time=float(data["arrival_time"]),
            cpu_demand=float(data["cpu_demand"]),
            memory_demand=float(data["memory_demand"]),
            duration=float(data["duration"]),
            priority=int(data.get("priority", 5)),
            deadline=deadline
        )

    def __repr__(self) -> str:
        return f"<Task id={self.task_id} cpu={self.cpu_demand} mem={self.memory_demand} dur={self.duration} state={self.state.value}>"
