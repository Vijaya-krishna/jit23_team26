from abc import ABC, abstractmethod
import random
from typing import List

from backend.simulation.host import PhysicalHost
from backend.simulation.vm import VirtualMachine


class BaseScheduler(ABC):
    """Abstract base class for all schedulers.
    Implementations must provide a ``schedule`` method that assigns VMs to hosts.
    """

    @abstractmethod
    def schedule(self, hosts: List[PhysicalHost], vms: List[VirtualMachine]) -> None:
        """Assign ``vms`` to the given ``hosts``.
        The method should mutate the ``hosts`` (by adding VMs) and update each VM's ``host_id``.
        """
        pass


class RoundRobinScheduler(BaseScheduler):
    """Distribute VMs across hosts in a circular order.
    Maintains an internal index so that consecutive calls continue the rotation.
    """

    def __init__(self) -> None:
        self._next_index = 0

    def schedule(self, hosts: List[PhysicalHost], vms: List[VirtualMachine]) -> None:
        if not hosts:
            return
        host_count = len(hosts)
        for vm in vms:
            # Find the next host that can accept the VM
            placed = False
            for _ in range(host_count):
                host = hosts[self._next_index]
                self._next_index = (self._next_index + 1) % host_count
                if host.add_vm(vm):
                    vm.host_id = host.host_id
                    placed = True
                    break
            if not placed:
                continue


class RandomScheduler(BaseScheduler):
    """Assign each VM to a randomly chosen host that can accommodate it."""

    def schedule(self, hosts: List[PhysicalHost], vms: List[VirtualMachine]) -> None:
        if not hosts:
            return
        for vm in vms:
            shuffled = hosts[:]
            random.shuffle(shuffled)
            for host in shuffled:
                if host.add_vm(vm):
                    vm.host_id = host.host_id
                    break


class EnergyAwareScheduler(BaseScheduler):
    """
    Power-Aware Best-Fit Decreasing (BFD) Scheduler.
    Sorts VMs by resource demand and assigns each VM to the host that results
    in the minimal increase in power consumption.
    Also handles dynamic host consolidation (transitioning empty hosts to SLEEP).
    """

    def schedule(self, hosts: List[PhysicalHost], vms: List[VirtualMachine]) -> None:
        if not hosts or not vms:
            return

        # Sort VMs in decreasing order of resource footprint (CPU cores + RAM)
        sorted_vms = sorted(
            vms,
            key=lambda v: (v.cpu_cores, v.ram_mb),
            reverse=True
        )

        for vm in sorted_vms:
            best_host = None
            min_delta_power = float('inf')

            # Consider active hosts first, then sleeping hosts
            active_hosts = [h for h in hosts if h.power_state == "ACTIVE"]
            eligible_hosts = active_hosts if active_hosts else hosts

            for host in eligible_hosts:
                if host.can_add_vm(vm):
                    curr_power = host.get_power_consumption()
                    # Estimate power after adding VM
                    temp_cpu_util = min(1.0, host.cpu_utilization + (vm.cpu_cores / max(1, host.cpu_cores)))
                    temp_power = host.power_model.get_power(temp_cpu_util, "ACTIVE")
                    delta_power = temp_power - curr_power

                    if delta_power < min_delta_power:
                        min_delta_power = delta_power
                        best_host = host

            if best_host is not None:
                if best_host.power_state != "ACTIVE":
                    best_host.set_power_state("ACTIVE")
                if best_host.add_vm(vm):
                    vm.host_id = best_host.host_id

    def consolidate(self, hosts: List[PhysicalHost]) -> int:
        """
        Consolidate VMs from underutilized hosts to denser hosts.
        Transitions newly emptied hosts to SLEEP mode to save energy.
        Returns the number of hosts transitioned to SLEEP.
        """
        sleep_count = 0
        active_hosts = [h for h in hosts if h.power_state == "ACTIVE"]
        
        # Sort active hosts by utilization ascending (try to empty least loaded)
        active_hosts.sort(key=lambda h: h.cpu_utilization)

        for source_host in active_hosts:
            if not source_host.vms:
                source_host.set_power_state("SLEEP")
                sleep_count += 1
                continue

            vms_to_move = list(source_host.vms.values())
            all_moved = True

            for vm in vms_to_move:
                # Find alternative host with higher utilization
                target_host = None
                best_fit_diff = float('inf')

                for dest_host in active_hosts:
                    if dest_host.host_id == source_host.host_id:
                        continue
                    if dest_host.can_add_vm(vm):
                        # Prefer hosts closer to optimal 70% load
                        load_diff = abs(0.70 - (dest_host.cpu_utilization + (vm.cpu_cores / dest_host.cpu_cores)))
                        if load_diff < best_fit_diff:
                            best_fit_diff = load_diff
                            target_host = dest_host

                if target_host is not None:
                    source_host.remove_vm(vm.vm_id)
                    target_host.add_vm(vm)
                    vm.host_id = target_host.host_id
                else:
                    all_moved = False

            if all_moved and not source_host.vms:
                source_host.set_power_state("SLEEP")
                sleep_count += 1

        return sleep_count


class MLScheduler(BaseScheduler):
    """
    Predictive Multi-Objective AI/ML Resource Scheduler.
    Uses feature-weighted scoring considering power slope, thermal headroom,
    and 75% optimal load target to prevent SLA breaches and thermal throttling.
    """

    def __init__(self, w_power: float = 0.4, w_thermal: float = 0.3, w_load: float = 0.3) -> None:
        self.w_power = w_power
        self.w_thermal = w_thermal
        self.w_load = w_load

    def schedule(self, hosts: List[PhysicalHost], vms: List[VirtualMachine]) -> None:
        if not hosts or not vms:
            return

        sorted_vms = sorted(
            vms,
            key=lambda v: (v.cpu_cores, v.ram_mb),
            reverse=True
        )

        for vm in sorted_vms:
            best_host = None
            best_score = -float('inf')

            active_hosts = [h for h in hosts if h.power_state == "ACTIVE"]
            eligible_hosts = active_hosts if active_hosts else hosts

            for host in eligible_hosts:
                if host.can_add_vm(vm):
                    new_cpu_util = min(1.0, host.cpu_utilization + (vm.cpu_cores / max(1, host.cpu_cores)))
                    new_power = host.power_model.get_power(new_cpu_util, "ACTIVE")
                    max_power = host.power_model.get_power(1.0, "ACTIVE")
                    
                    # Feature 1: Normalized power efficiency (1.0 = zero extra power)
                    power_score = 1.0 - (new_power / max(1.0, max_power))
                    
                    # Feature 2: Thermal headroom (1.0 = ambient 22°C, 0.0 = thermal limit 80°C)
                    thermal_score = max(0.0, 1.0 - ((host.temperature - 22.0) / 58.0))
                    
                    # Feature 3: Target load efficiency (peak efficiency near 75% load)
                    load_score = 1.0 - abs(new_cpu_util - 0.75)

                    composite_score = (
                        self.w_power * power_score +
                        self.w_thermal * thermal_score +
                        self.w_load * load_score
                    )

                    if composite_score > best_score:
                        best_score = composite_score
                        best_host = host

            if best_host is not None:
                if best_host.power_state != "ACTIVE":
                    best_host.set_power_state("ACTIVE")
                if best_host.add_vm(vm):
                    vm.host_id = best_host.host_id


def get_scheduler(name: str) -> BaseScheduler:
    """Factory returning a scheduler instance based on ``name``.
    Accepted names:
      - ``"round_robin"`` or ``"rr"``
      - ``"random"``
      - ``"energy_aware"``, ``"bfd"``, or ``"power_aware"``
      - ``"ml"``, ``"ai"``, or ``"predictive"``
    """
    name = name.lower()
    if name in {"round_robin", "rr"}:
        return RoundRobinScheduler()
    if name == "random":
        return RandomScheduler()
    if name in {"energy_aware", "bfd", "power_aware"}:
        return EnergyAwareScheduler()
    if name in {"ml", "ai", "predictive"}:
        return MLScheduler()
    raise ValueError(f"Unsupported scheduler: {name}")

