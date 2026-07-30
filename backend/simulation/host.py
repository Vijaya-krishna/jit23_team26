from typing import Dict, Any, Optional
from backend.simulation.power_model import IPowerModel, LinearPowerModel
from backend.simulation.thermal_model import ThermalModel
from backend.simulation.network_storage import NetworkInterface, StorageUnit
from backend.simulation.vm import VirtualMachine

class PhysicalHost:
    """
    In-memory representation of a Physical Server (Host) in the data center.
    """
    def __init__(
        self,
        host_id: int,
        cpu_cores: int,
        cpu_frequency_ghz: float,
        ram_mb: float,
        storage_gb: float,
        bandwidth_mbps: float,
        power_model: Optional[IPowerModel] = None,
        thermal_model: Optional[ThermalModel] = None
    ):
        self.host_id = host_id
        self.cpu_cores = cpu_cores
        self.cpu_frequency_ghz = cpu_frequency_ghz
        self.ram_mb = ram_mb
        self.storage_gb = storage_gb
        self.bandwidth_mbps = bandwidth_mbps

        # Models (using Defaults if not provided)
        self.power_model = power_model or LinearPowerModel()
        self.thermal_model = thermal_model or ThermalModel()
        self.network = NetworkInterface(bandwidth_mbps)
        self.storage = StorageUnit(storage_gb)

        # Dynamic state telemetry
        self.power_state = "ACTIVE"  # 'ACTIVE', 'SLEEP', 'OFF'
        self.temperature = self.thermal_model.ambient_temp  # Start at ambient temperature
        self.cpu_utilization = 0.0  # 0.0 to 1.0
        self.ram_utilization = 0.0  # 0.0 to 1.0

        # Hosted VMs
        self.vms: Dict[int, VirtualMachine] = {}

    def can_add_vm(self, vm: VirtualMachine) -> bool:
        """
        Check if this host has sufficient CPU, RAM, storage, and network capacity to host the given VM.
        """
        allocated_cores = sum(v.cpu_cores for v in self.vms.values())
        allocated_ram = sum(v.ram_mb for v in self.vms.values())
        
        return (
            allocated_cores + vm.cpu_cores <= self.cpu_cores and
            allocated_ram + vm.ram_mb <= self.ram_mb and
            self.storage.current_utilization_gb + vm.storage_gb <= self.storage.capacity_gb and
            self.network.current_utilization + vm.bandwidth_mbps <= self.network.bandwidth_mbps
        )

    def add_vm(self, vm: VirtualMachine) -> bool:
        """
        Deploy a Virtual Machine on this physical host.
        Validates resources before allowing placement.
        """
        if not self.can_add_vm(vm):
            return False

        if not self.storage.allocate(vm.storage_gb) or not self.network.allocate(vm.bandwidth_mbps):
            return False

        vm.host_id = self.host_id
        self.vms[vm.vm_id] = vm
        self.tick()  # Refresh utilization immediately
        return True

    def remove_vm(self, vm_id: int) -> Optional[VirtualMachine]:
        """
        Remove a VM from this host and free up network, storage, and processing bounds.
        """
        if vm_id in self.vms:
            vm = self.vms.pop(vm_id)
            self.storage.release(vm.storage_gb)
            self.network.release(vm.bandwidth_mbps)
            vm.host_id = None
            self.tick()  # Refresh utilization immediately
            return vm
        return None

    def set_power_state(self, state: str) -> None:
        """
        Transitions the host's power state.
        Validates transitions: active, sleep, or off.
        """
        normalized_state = state.upper()
        if normalized_state not in ["ACTIVE", "SLEEP", "OFF"]:
            raise ValueError(f"Invalid power state requested: {state}")
        
        self.power_state = normalized_state
        
        # If server is sleeping or off, all VMs hosted on it are effectively stopped/cleared
        if normalized_state in ["SLEEP", "OFF"]:
            for vm in self.vms.values():
                vm.clear_tasks()
                vm.host_id = None
            self.vms.clear()
            self.storage.current_utilization_gb = 0.0
            self.network.current_utilization = 0.0
            
        self.tick()

    def get_power_consumption(self) -> float:
        """
        Get the current power consumption in Watts based on state and load.
        """
        return self.power_model.get_power(self.cpu_utilization, self.power_state)

    def tick(self) -> None:
        """
        Progress the server state by one time unit (tick).
        Aggregates VM resource usage, calculates core heat, and updates power draw.
        """
        if self.power_state != "ACTIVE":
            self.cpu_utilization = 0.0
            self.ram_utilization = 0.0
        else:
            # Aggregate utilization of VMs
            # P_util = Sum(VM_cores * VM_cpu_util) / Host_cores
            total_active_cores = sum(vm.cpu_cores * vm.cpu_utilization for vm in self.vms.values())
            total_active_ram = sum(vm.ram_mb * vm.ram_utilization for vm in self.vms.values())

            self.cpu_utilization = min(1.0, total_active_cores / self.cpu_cores) if self.cpu_cores > 0 else 0.0
            self.ram_utilization = min(1.0, total_active_ram / self.ram_mb) if self.ram_mb > 0 else 0.0

        # Update Thermal Profile based on power draw
        power_draw = self.get_power_consumption()
        self.temperature = self.thermal_model.update_temperature(self.temperature, power_draw)

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize the physical host stats.
        """
        return {
            "host_id": self.host_id,
            "cpu_cores": self.cpu_cores,
            "cpu_frequency_ghz": self.cpu_frequency_ghz,
            "ram_mb": self.ram_mb,
            "storage_gb": self.storage_gb,
            "bandwidth_mbps": self.bandwidth_mbps,
            "power_state": self.power_state,
            "temperature": self.temperature,
            "cpu_utilization": self.cpu_utilization,
            "ram_utilization": self.ram_utilization,
            "storage_utilization": self.storage.current_utilization_gb,
            "bandwidth_utilization": self.network.current_utilization,
            "power_consumption": self.get_power_consumption(),
            "vms_count": len(self.vms),
        }
