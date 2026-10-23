"""
Simulation events model for the discrete-event simulation engine.
Enables event-driven clock advancement with deterministic priority tie-breaking.
"""

from enum import Enum
from typing import Any, Dict


class EventType(str, Enum):
    TASK_ARRIVAL = "TASK_ARRIVAL"
    TASK_START = "TASK_START"
    TASK_COMPLETION = "TASK_COMPLETION"
    SERVER_WAKE_COMPLETE = "SERVER_WAKE_COMPLETE"
    SERVER_CHECK_SLEEP = "SERVER_CHECK_SLEEP"


class SimulationEvent:
    """
    Represents an atomic event in the discrete-event simulation timeline.
    Ordered by timestamp ascending, then priority ascending, then sequence id.
    """
    _counter = 0

    def __init__(
        self,
        timestamp: float,
        event_type: EventType,
        payload: Dict[str, Any],
        priority: int = 10
    ):
        self.timestamp = float(timestamp)
        self.event_type = EventType(event_type)
        self.payload = payload
        self.priority = int(priority)  # lower number = higher execution priority

        # Unique auto-increment counter to avoid unorderable dict comparison in heapq
        SimulationEvent._counter += 1
        self.seq_id = SimulationEvent._counter

    def __lt__(self, other: "SimulationEvent") -> bool:
        if self.timestamp != other.timestamp:
            return self.timestamp < other.timestamp
        if self.priority != other.priority:
            return self.priority < other.priority
        return self.seq_id < other.seq_id

    def __repr__(self) -> str:
        return f"<Event t={self.timestamp:.2f} type={self.event_type.value} prio={self.priority}>"
