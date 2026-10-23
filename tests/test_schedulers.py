"""
Unit tests for scheduling algorithms (FCFS, Round Robin, Load Balancing, EADCS) and fallback recovery.
Covers requirements 17, 19, 23.
"""

import pytest
from src.models.task import Task
from src.models.server import Server, ServerState
from src.algorithms.fcfs import FCFSScheduler
from src.algorithms.round_robin import RoundRobinScheduler
from src.algorithms.load_balancing import LoadBalancingScheduler
from src.algorithms.eadcs import EADCSScheduler
from src.utils.logging_config import clear_diagnostic_events, get_diagnostic_events


class TestSchedulers:
    def setup_method(self):
        clear_diagnostic_events()

    def create_sample_fleet(self):
        return [
            Server("S1", cpu_capacity=8.0, memory_capacity=16.0, idle_power=80.0, max_power=200.0),
            Server("S2", cpu_capacity=8.0, memory_capacity=16.0, idle_power=80.0, max_power=200.0),
            Server("S3", cpu_capacity=16.0, memory_capacity=32.0, idle_power=120.0, max_power=300.0),
        ]

    def test_fcfs_scheduler(self):
        """Test 19: FCFS selects first feasible server."""
        scheduler = FCFSScheduler()
        fleet = self.create_sample_fleet()
        task = Task("T1", "Job1", 0.0, cpu_demand=4.0, memory_demand=8.0, duration=10.0)

        server = scheduler.select_server(task, fleet, current_time=0.0)
        assert server is not None
        assert server.server_id == "S1"

    def test_round_robin_scheduler(self):
        """Test 19: Round Robin distributes across servers circularly."""
        scheduler = RoundRobinScheduler()
        fleet = self.create_sample_fleet()
        t1 = Task("T1", "Job1", 0.0, cpu_demand=2.0, memory_demand=4.0, duration=10.0)
        t2 = Task("T2", "Job2", 0.0, cpu_demand=2.0, memory_demand=4.0, duration=10.0)
        t3 = Task("T3", "Job3", 0.0, cpu_demand=2.0, memory_demand=4.0, duration=10.0)
        t4 = Task("T4", "Job4", 0.0, cpu_demand=2.0, memory_demand=4.0, duration=10.0)

        s1 = scheduler.select_server(t1, fleet, 0.0)
        fleet[0].allocate_task(t1, 0.0)

        s2 = scheduler.select_server(t2, fleet, 0.0)
        fleet[1].allocate_task(t2, 0.0)

        s3 = scheduler.select_server(t3, fleet, 0.0)
        fleet[2].allocate_task(t3, 0.0)

        s4 = scheduler.select_server(t4, fleet, 0.0)

        assert s1.server_id == "S1"
        assert s2.server_id == "S2"
        assert s3.server_id == "S3"
        assert s4.server_id == "S1" # Cycled back!

    def test_load_balancing_scheduler(self):
        """Test 19: Load Balancing selects server with minimum utilization."""
        scheduler = LoadBalancingScheduler()
        fleet = self.create_sample_fleet()
        
        # Load S1 with 4.0 CPU (util = 4/8 = 50%)
        t_heavy = Task("T_init", "JobInit", 0.0, cpu_demand=4.0, memory_demand=4.0, duration=10.0)
        fleet[0].allocate_task(t_heavy, 0.0)

        # New task should choose S2 (util = 0%) rather than S1
        t_new = Task("T_new", "JobNew", 0.0, cpu_demand=2.0, memory_demand=4.0, duration=10.0)
        selected = scheduler.select_server(t_new, fleet, 0.0)
        assert selected.server_id in ("S2", "S3")
        assert selected.cpu_utilization == 0.0

    def test_eadcs_scheduler_consolidation(self):
        """Test EADCS prefers active host to consolidate rather than waking sleep host."""
        scheduler = EADCSScheduler()
        fleet = self.create_sample_fleet()
        fleet[0].set_state(ServerState.ACTIVE, current_time=0.0)
        fleet[1].set_state(ServerState.SLEEPING, current_time=0.0)
        fleet[2].set_state(ServerState.SLEEPING, current_time=0.0)

        task = Task("T_cons", "JobCons", 0.0, cpu_demand=2.0, memory_demand=4.0, duration=10.0)
        selected = scheduler.select_server(task, fleet, current_time=0.0)
        # Should pick active S1 to avoid waking up S2 or S3
        assert selected.server_id == "S1"

    def test_scheduler_fallback_behavior(self):
        """Test 17: Scheduler falls back safely when encountering an unexpected error."""
        class BuggyScheduler(FCFSScheduler):
            def select_server(self, task, servers, current_time):
                raise ZeroDivisionError("Simulated unexpected algorithm bug")

        buggy = BuggyScheduler()
        buggy.name = "Buggy"
        buggy.fallback_scheduler = FCFSScheduler()

        fleet = self.create_sample_fleet()
        task = Task("T_err", "JobErr", 0.0, cpu_demand=2.0, memory_demand=4.0, duration=10.0)

        allocations = buggy.schedule_tasks([task], fleet, current_time=0.0)
        assert len(allocations) == 1
        assert allocations[0][1].server_id == "S1"

        # Diagnostic log should have captured fallback event
        diag = get_diagnostic_events()
        assert any(d["event_type"] == "FALLBACK_TRIGGERED" for d in diag)

    def test_repeated_runs_without_state_leakage(self):
        """Test 23: Multiple scheduler executions do not leak state."""
        scheduler = RoundRobinScheduler()
        fleet = self.create_sample_fleet()
        task = Task("T_run", "JobRun", 0.0, cpu_demand=2.0, memory_demand=4.0, duration=10.0)

        # Run 1
        s1 = scheduler.select_server(task, fleet, 0.0)
        assert s1.server_id == "S1"

        # Reset
        scheduler.reset()
        assert scheduler.current_index == -1

        # Run 2 from reset state
        s2 = scheduler.select_server(task, fleet, 0.0)
        assert s2.server_id == "S1"
