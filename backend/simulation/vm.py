from typing import Optional, List, Dict, Any

class VirtualMachine:
    """
    In-memory representation of a Virtual Machine (VM) in the simulation.
    """
    def __init__(
        self,
        vm_id: int,
        cpu_cores: int,
        ram_mb: float,
        storage_gb: float,
        bandwidth_mbps: float,
        host_id: Optional[int] = None
    ):
        self.vm_id = vm_id
        self.cpu_cores = cpu_cores
        self.ram_mb = ram_mb
        self.storage_gb = storage_gb
        self.bandwidth_mbps = bandwidth_mbps
        self.host_id = host_id

        # Real-time utilization states (0.0 to 1.0)
        self.cpu_utilization = 0.0
        self.ram_utilization = 0.0

        # Workload tasks actively processing on this VM
        # Task representation will be fully fleshed out in Module 4 (Workload Generator)
        self.active_tasks: List[Dict[str, Any]] = []

    def add_task(self, task: Dict[str, Any]) -> None:
        """
        Deploy a task on this VM.
        Each task specifies its resource requirements.
        """
        self.active_tasks.append(task)
        self.update_utilization()

    def remove_task(self, task_id: int) -> None:
        """
        Remove a completed task from the active queue.
        """
        self.active_tasks = [t for t in self.active_tasks if t.get("id") != task_id]
        self.update_utilization()

    def clear_tasks(self) -> None:
        """
        Clear all active tasks.
        """
        self.active_tasks.clear()
        self.update_utilization()

    def update_utilization(self) -> None:
        """
        Recalculates CPU and RAM utilization metrics based on the aggregation
        of resources required by active tasks.
        """
        if not self.active_tasks:
            self.cpu_utilization = 0.0
            self.ram_utilization = 0.0
            return

        total_cpu_req = sum(t.get("cpu_requirement", 0.0) for t in self.active_tasks)
        total_ram_req = sum(t.get("ram_requirement", 0.0) for t in self.active_tasks)

        # Express utilization as a percentage of VM's capacity (capped at 1.0/100%)
        # Note: If tasks exceed VM capacity, the VM throttles and locks at 1.0 (100% capacity)
        self.cpu_utilization = min(1.0, total_cpu_req / self.cpu_cores)
        self.ram_utilization = min(1.0, total_ram_req / self.ram_mb)

    def to_dict(self) -> Dict[str, Any]:
        """
        Helper method to serialize the VM state.
        """
        return {
            "vm_id": self.vm_id,
            "cpu_cores": self.cpu_cores,
            "ram_mb": self.ram_mb,
            "storage_gb": self.storage_gb,
            "bandwidth_mbps": self.bandwidth_mbps,
            "host_id": self.host_id,
            "cpu_utilization": self.cpu_utilization,
            "ram_utilization": self.ram_utilization,
            "active_tasks_count": len(self.active_tasks),
        }
