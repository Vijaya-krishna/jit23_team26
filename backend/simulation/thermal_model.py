class ThermalModel:
    """
    Simulates CPU core temperature changes over time.
    Uses discrete Newton's Law of Cooling, where core heat rises with power draw,
    and heat dissipates depending on the cooling coefficient.
    """
    def __init__(
        self,
        ambient_temp: float = 22.0,
        thermal_resistance: float = 0.08,  # °C per Watt thermal resistance
        cooling_coefficient: float = 0.15,   # Dissipation factor to ambient
        critical_temp: float = 85.0
    ):
        self.ambient_temp = ambient_temp
        self.thermal_resistance = thermal_resistance
        self.cooling_coefficient = cooling_coefficient
        self.critical_temp = critical_temp

    def update_temperature(self, current_temp: float, power_draw: float) -> float:
        """
        Compute the new core temperature after one simulation step (tick).
        """
        # Heat generation from power draw
        heat_generated = power_draw * self.thermal_resistance
        
        # Heat dissipation to ambient environment
        heat_dissipated = self.cooling_coefficient * (current_temp - self.ambient_temp)
        
        # Next state temperature
        next_temp = current_temp + heat_generated - heat_dissipated
        
        # Lower bound is ambient temperature, upper limit clamped for physical logic
        return max(self.ambient_temp, min(100.0, next_temp))
