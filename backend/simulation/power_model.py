from abc import ABC, abstractmethod


class IPowerModel(ABC):
    """
    Interface for data center server power models.
    Follows Dependency Inversion Principle — all models are interchangeable.
    """
    model_name: str = "abstract"

    @abstractmethod
    def get_power(self, cpu_utilization: float, power_state: str) -> float:
        """
        Calculate server power draw in Watts.
        cpu_utilization: float in [0.0, 1.0]
        power_state: 'ACTIVE' | 'SLEEP' | 'OFF'
        """
        pass

    @property
    def idle_power(self) -> float:
        return 0.0

    @property
    def peak_power(self) -> float:
        return 0.0


class LinearPowerModel(IPowerModel):
    """
    Standard linear server power draw model (baseline).
    P(u) = P_idle + (P_peak - P_idle) * u

    Reference: Standard data center simulation baseline.
    - Idle Power:  80 W  (32% of peak — typical commodity server)
    - Peak Power: 250 W
    - Sleep Power: 10 W  (ACPI S3 suspend-to-RAM)
    - Standby:      5 W  (BMC/IPMI chip draw in hard-off)
    """
    model_name = "Linear"

    def __init__(
        self,
        idle_power: float = None,
        max_power: float = None,
        sleep_power: float = None,
        standby_power: float = 0.0,
        **kwargs,
    ):
        """Initialize LinearPowerModel.
        Supports both legacy parameter names (idle_power_w, peak_power_w, etc.)
        and test-oriented names (idle_power, max_power, sleep_power, standby_power).
        """
        # Resolve possible legacy kwargs
        if idle_power is None:
            idle_power = kwargs.get('idle_power_w', 80.0)
        if max_power is None:
            max_power = kwargs.get('peak_power_w', 250.0)
        if sleep_power is None:
            sleep_power = kwargs.get('sleep_power_w', 10.0)
        if 'standby_power_w' in kwargs:
            standby_power = kwargs['standby_power_w']
        self._idle_power = idle_power
        self._peak_power = max_power
        self.sleep_power_w = sleep_power
        self.standby_power_w = standby_power


    @property
    def idle_power(self) -> float:
        return self._idle_power

    @property
    def peak_power(self) -> float:
        return self._peak_power

    def get_power(self, cpu_utilization: float, power_state: str) -> float:
        state = power_state.upper()
        if state == "OFF":
            return self.standby_power_w
        if state == "SLEEP":
            return self.sleep_power_w
        # ACTIVE — linear interpolation
        u = max(0.0, min(1.0, cpu_utilization))
        return self._idle_power + (self._peak_power - self._idle_power) * u


class CubicPowerModel(IPowerModel):
    """
    Research-grade cubic server power model.
    P(u) = P_idle + (P_peak - P_idle) * u^alpha  (alpha ≈ 2.5 per Barroso & Hölzle 2007)

    Captures the super-linear relationship between CPU load and power draw
    caused by voltage/frequency scaling and memory sub-system costs.
    Servers consume ~70% peak power at 100% load but only ~30% at idle.

    Reference:
      Barroso, L.A. & Hölzle, U. (2007). The Case for Energy-Proportional Computing.
      IEEE Computer, 40(12), 33-37.
    """
    model_name = "Cubic (Barroso-Hölzle)"

    def __init__(
        self,
        idle_power_w: float = 80.0,
        peak_power_w: float = 250.0,
        sleep_power_w: float = 10.0,
        standby_power_w: float = 5.0,
        alpha: float = 2.5,
    ):
        self._idle_power = idle_power_w
        self._peak_power = peak_power_w
        self.sleep_power_w = sleep_power_w
        self.standby_power_w = standby_power_w
        self.alpha = alpha  # Exponent controlling curvature

    @property
    def idle_power(self) -> float:
        return self._idle_power

    @property
    def peak_power(self) -> float:
        return self._peak_power

    def get_power(self, cpu_utilization: float, power_state: str) -> float:
        state = power_state.upper()
        if state == "OFF":
            return self.standby_power_w
        if state == "SLEEP":
            return self.sleep_power_w
        u = max(0.0, min(1.0, cpu_utilization))
        return self._idle_power + (self._peak_power - self._idle_power) * (u ** self.alpha)


class SPECpowerModel(IPowerModel):
    """
    SPECpower_ssj2008 benchmark-based piecewise-linear power model.
    Uses a 11-point lookup table (0%→100% in 10% steps) matching
    industry-measured server power curves.

    Lookup table derived from SPECpower_ssj2008 average across 200+ submissions:
    https://www.spec.org/power_ssj2008/results/

    At each utilisation breakpoint (0%-100%), the power fraction relative to
    peak is pre-tabulated and linearly interpolated between points.
    """
    model_name = "SPECpower (piecewise)"

    # Power fraction at [0%, 10%, 20%, 30%, 40%, 50%, 60%, 70%, 80%, 90%, 100%]
    # Source: SPECpower_ssj2008 average results (fraction of peak power)
    SPEC_FRACTIONS = [0.333, 0.414, 0.492, 0.561, 0.624, 0.679, 0.731, 0.783, 0.839, 0.906, 1.000]

    def __init__(
        self,
        peak_power_w: float = 250.0,
        sleep_power_w: float = 10.0,
        standby_power_w: float = 5.0,
    ):
        self._peak_power = peak_power_w
        self._idle_power = peak_power_w * self.SPEC_FRACTIONS[0]   # P at 0% load
        self.sleep_power_w = sleep_power_w
        self.standby_power_w = standby_power_w

    @property
    def idle_power(self) -> float:
        return self._idle_power

    @property
    def peak_power(self) -> float:
        return self._peak_power

    def get_power(self, cpu_utilization: float, power_state: str) -> float:
        state = power_state.upper()
        if state == "OFF":
            return self.standby_power_w
        if state == "SLEEP":
            return self.sleep_power_w
        u = max(0.0, min(1.0, cpu_utilization))
        # Map utilisation to index range [0, 10]
        idx_float = u * 10.0
        idx_low = int(idx_float)
        idx_high = min(idx_low + 1, 10)
        frac = idx_float - idx_low
        power_fraction = self.SPEC_FRACTIONS[idx_low] * (1 - frac) + self.SPEC_FRACTIONS[idx_high] * frac
        return self._peak_power * power_fraction

