import pytest
from backend.simulation.host import PhysicalHost
from backend.simulation.vm import VirtualMachine
from backend.simulation.scheduler import RoundRobinScheduler, RandomScheduler, EnergyAwareScheduler, MLScheduler, get_scheduler

def test_energy_aware_scheduler_placement():
    scheduler = EnergyAwareScheduler()
    h1 = PhysicalHost(host_id=1, cpu_cores=16, cpu_frequency_ghz=3.2, ram_mb=64000, storage_gb=2000, bandwidth_mbps=10000)
    h2 = PhysicalHost(host_id=2, cpu_cores=16, cpu_frequency_ghz=3.2, ram_mb=64000, storage_gb=2000, bandwidth_mbps=10000)
    
    vm1 = VirtualMachine(vm_id=101, cpu_cores=4, ram_mb=8000, storage_gb=100, bandwidth_mbps=1000, host_id=1)
    vm2 = VirtualMachine(vm_id=102, cpu_cores=8, ram_mb=16000, storage_gb=200, bandwidth_mbps=2000, host_id=2)

    scheduler.schedule([h1, h2], [vm1, vm2])

    assert vm1.host_id is not None
    assert vm2.host_id is not None
    assert vm1.host_id in (1, 2)
    assert vm2.host_id in (1, 2)

def test_ml_scheduler_placement():
    scheduler = MLScheduler()
    h1 = PhysicalHost(host_id=1, cpu_cores=16, cpu_frequency_ghz=3.2, ram_mb=64000, storage_gb=2000, bandwidth_mbps=10000)
    h2 = PhysicalHost(host_id=2, cpu_cores=32, cpu_frequency_ghz=3.0, ram_mb=128000, storage_gb=4000, bandwidth_mbps=10000)

    vm = VirtualMachine(vm_id=201, cpu_cores=8, ram_mb=16000, storage_gb=200, bandwidth_mbps=2000, host_id=1)
    scheduler.schedule([h1, h2], [vm])

    assert vm.host_id is not None
    assert vm.host_id in (1, 2)

def test_get_scheduler_factory():
    s_rr = get_scheduler("round_robin")
    assert isinstance(s_rr, RoundRobinScheduler)

    s_rand = get_scheduler("random")
    assert isinstance(s_rand, RandomScheduler)

    s_ea = get_scheduler("energy_aware")
    assert isinstance(s_ea, EnergyAwareScheduler)

    s_ml = get_scheduler("ml")
    assert isinstance(s_ml, MLScheduler)

    with pytest.raises(ValueError):
        get_scheduler("unknown_scheduler_type")
