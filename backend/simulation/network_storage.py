class NetworkInterface:
    """
    Simulates a network card interface detailing bandwidth allocation and limits.
    """
    def __init__(self, bandwidth_mbps: float = 10000.0):
        self.bandwidth_mbps = bandwidth_mbps
        self.current_utilization = 0.0  # Mbps

    def allocate(self, amount: float) -> bool:
        """
        Request additional network capacity. Returns false if link is saturated.
        """
        if self.current_utilization + amount <= self.bandwidth_mbps:
            self.current_utilization += amount
            return True
        return False

    def release(self, amount: float):
        """
        Release network capacity.
        """
        self.current_utilization = max(0.0, self.current_utilization - amount)

    def get_utilization_ratio(self) -> float:
        """
        Return network interface utilization ratio.
        """
        return self.current_utilization / self.bandwidth_mbps


class StorageUnit:
    """
    Simulates storage drive resources detailing capacity and speed.
    """
    def __init__(self, capacity_gb: float = 1000.0, read_write_speed_mbps: float = 500.0):
        self.capacity_gb = capacity_gb
        self.read_write_speed_mbps = read_write_speed_mbps
        self.current_utilization_gb = 0.0

    def allocate(self, amount_gb: float) -> bool:
        """
        Allocate storage space. Returns false if disk is full.
        """
        if self.current_utilization_gb + amount_gb <= self.capacity_gb:
            self.current_utilization_gb += amount_gb
            return True
        return False

    def release(self, amount_gb: float):
        """
        Release storage space.
        """
        self.current_utilization_gb = max(0.0, self.current_utilization_gb - amount_gb)

    def get_utilization_ratio(self) -> float:
        """
        Return disk space utilization ratio.
        """
        return self.current_utilization_gb / self.capacity_gb
