from abc import ABC, abstractmethod
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from backend.database.models.simulation_models import PhysicalServerModel, VirtualMachineModel, SimulationStateModel, TaskModel, GlobalTelemetryLogModel, HostTelemetryLogModel
from backend.simulation.datacenter_simulator import DataCenterSimulator
from backend.simulation.host import PhysicalHost
from backend.simulation.vm import VirtualMachine

class ISimulationRepository(ABC):
    """
    Interface for simulation resources repository.
    """
    @abstractmethod
    def get_server_by_id(self, server_id: int) -> Optional[PhysicalServerModel]:
        pass

    @abstractmethod
    def list_all_servers(self) -> List[PhysicalServerModel]:
        pass

    @abstractmethod
    def list_all_vms(self) -> List[VirtualMachineModel]:
        pass

    @abstractmethod
    def create_server(self, server: PhysicalServerModel) -> PhysicalServerModel:
        pass

    @abstractmethod
    def create_vm(self, vm: VirtualMachineModel) -> VirtualMachineModel:
        pass

    @abstractmethod
    def delete_vm(self, vm_id: int) -> bool:
        pass

    @abstractmethod
    def save_simulator_state(self, simulator: DataCenterSimulator) -> None:
        pass

    @abstractmethod
    def sync_simulator_from_db(self, simulator: DataCenterSimulator) -> None:
        pass

    @abstractmethod
    def list_all_tasks(self) -> List[TaskModel]:
        pass

    @abstractmethod
    def create_task_batch(self, tasks: List[TaskModel]) -> List[TaskModel]:
        pass

    @abstractmethod
    def get_next_pending_task_id(self) -> int:
        pass

    @abstractmethod
    def create_global_log(self, log: GlobalTelemetryLogModel) -> GlobalTelemetryLogModel:
        pass

    @abstractmethod
    def create_host_log(self, log: HostTelemetryLogModel) -> HostTelemetryLogModel:
        pass

    @abstractmethod
    def list_global_logs(self, limit: int = 100) -> List[GlobalTelemetryLogModel]:
        pass

    @abstractmethod
    def list_host_logs(self, host_id: int, limit: int = 100) -> List[HostTelemetryLogModel]:
        pass


class SimulationRepository(ISimulationRepository):
    """
    Concrete SQLAlchemy repository implementation for simulation objects.
    """
    def __init__(self, db: Session):
        self.db = db

    def get_server_by_id(self, server_id: int) -> Optional[PhysicalServerModel]:
        """
        Fetch a physical host with nested VMs loaded.
        """
        return self.db.query(PhysicalServerModel).options(
            joinedload(PhysicalServerModel.vms)
        ).filter(PhysicalServerModel.id == server_id).first()

    def list_all_servers(self) -> List[PhysicalServerModel]:
        """
        Fetch all physical hosts with nested VMs and their tasks.
        """
        return self.db.query(PhysicalServerModel).options(
            joinedload(PhysicalServerModel.vms)
        ).all()

    def list_all_vms(self) -> List[VirtualMachineModel]:
        """
        Fetch all virtual machine records.
        """
        return self.db.query(VirtualMachineModel).all()

    def create_server(self, server: PhysicalServerModel) -> PhysicalServerModel:
        """
        Persist a new physical host record.
        """
        self.db.add(server)
        self.db.commit()
        self.db.refresh(server)
        return server

    def create_vm(self, vm: VirtualMachineModel) -> VirtualMachineModel:
        """
        Persist a new virtual machine record.
        """
        self.db.add(vm)
        self.db.commit()
        self.db.refresh(vm)
        return vm

    def delete_vm(self, vm_id: int) -> bool:
        """
        Delete a VM record.
        """
        vm = self.db.query(VirtualMachineModel).filter(VirtualMachineModel.id == vm_id).first()
        if vm:
            self.db.delete(vm)
            self.db.commit()
            return True
        return False

    def list_all_tasks(self) -> List[TaskModel]:
        """
        List all tasks stored in the database.
        """
        return self.db.query(TaskModel).all()

    def create_task_batch(self, tasks: List[TaskModel]) -> List[TaskModel]:
        """
        Bulk insert a collection of tasks.
        """
        self.db.add_all(tasks)
        self.db.commit()
        return tasks

    def get_next_pending_task_id(self) -> int:
        """
        Return the next ID to assign to new tasks.
        """
        from sqlalchemy import func
        max_id = self.db.query(func.max(TaskModel.id)).scalar()
        return (max_id or 0) + 1

    def create_global_log(self, log: GlobalTelemetryLogModel) -> GlobalTelemetryLogModel:
        """
        Save a global telemetry snapshot to history logs.
        """
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log

    def create_host_log(self, log: HostTelemetryLogModel) -> HostTelemetryLogModel:
        """
        Save a host-level telemetry snapshot to history logs.
        """
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log

    def list_global_logs(self, limit: int = 100) -> List[GlobalTelemetryLogModel]:
        """
        Retrieve global telemetry logs ordered by tick.
        """
        return self.db.query(GlobalTelemetryLogModel).order_by(GlobalTelemetryLogModel.tick.asc()).limit(limit).all()

    def list_host_logs(self, host_id: int, limit: int = 100) -> List[HostTelemetryLogModel]:
        """
        Retrieve host-level telemetry logs ordered by tick.
        """
        return self.db.query(HostTelemetryLogModel).filter(HostTelemetryLogModel.host_id == host_id).order_by(HostTelemetryLogModel.tick.asc()).limit(limit).all()

    def save_simulator_state(self, simulator: DataCenterSimulator) -> None:
        """
        Dumps the in-memory simulator stats back into the database.
        Synchronizes runtime CPU/RAM/power state mappings into table rows.
        """
        # 1. Sync global state
        db_state = self.db.query(SimulationStateModel).filter(SimulationStateModel.id == 1).first()
        if not db_state:
            db_state = SimulationStateModel(id=1, tick_counter=simulator.tick_counter, total_energy_kwh=simulator.total_energy_kwh)
            self.db.add(db_state)
        else:
            db_state.tick_counter = simulator.tick_counter
            db_state.total_energy_kwh = simulator.total_energy_kwh

        # 2. Sync Hosts
        for host in simulator.hosts.values():
            db_host = self.db.query(PhysicalServerModel).filter(PhysicalServerModel.id == host.host_id).first()
            if db_host:
                db_host.power_state = host.power_state
                db_host.temperature = host.temperature
                db_host.cpu_utilization = host.cpu_utilization
                db_host.ram_utilization = host.ram_utilization
                db_host.storage_utilization = host.storage.current_utilization_gb
                db_host.bandwidth_utilization = host.network.current_utilization
                db_host.power_consumption = host.get_power_consumption()

            # Sync VMs hosted on this host
            for vm in host.vms.values():
                db_vm = self.db.query(VirtualMachineModel).filter(VirtualMachineModel.id == vm.vm_id).first()
                if db_vm:
                    db_vm.cpu_utilization = vm.cpu_utilization
                    db_vm.ram_utilization = vm.ram_utilization
                    db_vm.host_id = host.host_id

        self.db.commit()

    def sync_simulator_from_db(self, simulator: DataCenterSimulator) -> None:
        """
        Reconstructs the simulator's in-memory data structures using records loaded from the DB.
        """
        simulator.hosts.clear()
        simulator.vms.clear()

        # 1. Sync global state
        db_state = self.db.query(SimulationStateModel).filter(SimulationStateModel.id == 1).first()
        if db_state:
            simulator.tick_counter = db_state.tick_counter
            simulator.total_energy_kwh = db_state.total_energy_kwh
        else:
            simulator.tick_counter = 0
            simulator.total_energy_kwh = 0.0
        
        # 2. Sync Hosts and VMs
        db_hosts = self.list_all_servers()
        for db_host in db_hosts:
            host_sim = PhysicalHost(
                host_id=db_host.id,
                cpu_cores=db_host.cpu_cores,
                cpu_frequency_ghz=db_host.cpu_frequency_ghz,
                ram_mb=db_host.ram_mb,
                storage_gb=db_host.storage_gb,
                bandwidth_mbps=db_host.bandwidth_mbps
            )
            host_sim.power_state = db_host.power_state
            host_sim.temperature = db_host.temperature
            host_sim.cpu_utilization = db_host.cpu_utilization
            host_sim.ram_utilization = db_host.ram_utilization
            host_sim.storage.current_utilization_gb = db_host.storage_utilization
            host_sim.network.current_utilization = db_host.bandwidth_utilization
            
            # Recreate hosted VMs
            for db_vm in db_host.vms:
                vm_sim = VirtualMachine(
                    vm_id=db_vm.id,
                    cpu_cores=db_vm.cpu_cores,
                    ram_mb=db_vm.ram_mb,
                    storage_gb=db_vm.storage_gb,
                    bandwidth_mbps=db_vm.bandwidth_mbps,
                    host_id=db_host.id
                )
                
                # Load tasks currently running on this VM
                for db_task in db_vm.tasks:
                    if db_task.status == "RUNNING":
                        task_dict = {
                            "id": db_task.id,
                            "cpu_requirement": db_task.cpu_requirement,
                            "ram_requirement": db_task.ram_requirement,
                            "storage_requirement": db_task.storage_requirement,
                            "bandwidth_requirement": db_task.bandwidth_requirement,
                            "priority": db_task.priority,
                            "execution_time": db_task.execution_time,
                            "deadline": db_task.deadline,
                            "arrival_time": db_task.arrival_time,
                            "status": db_task.status,
                            "vm_id": db_task.vm_id
                        }
                        vm_sim.active_tasks.append(task_dict)
                
                # Re-compute VM utilization based on active tasks
                vm_sim.update_utilization()
                
                host_sim.vms[vm_sim.vm_id] = vm_sim
                simulator.vms[vm_sim.vm_id] = vm_sim
                
            simulator.hosts[host_sim.host_id] = host_sim
