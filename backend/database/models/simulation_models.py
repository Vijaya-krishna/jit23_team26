from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from datetime import datetime
from sqlalchemy.orm import relationship
from backend.database.session import Base

class PhysicalServerModel(Base):
    """
    SQLAlchemy model representing physical hosts in the datacenter.
    Stores hardware specifications and dynamic runtime telemetry.
    """
    __tablename__ = "physical_servers"

    id = Column(Integer, primary_key=True, index=True)
    cpu_cores = Column(Integer, nullable=False)
    cpu_frequency_ghz = Column(Float, nullable=False)
    ram_mb = Column(Float, nullable=False)
    storage_gb = Column(Float, nullable=False)
    bandwidth_mbps = Column(Float, nullable=False)

    # Dynamic metrics
    power_state = Column(String(20), default="ACTIVE", nullable=False)  # 'ACTIVE', 'SLEEP', 'OFF'
    temperature = Column(Float, default=22.0, nullable=False)
    cpu_utilization = Column(Float, default=0.0, nullable=False)
    ram_utilization = Column(Float, default=0.0, nullable=False)
    storage_utilization = Column(Float, default=0.0, nullable=False)
    bandwidth_utilization = Column(Float, default=0.0, nullable=False)
    power_consumption = Column(Float, default=0.0, nullable=False)

    # Relationship to hosted Virtual Machines
    vms = relationship("VirtualMachineModel", back_populates="host", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<PhysicalServerModel id={self.id} power_state={self.power_state} cpu_util={self.cpu_utilization:.2f}>"


class VirtualMachineModel(Base):
    """
    SQLAlchemy model representing deployed Virtual Machines (VMs).
    """
    __tablename__ = "virtual_machines"

    id = Column(Integer, primary_key=True, index=True)
    cpu_cores = Column(Integer, nullable=False)
    ram_mb = Column(Float, nullable=False)
    storage_gb = Column(Float, nullable=False)
    bandwidth_mbps = Column(Float, nullable=False)

    # Dynamic metrics
    cpu_utilization = Column(Float, default=0.0, nullable=False)
    ram_utilization = Column(Float, default=0.0, nullable=False)

    # Parent physical host assignment
    host_id = Column(Integer, ForeignKey("physical_servers.id", ondelete="SET NULL"), nullable=True)
    host = relationship("PhysicalServerModel", back_populates="vms")

    # Dynamic tasks mapped on this VM
    tasks = relationship("TaskModel", back_populates="vm", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<VirtualMachineModel id={self.id} host_id={self.host_id} cpu_util={self.cpu_utilization:.2f}>"


class SimulationStateModel(Base):
    """
    SQLAlchemy model storing global, persistent simulation runtime states.
    Allows tick steps and power consumption histories to survive API request sessions.
    """
    __tablename__ = "simulation_state"

    id = Column(Integer, primary_key=True, default=1)
    tick_counter = Column(Integer, default=0, nullable=False)
    total_energy_kwh = Column(Float, default=0.0, nullable=False)

    def __repr__(self) -> str:
        return f"<SimulationStateModel tick={self.tick_counter} energy={self.total_energy_kwh:.6f} kWh>"


class TaskModel(Base):
    """
    SQLAlchemy model representing synthetic cloud processing tasks (workloads).
    """
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    cpu_requirement = Column(Float, nullable=False)
    ram_requirement = Column(Float, nullable=False)
    storage_requirement = Column(Float, nullable=False)
    bandwidth_requirement = Column(Float, nullable=False)
    priority = Column(String(20), nullable=False)        # 'HIGH', 'MEDIUM', 'LOW'
    execution_time = Column(Integer, nullable=False)     # remaining ticks
    deadline = Column(Integer, nullable=False)           # tick limit
    arrival_time = Column(Integer, nullable=False)       # tick added
    status = Column(String(20), default="WAITING", nullable=False)  # 'WAITING', 'RUNNING', 'COMPLETED', 'FAILED'

    # VM assignment mapping
    vm_id = Column(Integer, ForeignKey("virtual_machines.id", ondelete="SET NULL"), nullable=True)
    vm = relationship("VirtualMachineModel", back_populates="tasks")

    def __repr__(self) -> str:
        return f"<TaskModel id={self.id} status={self.status} remaining_time={self.execution_time}>"


class GlobalTelemetryLogModel(Base):
    """
    Time-series model logging aggregated data center telemetry per tick.
    """
    __tablename__ = "global_telemetry_logs"

    id = Column(Integer, primary_key=True, index=True)
    tick = Column(Integer, nullable=False, index=True)
    cpu_utilization = Column(Float, nullable=False)
    ram_utilization = Column(Float, nullable=False)
    storage_utilization = Column(Float, nullable=False)
    bandwidth_utilization = Column(Float, nullable=False)
    it_power_w = Column(Float, nullable=False)
    cooling_power_w = Column(Float, nullable=False)
    total_power_w = Column(Float, nullable=False)
    total_energy_kwh = Column(Float, nullable=False)
    carbon_emissions_kg = Column(Float, nullable=False)
    pue = Column(Float, nullable=False, default=1.35)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<GlobalTelemetryLogModel tick={self.tick} total_power={self.total_power_w:.1f}W>"


class HostTelemetryLogModel(Base):
    """
    Time-series model logging per-host physical metrics per tick.
    """
    __tablename__ = "host_telemetry_logs"

    id = Column(Integer, primary_key=True, index=True)
    tick = Column(Integer, nullable=False, index=True)
    host_id = Column(Integer, ForeignKey("physical_servers.id", ondelete="CASCADE"), nullable=False, index=True)
    cpu_utilization = Column(Float, nullable=False)
    ram_utilization = Column(Float, nullable=False)
    storage_utilization = Column(Float, nullable=False)
    bandwidth_utilization = Column(Float, nullable=False)
    temperature = Column(Float, nullable=False)
    power_consumption_w = Column(Float, nullable=False)

    # Establish relationship to PhysicalServerModel
    host = relationship("PhysicalServerModel")

    def __repr__(self) -> str:
        return f"<HostTelemetryLogModel tick={self.tick} host={self.host_id} temp={self.temperature:.1f}C>"

