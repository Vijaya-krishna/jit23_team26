import logging
from typing import Dict, Any, List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.api.repositories.simulation_repository import ISimulationRepository
from backend.database.models.simulation_models import PhysicalServerModel, VirtualMachineModel, TaskModel, GlobalTelemetryLogModel, HostTelemetryLogModel
from backend.database.schemas.simulation_schema import VirtualMachineCreate, PhysicalServerCreate
from backend.simulation.datacenter_simulator import DataCenterSimulator
from backend.simulation.vm import VirtualMachine
from backend.simulation.task_generator import WorkloadGenerator

logger = logging.getLogger("simulation_service")

class SimulationService:
    """
    Simulation business logic coordinator.
    Loads DB stats into the simulator engine, updates clock ticks, manages VM routing, and commits changes.
    """
    def __init__(self, repo: ISimulationRepository):
        self.repo = repo
        self.simulator = DataCenterSimulator()

    def _sync_load(self) -> None:
        """
        Pull all active hardware components from the DB to rebuild memory objects.
        """
        self.repo.sync_simulator_from_db(self.simulator)

    def _sync_save(self) -> None:
        """
        Dump all updated memory allocations, power draw, and thermal telemetry back to DB.
        """
        self.repo.save_simulator_state(self.simulator)

    def get_servers_status(self) -> List[PhysicalServerModel]:
        """
        Retrieve details of all physical hosts in the data center.
        """
        return self.repo.list_all_servers()

    def get_vms_status(self) -> List[VirtualMachineModel]:
        """
        Retrieve details of all virtual machines in the data center.
        """
        return self.repo.list_all_vms()

    def update_host_power_state(self, host_id: int, target_state: str) -> PhysicalServerModel:
        """
        Toggle power state of a physical host (ACTIVE, SLEEP, OFF).
        Saves updated stats back to DB.
        """
        self._sync_load()
        host = self.simulator.get_host(host_id)
        if not host:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Physical server with ID {host_id} not found."
            )
        
        try:
            host.set_power_state(target_state)
        except ValueError as err:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(err)
            )

        self._sync_save()
        return self.repo.get_server_by_id(host_id)

    def deploy_vm(self, host_id: int, vm_data: VirtualMachineCreate) -> VirtualMachineModel:
        """
        Create a new Virtual Machine and deploy it onto a physical server.
        """
        self._sync_load()
        host = self.simulator.get_host(host_id)
        if not host:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Target physical server with ID {host_id} does not exist."
            )

        if host.power_state != "ACTIVE":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot deploy VM on host {host_id} because its current state is: {host.power_state}."
            )

        # Create record in DB first to obtain autoincrement ID
        db_vm = VirtualMachineModel(
            cpu_cores=vm_data.cpu_cores,
            ram_mb=vm_data.ram_mb,
            storage_gb=vm_data.storage_gb,
            bandwidth_mbps=vm_data.bandwidth_mbps,
            host_id=host_id
        )
        db_vm = self.repo.create_vm(db_vm)

        # Map to simulator
        vm_sim = VirtualMachine(
            vm_id=db_vm.id,
            cpu_cores=db_vm.cpu_cores,
            ram_mb=db_vm.ram_mb,
            storage_gb=db_vm.storage_gb,
            bandwidth_mbps=db_vm.bandwidth_mbps,
            host_id=host_id
        )

        if not host.add_vm(vm_sim):
            # Rollback DB record if deployment fails
            self.repo.delete_vm(db_vm.id)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Physical host {host_id} does not have sufficient resources to hold this VM."
            )

        # Successful allocation
        self._sync_save()
        return db_vm

    def destroy_vm(self, vm_id: int) -> bool:
        """
        Tear down a virtual machine and release physical server resources.
        """
        self._sync_load()
        if vm_id not in self.simulator.vms:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Virtual machine with ID {vm_id} not found."
            )

        # Remove from memory simulator
        self.simulator.unregister_vm(vm_id)
        
        # Remove from database
        self.repo.delete_vm(vm_id)
        self._sync_save()
        return True

    def trigger_tick(self) -> Dict[str, Any]:
        """
        Advance simulator clock by one tick.
        Re-computes cooling costs, energy draws, and returns telemetry.
        """
        self._sync_load()

        # Update Tasks state progress in database before we step the clock tick
        current_tick = self.simulator.tick_counter
        all_tasks = self.repo.list_all_tasks()

        # Assign WAITING tasks to active deployed VMs on ACTIVE hosts
        active_vms = [
            vm for vm in self.simulator.vms.values()
            if vm.host_id is not None and self.simulator.hosts.get(vm.host_id) and self.simulator.hosts[vm.host_id].power_state == "ACTIVE"
        ]

        if active_vms:
            waiting_tasks = [t for t in all_tasks if t.status == "WAITING"]
            priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
            waiting_tasks.sort(key=lambda t: (priority_order.get(t.priority, 3), t.arrival_time))

            vm_idx = 0
            for task in waiting_tasks:
                target_vm = active_vms[vm_idx % len(active_vms)]
                vm_idx += 1

                task.status = "RUNNING"
                task.vm_id = target_vm.vm_id

                task_dict = {
                    "id": task.id,
                    "cpu_requirement": task.cpu_requirement,
                    "ram_requirement": task.ram_requirement,
                    "storage_requirement": task.storage_requirement,
                    "bandwidth_requirement": task.bandwidth_requirement,
                    "priority": task.priority,
                    "execution_time": task.execution_time,
                    "deadline": task.deadline,
                    "arrival_time": task.arrival_time,
                    "status": "RUNNING",
                    "vm_id": task.vm_id
                }
                target_vm.add_task(task_dict)

        for task in all_tasks:
            if task.status == "RUNNING":
                task.execution_time -= 1
                if task.execution_time <= 0:
                    task.status = "COMPLETED"
                    # Release in-memory VM footprint
                    if task.vm_id is not None:
                        vm_sim = self.simulator.vms.get(task.vm_id)
                        if vm_sim:
                            # Remove task from in-memory VM list
                            vm_sim.active_tasks = [t for t in vm_sim.active_tasks if t["id"] != task.id]
                            vm_sim.update_utilization()
                    task.vm_id = None
                elif current_tick > task.deadline:
                    task.status = "FAILED"  # SLA breach
                    if task.vm_id is not None:
                        vm_sim = self.simulator.vms.get(task.vm_id)
                        if vm_sim:
                            vm_sim.active_tasks = [t for t in vm_sim.active_tasks if t["id"] != task.id]
                            vm_sim.update_utilization()
                    task.vm_id = None
            elif task.status == "WAITING":
                if current_tick > task.deadline:
                    task.status = "FAILED"  # SLA breach in queue

        # Now trigger the core simulator logic (calculates power, cooling, increments tick)
        self.simulator.tick()
        self._sync_save()

        # Extract post-tick telemetry results
        telemetry = self.simulator.get_telemetry()
        hosts_list = list(self.simulator.hosts.values())
        total_hosts_count = len(hosts_list)

        if total_hosts_count > 0:
            avg_storage = sum(h.storage.current_utilization_gb / max(1.0, h.storage.capacity_gb) for h in hosts_list) / total_hosts_count
            avg_network = sum(h.network.current_utilization / max(1.0, h.network.bandwidth_mbps) for h in hosts_list) / total_hosts_count
        else:
            avg_storage = 0.0
            avg_network = 0.0

        # Compute PUE from tick telemetry (last entry in simulator pue_history)
        pue_value = self.simulator.pue_history[-1]["pue"] if self.simulator.pue_history else 1.35

        # Save Global Telemetry History Log
        global_log = GlobalTelemetryLogModel(
            tick=telemetry["tick"],
            cpu_utilization=telemetry["average_cpu_utilization"],
            ram_utilization=telemetry["average_ram_utilization"],
            storage_utilization=avg_storage,
            bandwidth_utilization=avg_network,
            it_power_w=telemetry["it_power_w"],
            cooling_power_w=telemetry["cooling_power_w"],
            total_power_w=telemetry["total_power_w"],
            total_energy_kwh=telemetry["total_energy_kwh"],
            carbon_emissions_kg=telemetry["carbon_emissions_kg"],
            pue=pue_value
        )
        self.repo.create_global_log(global_log)

        # Save Per-Host Telemetry History Logs
        for host in hosts_list:
            host_log = HostTelemetryLogModel(
                tick=telemetry["tick"],
                host_id=host.host_id,
                cpu_utilization=host.cpu_utilization,
                ram_utilization=host.ram_utilization,
                storage_utilization=host.storage.current_utilization_gb / max(1.0, host.storage.capacity_gb),
                bandwidth_utilization=host.network.current_utilization / max(1.0, host.network.bandwidth_mbps),
                temperature=host.temperature,
                power_consumption_w=host.get_power_consumption()
            )
            self.repo.create_host_log(host_log)

        return telemetry

    def register_host(self, server_data: PhysicalServerCreate) -> PhysicalServerModel:
        """
        Provision and register a new physical host in the database and in-memory simulation pool.
        """
        db_host = PhysicalServerModel(
            cpu_cores=server_data.cpu_cores,
            cpu_frequency_ghz=server_data.cpu_frequency_ghz,
            ram_mb=server_data.ram_mb,
            storage_gb=server_data.storage_gb,
            bandwidth_mbps=server_data.bandwidth_mbps,
            power_state="ACTIVE",
            temperature=22.0,
            cpu_utilization=0.0,
            ram_utilization=0.0,
            storage_utilization=0.0,
            bandwidth_utilization=0.0,
            power_consumption=80.0
        )
        db_host = self.repo.create_server(db_host)
        
        # Load in memory
        self._sync_load()
        return db_host

    def get_telemetry_status(self) -> Dict[str, Any]:
        """
        Retrieve current aggregated telemetry metrics.
        """
        self._sync_load()
        return self.simulator.get_telemetry()

    def set_scheduler(self, name: str) -> None:
        """Set the active scheduler for the simulation.
        Uses the scheduler factory to create an instance and assigns it to the
        DataCenterSimulator. Raises HTTPException if the name is unsupported.
        """
        from backend.simulation.scheduler import get_scheduler
        try:
            scheduler = get_scheduler(name)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        self.simulator.set_scheduler(scheduler)

    def generate_workload(self, count: int) -> List[TaskModel]:
        """
        Generate and persist a batch of synthetic cloud tasks in the waiting queue.
        """
        self._sync_load()
        start_id = self.repo.get_next_pending_task_id()
        generator = WorkloadGenerator()
        
        task_dicts = generator.generate_batch(start_id, count, self.simulator.tick_counter)
        
        db_tasks = []
        for td in task_dicts:
            db_task = TaskModel(
                id=td["id"],
                cpu_requirement=td["cpu_requirement"],
                ram_requirement=td["ram_requirement"],
                storage_requirement=td["storage_requirement"],
                bandwidth_requirement=td["bandwidth_requirement"],
                priority=td["priority"],
                execution_time=td["execution_time"],
                deadline=td["deadline"],
                arrival_time=td["arrival_time"],
                status=td["status"],
                vm_id=td["vm_id"]
            )
            db_tasks.append(db_task)
            
        return self.repo.create_task_batch(db_tasks)

    def get_tasks(self) -> List[TaskModel]:
        """
        Retrieve all tasks from the database.
        """
        return self.repo.list_all_tasks()

    def get_global_logs(self, limit: int = 100) -> List[GlobalTelemetryLogModel]:
        """
        Retrieve global time-series history logs.
        """
        return self.repo.list_global_logs(limit)

    def get_host_logs(self, host_id: int, limit: int = 100) -> List[HostTelemetryLogModel]:
        """
        Retrieve host-level time-series history logs.
        """
        return self.repo.list_host_logs(host_id, limit)

    def get_power_profile_data(self) -> dict:
        """
        Return the real-time power consumption profile from the in-memory simulator.
        Includes PUE, per-host model breakdown, standby draw, and PUE history.
        """
        self._sync_load()
        return self.simulator.get_power_profile()



