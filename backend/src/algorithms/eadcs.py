"""
Energy-Aware Dynamic Consolidation Scheduler (EADCS).
Multi-objective heuristic optimizing energy consumption, completion latency, deadline risk,
workload consolidation, state transitions, and resource fragmentation.
"""

from typing import List, Optional, Dict, Any
from src.algorithms.base_scheduler import BaseScheduler
from src.algorithms.fcfs import FCFSScheduler
from src.models.task import Task
from src.models.server import Server, ServerState
from src.energy.power_model import PowerModel
from src.utils.logging_config import setup_logger, log_diagnostic_event


class EADCSScheduler(BaseScheduler):
    """
    Energy-Aware Dynamic Consolidation Scheduler (EADCS).
    
    Evaluates every feasible server using a normalized multi-objective cost function:
        Cost = w_E * C_energy
             + w_T * C_time
             + w_D * C_deadline
             + w_L * C_load
             + w_S * C_state
             + w_F * C_frag

    Features:
    - Workload consolidation onto active servers to allow idle servers to sleep.
    - Wake-up penalty consideration to prevent needless state toggling.
    - Overload prevention when utilization approaches saturation.
    - Multi-dimensional resource alignment to reduce fragmentation.
    - Transparent fallback to FCFS on unforeseen computational errors.
    """
    def __init__(
        self,
        weights: Optional[Dict[str, float]] = None,
        target_cpu_utilization: float = 0.80,
        overload_cpu_threshold: float = 0.90
    ):
        super().__init__(
            name="EADCS",
            description="Energy-Aware Dynamic Consolidation: Multi-objective scheduler optimizing energy, consolidation, and deadlines."
        )
        self.fallback_scheduler = FCFSScheduler()

        # Configurable objective weights (normalized)
        default_weights = {
            "w_energy": 0.40,
            "w_time": 0.20,
            "w_deadline": 0.15,
            "w_load": 0.10,
            "w_state": 0.10,
            "w_frag": 0.05
        }
        self.weights = weights if weights is not None else default_weights
        self._normalize_weights()

        self.target_cpu_utilization = float(target_cpu_utilization)
        self.overload_cpu_threshold = float(overload_cpu_threshold)

    def _normalize_weights(self):
        """Ensures the sum of weights equals 1.0 for balanced multi-objective scoring."""
        total = sum(self.weights.values())
        if total <= 0.0:
            # Revert to defaults if invalid
            self.weights = {
                "w_energy": 0.40, "w_time": 0.20, "w_deadline": 0.15,
                "w_load": 0.10, "w_state": 0.10, "w_frag": 0.05
            }
        else:
            self.weights = {k: v / total for k, v in self.weights.items()}

    def update_weights(self, new_weights: Dict[str, float]):
        """Updates objective weights at runtime."""
        self.weights.update(new_weights)
        self._normalize_weights()

    def calculate_assignment_cost(
        self,
        task: Task,
        server: Server,
        current_time: float
    ) -> float:
        """
        Evaluates the composite normalized cost of assigning 'task' to 'server'.
        Lower cost indicates a more desirable allocation.
        """
        # 1. Normalized Energy Cost (C_energy)
        # Evaluates incremental power delta + wake-up energy if server must be powered on
        marginal_power = PowerModel.calculate_marginal_power(server, task.cpu_demand)
        norm_energy = marginal_power / max(server.max_power, 1.0)
        if server.state == ServerState.SLEEPING:
            # Add normalized wake-up energy penalty (Joules normalized over 1000J reference)
            norm_energy += min(1.0, server.wake_up_energy / 1000.0)
        norm_energy = min(2.0, max(0.0, norm_energy))

        # 2. Normalized Completion Time Cost (C_time)
        # Includes wake-up delay if server is currently asleep
        startup_delay = server.wake_up_delay if server.state == ServerState.SLEEPING else 0.0
        est_completion = current_time + startup_delay + task.duration
        norm_time = min(1.0, (startup_delay + task.duration) / max(task.duration * 2.0, 10.0))

        # 3. Deadline Risk Penalty (C_deadline)
        norm_deadline = 0.0
        if task.deadline is not None:
            slack = task.deadline - est_completion
            if slack < 0.0:
                # Deadline missed: severe penalty proportional to lateness
                norm_deadline = 1.0 + abs(slack) / max(task.duration, 1.0)
            elif slack < task.duration * 0.5:
                # Tight deadline: moderate penalty
                norm_deadline = 1.0 - (slack / max(task.duration * 0.5, 1e-3))
            else:
                norm_deadline = 0.0

        # 4. Load-Imbalance & Consolidation Cost (C_load)
        # We want to encourage consolidation up to target_cpu_utilization (~80%),
        # but strongly discourage exceeding overload threshold (>90%).
        hypothetical_cpu = server.allocated_cpu + task.cpu_demand
        u_new = hypothetical_cpu / server.cpu_capacity if server.cpu_capacity > 0 else 1.0

        if u_new > self.overload_cpu_threshold:
            # Overload penalty: scales steeply above 90%
            norm_load = 1.0 + 4.0 * (u_new - self.overload_cpu_threshold)
        elif u_new <= self.target_cpu_utilization:
            # Consolidation incentive: higher utilization on active server = lower cost
            # (1.0 - u_new) is minimized as u_new approaches target
            norm_load = max(0.0, 1.0 - u_new)
        else:
            # Sweet spot between target (0.80) and overload (0.90)
            norm_load = (u_new - self.target_cpu_utilization) / (self.overload_cpu_threshold - self.target_cpu_utilization)

        # 5. Server State Transition Penalty (C_state)
        # Active servers incur zero transition penalty.
        # Idle servers (already warm) incur mild penalty.
        # Sleeping servers incur significant penalty to discourage waking them up needlessly.
        if server.state == ServerState.ACTIVE:
            norm_state = 0.0
        elif server.state == ServerState.IDLE:
            norm_state = 0.15
        elif server.state == ServerState.SLEEPING:
            norm_state = 1.0
        else:
            norm_state = 2.0

        # 6. Resource Fragmentation Penalty (C_frag)
        # Evaluates disparity between remaining CPU ratio and remaining Memory ratio
        rem_cpu = max(0.0, server.cpu_capacity - hypothetical_cpu)
        rem_mem = max(0.0, server.memory_capacity - (server.allocated_memory + task.memory_demand))
        cpu_ratio = rem_cpu / server.cpu_capacity if server.cpu_capacity > 0 else 0.0
        mem_ratio = rem_mem / server.memory_capacity if server.memory_capacity > 0 else 0.0
        norm_frag = abs(cpu_ratio - mem_ratio)

        # Multi-objective weighted sum
        total_cost = (
            self.weights["w_energy"] * norm_energy
            + self.weights["w_time"] * norm_time
            + self.weights["w_deadline"] * norm_deadline
            + self.weights["w_load"] * norm_load
            + self.weights["w_state"] * norm_state
            + self.weights["w_frag"] * norm_frag
        )
        return total_cost

    def select_server(self, task: Task, servers: List[Server], current_time: float) -> Optional[Server]:
        feasible = self.get_feasible_servers(task, servers)
        if not feasible:
            return None

        # Prioritize active/warm feasible servers if they have safe capacity to maximize consolidation
        best_server = None
        best_cost = float("inf")

        for server in feasible:
            cost = self.calculate_assignment_cost(task, server, current_time)
            if cost < best_cost:
                best_cost = cost
                best_server = server

        return best_server
