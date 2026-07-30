import unittest
from backend.simulation.power_model import LinearPowerModel
from backend.simulation.thermal_model import ThermalModel

class TestSimulationModels(unittest.TestCase):
    """
    Unit test cases for simulator power and thermal calculations.
    """
    def setUp(self):
        # Initialize default linear power model (80W idle, 250W max, 10W sleep)
        self.power_model = LinearPowerModel(idle_power=80.0, max_power=250.0, sleep_power=10.0)
        # Initialize default thermal model (22°C ambient)
        self.thermal_model = ThermalModel(ambient_temp=22.0, thermal_resistance=0.08, cooling_coefficient=0.15)

    def test_power_model_active_states(self):
        """
        Verify power calculation matches the linear interpolation equation.
        Power = Idle + (Max - Idle) * Util
        """
        # 1. Active at 0% utilization
        p_0 = self.power_model.get_power(0.0, "active")
        self.assertAlmostEqual(p_0, 80.0)

        # 2. Active at 50% utilization
        # 80 + (250 - 80) * 0.5 = 80 + 85 = 165W
        p_50 = self.power_model.get_power(0.5, "active")
        self.assertAlmostEqual(p_50, 165.0)

        # 3. Active at 100% utilization
        p_100 = self.power_model.get_power(1.0, "active")
        self.assertAlmostEqual(p_100, 250.0)

        # 4. Out of bounds clamp check
        p_over = self.power_model.get_power(1.5, "active")
        self.assertAlmostEqual(p_over, 250.0)

        p_under = self.power_model.get_power(-0.2, "active")
        self.assertAlmostEqual(p_under, 80.0)

    def test_power_model_sleep_and_off(self):
        """
        Verify sleep and off states return the constant specs.
        """
        p_sleep = self.power_model.get_power(0.5, "sleep")
        self.assertAlmostEqual(p_sleep, 10.0)

        p_off = self.power_model.get_power(0.9, "off")
        self.assertAlmostEqual(p_off, 0.0)

    def test_thermal_model_temperature_increase(self):
        """
        Verify core temperature rises when power draw generates more heat than dissipated.
        """
        # Core starting at ambient 22°C, server running at 100W draw
        # Heat generated = 100 * 0.08 = 8°C
        # Heat dissipated = 0.15 * (22.0 - 22.0) = 0°C
        # Next temp = 22.0 + 8.0 - 0.0 = 30.0°C
        t_next = self.thermal_model.update_temperature(22.0, 100.0)
        self.assertAlmostEqual(t_next, 30.0)

    def test_thermal_model_dissipation_cooling(self):
        """
        Verify temperature drops towards ambient if heat dissipation exceeds power generation.
        """
        # Server core is hot at 60°C, but server is now turned off (0W draw)
        # Heat generated = 0 * 0.08 = 0°C
        # Heat dissipated = 0.15 * (60.0 - 22.0) = 0.15 * 38.0 = 5.7°C
        # Next temp = 60.0 + 0.0 - 5.7 = 54.3°C
        t_next = self.thermal_model.update_temperature(60.0, 0.0)
        self.assertAlmostEqual(t_next, 54.3)

if __name__ == "__main__":
    unittest.main()
