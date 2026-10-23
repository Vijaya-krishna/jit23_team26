"""
Unit tests for the non-linear Power Model and Energy Calculator.
Covers requirements 7, 8, 9.
"""

import pytest
from src.models.server import Server, ServerState
from src.models.task import Task
from src.energy.power_model import PowerModel
from src.energy.energy_calculator import EnergyCalculator


class TestPowerAndEnergy:
    def test_power_calculation_idle_and_max(self):
        """Test 7: Power calculation at zero, intermediate, and full utilization."""
        server = Server(
            server_id="S_pwr",
            cpu_capacity=10.0,
            memory_capacity=20.0,
            idle_power=100.0,
            max_power=300.0,
            alpha=1.0 # Linear for easy verification: P = 100 + 200 * u
        )

        # At u = 0.0 (Idle)
        p_idle = PowerModel.calculate_power(server, custom_utilization=0.0)
        assert p_idle == 100.0

        # At u = 0.5 (Half load)
        p_half = PowerModel.calculate_power(server, custom_utilization=0.5)
        assert p_half == 200.0

        # At u = 1.0 (Full load)
        p_full = PowerModel.calculate_power(server, custom_utilization=1.0)
        assert p_full == 300.0

    def test_non_linear_power_scaling(self):
        """Tests non-linear power curve with alpha = 2.0."""
        server = Server(
            server_id="S_nl",
            cpu_capacity=10.0,
            memory_capacity=20.0,
            idle_power=100.0,
            max_power=300.0,
            alpha=2.0 # P = 100 + 200 * (u^2)
        )
        # At u = 0.5: 100 + 200 * 0.25 = 150.0 W
        p_half = PowerModel.calculate_power(server, custom_utilization=0.5)
        assert p_half == 150.0

    def test_energy_integration_constant_power(self):
        """Test 7 & 8: Energy integration across intervals (Energy = Power * hours)."""
        server = Server("S_int", 10.0, 20.0, idle_power=120.0, max_power=300.0)
        calc = EnergyCalculator([server])

        # Over 3600 seconds (1 hour) at idle power (120W)
        calc.record_interval(current_time=3600.0, delta_time=3600.0)
        
        # 120 W * 1 h = 120 Wh
        assert abs(calc.total_fleet_energy_wh - 120.0) < 1e-3
        # 120 Wh * 3600 J/Wh = 432,000 Joules
        assert abs(calc.total_fleet_energy_joules - 432000.0) < 1e-1

    def test_sleep_and_wakeup_energy_behavior(self):
        """Test 9: Sleep power reduction and wake-up overhead accounting."""
        server = Server(
            server_id="S_sleep",
            cpu_capacity=16.0,
            memory_capacity=32.0,
            idle_power=100.0,
            max_power=250.0,
            sleep_power=10.0,       # 10W in sleep vs 100W idle
            wake_up_energy=720.0    # 720 Joules wake-up cost = 720/3600 = 0.2 Wh
        )
        server.set_state(ServerState.SLEEPING, current_time=0.0)
        calc = EnergyCalculator([server])

        # 1 hour in sleep state: 10W * 1h = 10 Wh
        calc.record_interval(current_time=3600.0, delta_time=3600.0)
        breakdown = calc.get_server_breakdown("S_sleep")
        assert abs(breakdown["sleep_wh"] - 10.0) < 1e-3
        assert breakdown["idle_wh"] == 0.0

        # Wake-up event
        calc.record_wakeup(server)
        breakdown_after_wake = calc.get_server_breakdown("S_sleep")
        assert abs(breakdown_after_wake["wakeup_wh"] - 0.2) < 1e-3
        assert abs(calc.total_fleet_energy_wh - 10.2) < 1e-3

    def test_marginal_power_calculation(self):
        """Tests marginal power computation for scheduling decisions."""
        server = Server("S_mp", 10.0, 20.0, idle_power=100.0, max_power=200.0, alpha=1.0)
        # Empty server: adding 5 CPU units brings utilization from 0.0 to 0.5
        # Power increases from 100W to 150W => delta = 50W
        marginal = PowerModel.calculate_marginal_power(server, additional_cpu=5.0)
        assert abs(marginal - 50.0) < 1e-3
