import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database.session import Base
from backend.database.models.simulation_models import TaskModel, VirtualMachineModel, PhysicalServerModel, SimulationStateModel
from backend.api.repositories.simulation_repository import SimulationRepository
from backend.api.services.simulation_service import SimulationService
from backend.simulation.task_generator import WorkloadGenerator

class TestWorkloadAndTasks(unittest.TestCase):
    """
    Unit test suite validating task metrics generation and simulation processing loops.
    """
    def setUp(self):
        # Setup clean in-memory SQLite database
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.db = Session()
        
        self.repo = SimulationRepository(self.db)
        self.service = SimulationService(self.repo)

        # Seed global simulation state
        self.db.add(SimulationStateModel(id=1, tick_counter=0, total_energy_kwh=0.0))
        self.db.commit()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(self.engine)

    def test_workload_generator_bounds(self):
        """
        Verify the generated tasks stay within correct resource constraints.
        """
        generator = WorkloadGenerator()
        tasks = generator.generate_batch(start_task_id=1, count=20, arrival_tick=0)
        self.assertEqual(len(tasks), 20)
        
        for t in tasks:
            self.assertIn(t["priority"], ["HIGH", "MEDIUM", "LOW"])
            self.assertGreaterEqual(t["cpu_requirement"], 1.0)
            self.assertLessEqual(t["cpu_requirement"], 8.0)
            self.assertGreaterEqual(t["ram_requirement"], 1000.0)
            self.assertLessEqual(t["ram_requirement"], 32000.0)
            self.assertGreaterEqual(t["execution_time"], 4)
            self.assertLessEqual(t["execution_time"], 30)
            self.assertGreater(t["deadline"], t["arrival_time"])
            self.assertEqual(t["status"], "WAITING")

    def test_task_tick_decrement_loop(self):
        """
        Verify running tasks decrement execution times and transition status on completion.
        """
        # 1. Create a server and VM
        server = PhysicalServerModel(
            id=1, cpu_cores=8, cpu_frequency_ghz=3.0, ram_mb=16000.0, storage_gb=500.0, bandwidth_mbps=1000.0,
            power_state="ACTIVE", temperature=22.0, cpu_utilization=0.0, ram_utilization=0.0,
            storage_utilization=0.0, bandwidth_utilization=0.0, power_consumption=80.0
        )
        vm = VirtualMachineModel(
            id=1, cpu_cores=4, ram_mb=8000.0, storage_gb=100.0, bandwidth_mbps=100.0,
            cpu_utilization=0.0, ram_utilization=0.0, host_id=1
        )
        self.db.add(server)
        self.db.add(vm)
        self.db.commit()

        # 2. Add running task with 2 ticks execution time
        task = TaskModel(
            id=101, cpu_requirement=2.0, ram_requirement=4000.0, storage_requirement=50.0, bandwidth_requirement=50.0,
            priority="MEDIUM", execution_time=2, deadline=10, arrival_time=0, status="RUNNING", vm_id=1
        )
        self.db.add(task)
        self.db.commit()

        # 3. Call tick 1
        self.service.trigger_tick()
        self.db.refresh(task)
        # Task remains running, remaining execution_time decrements to 1
        self.assertEqual(task.status, "RUNNING")
        self.assertEqual(task.execution_time, 1)

        # 4. Call tick 2
        self.service.trigger_tick()
        self.db.refresh(task)
        # Task completes, vm_id becomes None
        self.assertEqual(task.status, "COMPLETED")
        self.assertEqual(task.execution_time, 0)
        self.assertIsNone(task.vm_id)

    def test_task_deadline_breach_failed(self):
        """
        Verify tasks transition to FAILED if they breach their deadline.
        """
        task = TaskModel(
            id=102, cpu_requirement=1.0, ram_requirement=1000.0, storage_requirement=10.0, bandwidth_requirement=10.0,
            priority="LOW", execution_time=5, deadline=1, arrival_time=0, status="WAITING", vm_id=None
        )
        self.db.add(task)
        self.db.commit()

        # Advance tick past deadline (current tick becomes 1, task deadline is 1, tick 2 breaches it)
        self.service.trigger_tick() # tick 0 -> 1
        self.service.trigger_tick() # tick 1 -> 2
        self.service.trigger_tick() # tick 2 -> 3
        self.db.refresh(task)
        
        self.assertEqual(task.status, "FAILED")

if __name__ == "__main__":
    unittest.main()
