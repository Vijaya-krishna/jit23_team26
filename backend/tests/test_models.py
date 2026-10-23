"""
Unit tests for Task and Server models, state transitions, and resource invariants.
Covers requirements 1, 2, 3, 4, 5, 6, 14, 16, 24.
"""

import pytest
from src.models.task import Task, TaskState
from src.models.server import Server, ServerState
from src.utils.exceptions import (
    ValidationError,
    InvalidStateTransitionError,
    ResourceConstraintViolation
)


class TestTaskModel:
    def test_task_creation_valid(self):
        """Test 1: Valid task creation and attribute assignments."""
        task = Task(
            task_id="T001",
            name="DataETL",
            arrival_time=10.0,
            cpu_demand=4.0,
            memory_demand=16.0,
            duration=30.0,
            priority=8,
            deadline=60.0
        )
        assert task.task_id == "T001"
        assert task.arrival_time == 10.0
        assert task.cpu_demand == 4.0
        assert task.memory_demand == 16.0
        assert task.duration == 30.0
        assert task.priority == 8
        assert task.deadline == 60.0
        assert task.state == TaskState.PENDING
        assert task.waiting_time is None
        assert task.turnaround_time is None
        assert not task.is_deadline_missed

    def test_task_creation_invalid_negative_resources(self):
        """Test 14: Negative resource requirements rejected."""
        with pytest.raises(ValidationError):
            Task("T_bad", "Bad", arrival_time=-1.0, cpu_demand=2.0, memory_demand=4.0, duration=10.0)

        with pytest.raises(ValidationError):
            Task("T_bad", "Bad", arrival_time=0.0, cpu_demand=-2.0, memory_demand=4.0, duration=10.0)

        with pytest.raises(ValidationError):
            Task("T_bad", "Bad", arrival_time=0.0, cpu_demand=2.0, memory_demand=-4.0, duration=10.0)

        with pytest.raises(ValidationError):
            Task("T_bad", "Bad", arrival_time=0.0, cpu_demand=2.0, memory_demand=4.0, duration=0.0)

    def test_task_state_transitions(self):
        """Test 6: Valid and invalid task state lifecycle transitions."""
        task = Task("T002", "Job2", arrival_time=5.0, cpu_demand=2.0, memory_demand=4.0, duration=20.0, deadline=30.0)
        
        # Valid: PENDING -> RUNNING
        task.mark_running(start_time=6.0, server_id="S01")
        assert task.state == TaskState.RUNNING
        assert task.waiting_time == 1.0

        # Invalid: RUNNING -> RUNNING (Illegal re-trigger)
        with pytest.raises(InvalidStateTransitionError):
            task.mark_running(start_time=7.0, server_id="S01")

        # Valid: RUNNING -> COMPLETED
        task.mark_completed(completion_time=26.0, energy=0.15)
        assert task.state == TaskState.COMPLETED
        assert task.turnaround_time == 21.0
        assert not task.is_deadline_missed

        # Invalid: cannot complete a completed task
        with pytest.raises(InvalidStateTransitionError):
            task.mark_completed(completion_time=30.0)

    def test_task_deadline_miss(self):
        """Test deadline miss evaluation."""
        task = Task("T003", "Job3", arrival_time=0.0, cpu_demand=2.0, memory_demand=4.0, duration=50.0, deadline=40.0)
        task.mark_running(start_time=0.0, server_id="S01")
        task.mark_completed(completion_time=50.0)
        assert task.is_deadline_missed is True


class TestServerModel:
    def test_server_initialization_and_capacity(self):
        """Test 2: Server initialization, capacities, and power parameters."""
        server = Server(
            server_id="S01",
            cpu_capacity=16.0,
            memory_capacity=64.0,
            idle_power=100.0,
            max_power=250.0,
            sleep_power=10.0,
            wake_up_energy=500.0,
            wake_up_delay=5.0
        )
        assert server.server_id == "S01"
        assert server.cpu_capacity == 16.0
        assert server.memory_capacity == 64.0
        assert server.allocated_cpu == 0.0
        assert server.allocated_memory == 0.0
        assert server.cpu_utilization == 0.0
        assert server.memory_utilization == 0.0
        assert server.remaining_cpu == 16.0
        assert server.remaining_memory == 64.0
        assert server.state == ServerState.IDLE

    def test_server_feasible_and_infeasible_placement(self):
        """Test 3: Feasible and infeasible task placement."""
        server = Server("S02", cpu_capacity=8.0, memory_capacity=16.0, idle_power=80.0, max_power=200.0)
        
        # Feasible
        assert server.can_accommodate(cpu_demand=4.0, memory_demand=8.0) is True
        
        # Infeasible: exceeds CPU
        assert server.can_accommodate(cpu_demand=10.0, memory_demand=8.0) is False
        
        # Infeasible: exceeds Memory
        assert server.can_accommodate(cpu_demand=4.0, memory_demand=20.0) is False

    def test_server_allocation_limits_and_overload_prevention(self):
        """Test 4: CPU and memory allocation limits and over-allocation prevention."""
        server = Server("S03", cpu_capacity=8.0, memory_capacity=16.0, idle_power=80.0, max_power=200.0)
        t1 = Task("T10", "Job1", 0.0, cpu_demand=6.0, memory_demand=12.0, duration=10.0)
        server.allocate_task(t1, current_time=0.0)
        
        assert server.allocated_cpu == 6.0
        assert server.allocated_memory == 12.0
        assert server.remaining_cpu == 2.0
        assert server.remaining_memory == 4.0

        # Attempting to allocate task that exceeds remaining CPU
        t2 = Task("T11", "Job2", 0.0, cpu_demand=4.0, memory_demand=2.0, duration=10.0)
        with pytest.raises(ResourceConstraintViolation):
            server.allocate_task(t2, current_time=0.0)

    def test_server_resource_release_after_completion(self):
        """Test 5: Resource release after task completion."""
        server = Server("S04", cpu_capacity=16.0, memory_capacity=32.0, idle_power=100.0, max_power=250.0)
        t = Task("T20", "JobX", 0.0, cpu_demand=8.0, memory_demand=16.0, duration=20.0)
        server.allocate_task(t, current_time=0.0)
        assert server.state == ServerState.ACTIVE
        
        released_task = server.release_task(t.task_id, current_time=20.0)
        assert released_task == t
        assert server.allocated_cpu == 0.0
        assert server.allocated_memory == 0.0
        assert server.state == ServerState.IDLE
        assert len(server.active_tasks) == 0

    def test_server_unavailability(self):
        """Test 16: Server unavailability prevents accommodation."""
        server = Server("S05", cpu_capacity=16.0, memory_capacity=32.0, idle_power=100.0, max_power=250.0)
        server.set_state(ServerState.UNAVAILABLE, current_time=0.0)
        assert server.can_accommodate(cpu_demand=2.0, memory_demand=4.0) is False

    def test_resource_conservation_invariants(self):
        """Test 24: Resource conservation and allocation invariants."""
        server = Server("S06", cpu_capacity=10.0, memory_capacity=20.0, idle_power=90.0, max_power=220.0)
        tasks = [
            Task(f"T_{i}", f"J_{i}", 0.0, cpu_demand=2.0, memory_demand=4.0, duration=10.0)
            for i in range(5)
        ]
        for t in tasks:
            server.allocate_task(t, current_time=0.0)

        # Fully utilized
        assert server.allocated_cpu == 10.0
        assert server.allocated_memory == 20.0
        assert server.remaining_cpu == 0.0
        assert server.remaining_memory == 0.0
        assert server.cpu_utilization == 1.0

        # Release all
        for t in tasks:
            server.release_task(t.task_id, current_time=10.0)

        assert server.allocated_cpu == 0.0
        assert server.allocated_memory == 0.0
        assert server.remaining_cpu == 10.0
        assert server.remaining_memory == 20.0
