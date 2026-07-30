"""
Unit Tests — Module 6: Power Consumption Engine
Tests all three power models (Linear, Cubic, SPECpower), state transitions,
PUE computation, and the get_power_profile() simulator method.
"""
import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from backend.simulation.power_model import LinearPowerModel, CubicPowerModel, SPECpowerModel
from backend.simulation.host import PhysicalHost
from backend.simulation.datacenter_simulator import DataCenterSimulator


# ─── Linear Power Model Tests ──────────────────────────────────────────────────

class TestLinearPowerModel:
    """Verify LinearPowerModel produces physically correct values at key breakpoints."""

    def setup_method(self):
        self.model = LinearPowerModel(idle_power_w=80.0, peak_power_w=250.0, sleep_power_w=10.0, standby_power_w=5.0)

    def test_idle_state_returns_idle_power(self):
        assert self.model.get_power(0.0, 'ACTIVE') == pytest.approx(80.0)

    def test_peak_state_returns_peak_power(self):
        assert self.model.get_power(1.0, 'ACTIVE') == pytest.approx(250.0)

    def test_half_load_is_midpoint(self):
        expected = 80.0 + (250.0 - 80.0) * 0.5
        assert self.model.get_power(0.5, 'ACTIVE') == pytest.approx(expected)

    def test_sleep_state_returns_sleep_power(self):
        assert self.model.get_power(1.0, 'SLEEP') == pytest.approx(10.0)

    def test_off_state_returns_standby_power(self):
        """OFF state must return standby (BMC chip) power, not zero."""
        assert self.model.get_power(0.0, 'OFF') == pytest.approx(5.0)

    def test_clamped_above_one(self):
        """Utilisation > 1.0 must be clamped to 1.0 (peak)."""
        assert self.model.get_power(2.0, 'ACTIVE') == pytest.approx(250.0)

    def test_clamped_below_zero(self):
        """Utilisation < 0.0 must be clamped to 0.0 (idle)."""
        assert self.model.get_power(-0.5, 'ACTIVE') == pytest.approx(80.0)

    def test_model_name(self):
        assert self.model.model_name == 'Linear'


# ─── Cubic Power Model Tests ───────────────────────────────────────────────────

class TestCubicPowerModel:
    """Verify CubicPowerModel super-linear behaviour (Barroso & Hölzle 2007)."""

    def setup_method(self):
        self.model = CubicPowerModel(idle_power_w=80.0, peak_power_w=250.0, sleep_power_w=10.0, standby_power_w=5.0, alpha=2.5)

    def test_idle_returns_idle_power(self):
        assert self.model.get_power(0.0, 'ACTIVE') == pytest.approx(80.0)

    def test_peak_returns_peak_power(self):
        assert self.model.get_power(1.0, 'ACTIVE') == pytest.approx(250.0)

    def test_cubic_at_half_load_less_than_linear(self):
        """
        At 50% load, cubic power < linear power (super-linear means less power
        at medium loads compared to linear, approaching peak only at full load).
        """
        linear = LinearPowerModel(80, 250, 10, 5)
        cubic = self.model
        assert cubic.get_power(0.5, 'ACTIVE') < linear.get_power(0.5, 'ACTIVE')

    def test_sleep_state(self):
        assert self.model.get_power(0.0, 'SLEEP') == pytest.approx(10.0)

    def test_off_standby(self):
        assert self.model.get_power(0.0, 'OFF') == pytest.approx(5.0)

    def test_monotonically_increasing(self):
        """Power must increase monotonically with CPU utilisation."""
        prev = self.model.get_power(0.0, 'ACTIVE')
        for u in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]:
            curr = self.model.get_power(u, 'ACTIVE')
            assert curr >= prev, f"Power not increasing at u={u}"
            prev = curr

    def test_model_name(self):
        assert 'Cubic' in self.model.model_name


# ─── SPECpower Model Tests ─────────────────────────────────────────────────────

class TestSPECpowerModel:
    """Verify SPECpowerModel piecewise interpolation from ssj2008 lookup table."""

    def setup_method(self):
        self.model = SPECpowerModel(peak_power_w=250.0, sleep_power_w=10.0, standby_power_w=5.0)

    def test_zero_load_returns_idle(self):
        """0% load → fraction[0] * peak = 0.333 * 250 = 83.25 W"""
        expected = 250.0 * 0.333
        assert self.model.get_power(0.0, 'ACTIVE') == pytest.approx(expected, rel=1e-3)

    def test_full_load_returns_peak(self):
        """100% load → fraction[10] * peak = 1.0 * 250 = 250 W"""
        assert self.model.get_power(1.0, 'ACTIVE') == pytest.approx(250.0, rel=1e-3)

    def test_spec_breakpoint_50_pct(self):
        """At exactly 50% load, SPECpower fraction should be 0.679."""
        expected = 250.0 * 0.679
        assert self.model.get_power(0.5, 'ACTIVE') == pytest.approx(expected, rel=1e-3)

    def test_intermediate_interpolation(self):
        """At 25% load, interpolate between 20% (0.492) and 30% (0.561) breakpoints."""
        expected = 250.0 * (0.492 * 0.5 + 0.561 * 0.5)
        assert self.model.get_power(0.25, 'ACTIVE') == pytest.approx(expected, rel=1e-3)

    def test_sleep_state(self):
        assert self.model.get_power(0.0, 'SLEEP') == pytest.approx(10.0)

    def test_off_standby(self):
        assert self.model.get_power(0.0, 'OFF') == pytest.approx(5.0)

    def test_always_above_idle(self):
        """ACTIVE state power must always be >= idle power at all loads."""
        idle = self.model.get_power(0.0, 'ACTIVE')
        for u in [0.1, 0.2, 0.5, 0.75, 1.0]:
            assert self.model.get_power(u, 'ACTIVE') >= idle

    def test_model_name(self):
        assert 'SPECpower' in self.model.model_name


# ─── PUE Computation Tests ────────────────────────────────────────────────────

class TestPUEComputation:
    """Verify PUE is computed correctly: PUE = total_facility / IT and is always >= 1.0."""

    def _make_sim(self, cooling_overhead=0.35):
        sim = DataCenterSimulator(cooling_overhead_pct=cooling_overhead)
        host = PhysicalHost(host_id=1, cpu_cores=16, cpu_frequency_ghz=3.2,
                            ram_mb=64000, storage_gb=2000, bandwidth_mbps=10000)
        sim.add_host(host)
        return sim

    def test_pue_always_geq_one(self):
        sim = self._make_sim(cooling_overhead=0.35)
        sim.tick()
        pue = sim.pue_history[-1]['pue']
        assert pue >= 1.0

    def test_pue_exact_value_35pct_overhead(self):
        """PUE with 35% cooling = 1.35 when active."""
        sim = self._make_sim(cooling_overhead=0.35)
        sim.tick()
        assert sim.pue_history[-1]['pue'] == pytest.approx(1.35, rel=1e-3)

    def test_pue_history_grows_per_tick(self):
        sim = self._make_sim()
        for _ in range(5):
            sim.tick()
        assert len(sim.pue_history) == 5

    def test_pue_history_tick_counter_matches(self):
        sim = self._make_sim()
        for _ in range(3):
            sim.tick()
        for i, entry in enumerate(sim.pue_history):
            assert entry['tick'] == i + 1


# ─── get_power_profile() Tests ────────────────────────────────────────────────

class TestGetPowerProfile:
    """Verify DataCenterSimulator.get_power_profile() returns valid structured data."""

    def setup_method(self):
        self.sim = DataCenterSimulator(cooling_overhead_pct=0.35)
        for _ in range(3):
            host = PhysicalHost(host_id=_ + 1, cpu_cores=16, cpu_frequency_ghz=3.2,
                                ram_mb=64000, storage_gb=2000, bandwidth_mbps=10000)
            self.sim.add_host(host)
        self.sim.tick()

    def test_profile_has_required_keys(self):
        profile = self.sim.get_power_profile()
        assert 'summary' in profile
        assert 'hosts' in profile
        assert 'pue_history' in profile

    def test_summary_pue_geq_one(self):
        profile = self.sim.get_power_profile()
        assert profile['summary']['pue'] >= 1.0

    def test_host_count_matches_registered(self):
        profile = self.sim.get_power_profile()
        assert len(profile['hosts']) == 3

    def test_each_host_profile_has_required_fields(self):
        profile = self.sim.get_power_profile()
        required = {'host_id', 'power_state', 'model_name', 'idle_power_w', 'peak_power_w', 'current_power_w', 'efficiency_pct'}
        for h in profile['hosts']:
            assert required.issubset(set(h.keys()))

    def test_efficiency_pct_between_zero_and_hundred(self):
        profile = self.sim.get_power_profile()
        for h in profile['hosts']:
            assert 0.0 <= h['efficiency_pct'] <= 100.0

    def test_pue_rating_string_assigned(self):
        profile = self.sim.get_power_profile()
        assert isinstance(profile['summary']['pue_rating'], str)
        assert len(profile['summary']['pue_rating']) > 0

    def test_total_facility_w_equals_it_plus_cooling(self):
        profile = self.sim.get_power_profile()
        s = profile['summary']
        assert s['total_facility_w'] == pytest.approx(s['it_power_w'] + s['cooling_power_w'], rel=1e-3)
