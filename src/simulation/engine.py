"""
Discrete-Event Simulation Engine for the Energy-Aware Dynamic Task Scheduling Framework.
Executes event-driven simulations with non-linear power modeling, dynamic sleep/wake transitions,
and strict resource capacity conservation invariants.
"""

import heapq
from typing import List, Dict, Any, Optional, Tuple
from src.models.task import Task, TaskState
from src.models.server import Server, ServerState
from src.algorithms.base_scheduler import BaseScheduler
from src.energy.energy_calculator import EnergyCalculator
from src.simulation.events import SimulationEvent, EventType
from src.utils.logging_config import setup_logger, log_diagnostic_event
from src.utils.exceptions import SimulationError, ResourceConstraintViolation


class SimulationResult:
    """
    Encapsulates all results, metrics, and logs from a completed simulation run.
    """
    def __init__(
        self,
        scheduler_name: str,
        tasks: List[Task],
        servers: List[Server],
        energy_calculator: EnergyCalculator,
        start_time: float,
        end_time: float,
        sim_metadata: Dict[str, Any] = None
    ):
        self.scheduler_name = scheduler_name
        self.tasks = tasks
        self.servers = servers
        self.energy_calculator = energy_calculator
        self.start_time = start_time
        self.end_time = end_time
        self.makespan = max(0.0, end_time - start_time)
        self.metadata = sim_metadata or {}

    @property
    def total_energy_wh(self) -> float:
        return self.energy_calculator.total_fleet_energy_wh

    @property
    def total_energy_joules(self) -> float:
        return self.energy_calculator.total_fleet_energy_joules

    @property
    def completed_tasks(self) -> List[Task]:
        return [t for t in self.tasks if t.state == TaskState.COMPLETED]

    @property
    def failed_tasks(self) -> List[Task]:
        return [t for t in self.tasks if t.state == TaskState.FAILED]

    @property
    def pending_tasks(self) -> List[Task]:
        return [t for t in self.tasks if t.state == TaskState.PENDING]


class SimulationEngine:
    """
    High-fidelity discrete-event simulator for cluster task scheduling.
    Advances simulation clock deterministically across events without thread sleeps.
    """
    def __init__(
        self,
        scheduler: BaseScheduler,
        servers: List[Server],
        tasks: List[Task],
        enable_sleep_state: bool = True,
        max_duration: float = 3600.0,
        idle_sleep_timeout: float = 15.0
    ):
        self.scheduler = scheduler
        self.servers = servers
        self.tasks = tasks
        self.enable_sleep_state = enable_sleep_state
        self.max_duration = max_duration
        self.idle_sleep_timeout = idle_sleep_timeout

        self.logger = setup_logger()
        self.current_time = 0.0
        self.event_queue: List[SimulationEvent] = []
        self.pending_tasks: List[Task] = []
        self.energy_calculator = EnergyCalculator(self.servers)
        self.waking_servers_tasks: Dict[str, List[Task]] = {s.server_id: [] for s in self.servers}

    def _push_event(self, event: SimulationEvent):
        heapq.heappush(self.event_queue, event)

    def _pop_event(self) -> SimulationEvent:
        return heapq.heappop(self.event_queue)

    def run(self) -> SimulationResult:
        """
        Executes the discrete-event simulation until completion or timeout.
        """
        self.logger.info(
            f"Starting simulation with scheduler '{self.scheduler.name}', "
            f"{len(self.tasks)} tasks, {len(self.servers)} servers."
        )

        # Handle zero tasks edge-case gracefully
        if not self.tasks:
            self.logger.warning("Simulation initiated with 0 tasks.")
            return SimulationResult(
                scheduler_name=self.scheduler.name,
                tasks=[],
                servers=self.servers,
                energy_calculator=self.energy_calculator,
                start_time=0.0,
                end_time=0.0,
                sim_metadata={"zero_workload": True}
            )

        # Clean slate reset of all entities
        self.scheduler.reset()
        for s in self.servers:
            s.reset(initial_state=ServerState.IDLE)
        for t in self.tasks:
            t.reset()
        self.energy_calculator.reset()
        self.event_queue.clear()
        self.pending_tasks.clear()
        self.waking_servers_tasks = {s.server_id: [] for s in self.servers}

        # Seed initial task arrivals
        earliest_arrival = min(t.arrival_time for t in self.tasks)
        self.current_time = earliest_arrival

        for task in self.tasks:
            self._push_event(SimulationEvent(
                timestamp=task.arrival_time,
                event_type=EventType.TASK_ARRIVAL,
                payload={"task": task},
                priority=10
            ))

        # Schedule initial sleep checks if sleep is enabled
        if self.enable_sleep_state:
            for server in self.servers:
                self._push_event(SimulationEvent(
                    timestamp=self.current_time + server.idle_timeout_to_sleep,
                    event_type=EventType.SERVER_CHECK_SLEEP,
                    payload={"server": server},
                    priority=20
                ))

        last_integrated_time = self.current_time

        # Main Discrete-Event Loop
        while self.event_queue and self.current_time <= self.max_duration:
            event = self._pop_event()

            # Ensure time monotonically increases
            if event.timestamp < self.current_time:
                raise SimulationError(
                    f"Clock inversion detected: Event {event.event_type} at {event.timestamp} "
                    f"is earlier than current time {self.current_time}."
                )

            # Integrate fleet energy over elapsed time delta
            time_delta = event.timestamp - last_integrated_time
            if time_delta > 0.0:
                self.energy_calculator.record_interval(self.current_time, time_delta)
                last_integrated_time = event.timestamp

            self.current_time = event.timestamp

            # Process event by type
            self._handle_event(event)

            # Periodically attempt to schedule any unassigned pending tasks
            self._dispatch_pending_tasks()

            # If all tasks are completed or failed, break early
            finished_count = sum(1 for t in self.tasks if t.state in (TaskState.COMPLETED, TaskState.FAILED))
            if finished_count == len(self.tasks):
                break

        # Finalize any lingering pending tasks exceeding max duration
        for t in self.pending_tasks:
            if t.state == TaskState.PENDING:
                t.mark_failed(self.current_time, reason="Simulation horizon limit exceeded")

        # Final energy record
        return SimulationResult(
            scheduler_name=self.scheduler.name,
            tasks=self.tasks,
            servers=self.servers,
            energy_calculator=self.energy_calculator,
            start_time=earliest_arrival,
            end_time=self.current_time,
            sim_metadata={
                "enable_sleep_state": self.enable_sleep_state,
                "max_duration": self.max_duration
            }
        )

    def _handle_event(self, event: SimulationEvent):
        """Dispatches an event to its dedicated handler."""
        etype = event.event_type

        if etype == EventType.TASK_ARRIVAL:
            task: Task = event.payload["task"]
            self.pending_tasks.append(task)

        elif etype == EventType.TASK_START:
            task: Task = event.payload["task"]
            server: Server = event.payload["server"]
            self._start_task(task, server)

        elif etype == EventType.TASK_COMPLETION:
            task: Task = event.payload["task"]
            server: Server = event.payload["server"]
            self._complete_task(task, server)

        elif etype == EventType.SERVER_WAKE_COMPLETE:
            server: Server = event.payload["server"]
            self._wake_server_complete(server)

        elif etype == EventType.SERVER_CHECK_SLEEP:
            server: Server = event.payload["server"]
            self._check_server_sleep(server)

    def _dispatch_pending_tasks(self):
        """
        Invokes the scheduler to map feasible pending tasks to servers.
        Handles waking up sleeping servers and scheduling task start events.
        """
        if not self.pending_tasks:
            return

        # Query scheduler for allocations
        allocations = self.scheduler.schedule_tasks(
            pending_tasks=self.pending_tasks,
            servers=self.servers,
            current_time=self.current_time
        )

        allocated_task_ids = set()

        for task, server in allocations:
            allocated_task_ids.add(task.task_id)

            if server.state == ServerState.SLEEPING:
                # Server needs to wake up before running task
                server.set_state(ServerState.WAKING, self.current_time)
                self.energy_calculator.record_wakeup(server)
                wake_finish_time = self.current_time + server.wake_up_delay

                # Queue task on this server to start once awake
                self.waking_servers_tasks[server.server_id].append(task)

                # Reserve resources immediately to prevent over-allocation during wake delay
                server.allocate_task(task, self.current_time)
                task.assigned_server_id = server.server_id

                self._push_event(SimulationEvent(
                    timestamp=wake_finish_time,
                    event_type=EventType.SERVER_WAKE_COMPLETE,
                    payload={"server": server},
                    priority=2
                ))

            elif server.state == ServerState.WAKING:
                # Server is already in the process of waking up
                self.waking_servers_tasks[server.server_id].append(task)
                server.allocate_task(task, self.current_time)
                task.assigned_server_id = server.server_id

            else:
                # Server is active or idle: allocate immediately and start task
                server.allocate_task(task, self.current_time)
                self._push_event(SimulationEvent(
                    timestamp=self.current_time,
                    event_type=EventType.TASK_START,
                    payload={"task": task, "server": server},
                    priority=5
                ))

        # Filter out allocated tasks from pending queue
        self.pending_tasks = [t for t in self.pending_tasks if t.task_id not in allocated_task_ids]

    def _start_task(self, task: Task, server: Server):
        """Marks task as running and schedules its completion event."""
        if task.state == TaskState.PENDING:
            task.mark_running(self.current_time, server.server_id)
            completion_time = self.current_time + task.duration
            self._push_event(SimulationEvent(
                timestamp=completion_time,
                event_type=EventType.TASK_COMPLETION,
                payload={"task": task, "server": server},
                priority=1
            ))

    def _complete_task(self, task: Task, server: Server):
        """Releases server resources and marks task as completed."""
        if task.state == TaskState.RUNNING:
            server.release_task(task.task_id, self.current_time)
            
            # Approximate task energy share: (cpu / total_cpu) * P(u) * duration (Wh)
            server_p = (server.idle_power + (server.max_power - server.idle_power) * (server.cpu_utilization ** server.alpha))
            cpu_fraction = min(1.0, task.cpu_demand / server.cpu_capacity) if server.cpu_capacity > 0 else 0.0
            task_energy_wh = cpu_fraction * server_p * (task.duration / 3600.0)

            task.mark_completed(self.current_time, energy=task_energy_wh)

            # If server is now empty, schedule sleep check
            if len(server.active_tasks) == 0 and self.enable_sleep_state:
                self._push_event(SimulationEvent(
                    timestamp=self.current_time + server.idle_timeout_to_sleep,
                    event_type=EventType.SERVER_CHECK_SLEEP,
                    payload={"server": server},
                    priority=20
                ))

    def _wake_server_complete(self, server: Server):
        """Server has finished wake-up sequence and is ready to process queued tasks."""
        if server.state in (ServerState.WAKING, ServerState.ACTIVE):
            server.set_state(ServerState.ACTIVE if server.active_tasks else ServerState.IDLE, self.current_time)
            
            # Start all tasks that were waiting for this server to wake
            queued = self.waking_servers_tasks[server.server_id]
            while queued:
                task = queued.pop(0)
                self._push_event(SimulationEvent(
                    timestamp=self.current_time,
                    event_type=EventType.TASK_START,
                    payload={"task": task, "server": server},
                    priority=5
                ))

    def _check_server_sleep(self, server: Server):
        """Transitions server to SLEEPING state if it remained idle for the timeout."""
        if not self.enable_sleep_state:
            return
        if server.state == ServerState.IDLE and len(server.active_tasks) == 0:
            if server.idle_since_time is not None:
                idle_duration = self.current_time - server.idle_since_time
                if idle_duration >= (server.idle_timeout_to_sleep - 1e-4):
                    server.set_state(ServerState.SLEEPING, self.current_time)
                    self.logger.debug(f"Server {server.server_id} transitioned to SLEEPING at t={self.current_time:.2f}s")
