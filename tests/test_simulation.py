"""
Integration tests for the discrete-event simulation engine and end-to-end comparisons.
Covers requirements 10, 18, 19, 23, 24.
"""

import pytest
from src.models.server import Server
from src.algorithms.fcfs import FCFSScheduler
from src.algorithms.round_robin import RoundRobinScheduler
from src.algorithms.load_balancing import LoadBalancingScheduler
from src.algorithms.eadcs import EADCSScheduler
from src.simulation.engine import SimulationEngine
from src.simulation.workload_generator import WorkloadGenerator, WorkloadCategory


class TestSimulationEngine:
    def create_servers(self, n=4):
        return [
            Server(f"S{i+1}", cpu_capacity=16.0, memory_capacity=32.0, idle_power=100.0, max_power=250.0)
            for i in range(n)
        ]

    def test_zero_task_workload(self):
        """Test 10: Zero-task workload completes gracefully without error."""
        engine = SimulationEngine(
            scheduler=FCFSScheduler(),
            servers=self.create_servers(2),
            tasks=[],
            enable_sleep_state=True
        )
        result = engine.run()
        assert len(result.tasks) == 0
        assert len(result.completed_tasks) == 0
        assert result.total_energy_wh == 0.0

    def test_deterministic_workload_generation(self):
        """Test 18: Workload generation with same seed produces identical tasks."""
        wl1 = WorkloadGenerator.generate_workload(num_tasks=25, category=WorkloadCategory.MEDIUM, seed=999)
        wl2 = WorkloadGenerator.generate_workload(num_tasks=25, category=WorkloadCategory.MEDIUM, seed=999)

        assert len(wl1) == len(wl2)
        for t1, t2 in zip(wl1, wl2):
            assert t1.task_id == t2.task_id
            assert t1.arrival_time == t2.arrival_time
            assert t1.cpu_demand == t2.cpu_demand
            assert t1.memory_demand == t2.memory_demand
            assert t1.duration == t2.duration
            assert t1.deadline == t2.deadline

    def test_end_to_end_simulation_all_algorithms(self):
        """Test 19 & 24: End-to-end simulation comparing all 4 schedulers on identical workloads."""
        tasks = WorkloadGenerator.generate_workload(num_tasks=30, category=WorkloadCategory.LOW, seed=42)
        schedulers = [FCFSScheduler(), RoundRobinScheduler(), LoadBalancingScheduler(), EADCSScheduler()]
        
        results = {}
        for sched in schedulers:
            servers = self.create_servers(4)
            engine = SimulationEngine(
                scheduler=sched,
                servers=servers,
                tasks=tasks,
                enable_sleep_state=True,
                idle_sleep_timeout=10.0
            )
            res = engine.run()
            results[sched.name] = res

            # Invariants verification
            assert len(res.completed_tasks) == len(tasks)
            assert res.total_energy_wh > 0.0
            assert res.makespan > 0.0
            for s in servers:
                assert s.allocated_cpu == 0.0
                assert s.allocated_memory == 0.0

        # EADCS consolidates on fewer servers, resulting in lower total energy than Load Balancing
        eadcs_energy = results["EADCS"].total_energy_wh
        lb_energy = results["Load Balancing"].total_energy_wh
        assert eadcs_energy <= lb_energy

    def test_state_leakage_between_repeated_runs(self):
        """Test 23: Successive simulation runs with the same engine/task objects reset properly."""
        tasks = WorkloadGenerator.generate_workload(num_tasks=15, category=WorkloadCategory.MEDIUM, seed=77)
        servers = self.create_servers(3)
        scheduler = EADCSScheduler()

        # Run 1
        eng1 = SimulationEngine(scheduler, servers, tasks, enable_sleep_state=True)
        res1 = eng1.run()
        energy_1 = res1.total_energy_wh

        # Run 2 on same objects
        eng2 = SimulationEngine(scheduler, servers, tasks, enable_sleep_state=True)
        res2 = eng2.run()
        energy_2 = res2.total_energy_wh

        assert abs(energy_1 - energy_2) < 1e-4
        assert len(res1.completed_tasks) == len(res2.completed_tasks)
