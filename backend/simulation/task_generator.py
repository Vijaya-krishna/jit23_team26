import random
from typing import Dict, Any, List

class WorkloadGenerator:
    """
    Generates synthetic cloud computing workloads.
    Produces random task profiles representing big data computations.
    """
    def __init__(self):
        # Establish deterministic randomness seeds if needed, or default to standard random
        pass

    @staticmethod
    def generate_task(task_id: int, arrival_tick: int) -> Dict[str, Any]:
        """
        Generate a single task with randomized specs.
        """
        # Determine priority category
        priority = random.choice(["HIGH", "MEDIUM", "LOW"])
        
        # CPU core bounds: 1 to 8 cores (highly dependent on priority)
        if priority == "HIGH":
            cpu_cores = random.randint(4, 8)
            ram_mb = random.choice([8000, 16000, 32000])
            execution_time = random.randint(15, 30)  # Ticks
        elif priority == "MEDIUM":
            cpu_cores = random.randint(2, 4)
            ram_mb = random.choice([4000, 8000, 16000])
            execution_time = random.randint(8, 20)
        else:  # LOW
            cpu_cores = random.randint(1, 2)
            ram_mb = random.choice([1000, 2000, 4000])
            execution_time = random.randint(4, 10)

        # Storage capacity bounds (10 GB to 500 GB)
        storage_gb = float(random.randint(10, 500))
        # Bandwidth bounds (100 Mbps to 2000 Mbps)
        bandwidth_mbps = float(random.randint(100, 2000))

        # Deadline computation: arrival + execution_time + random relaxation buffer
        buffer_ticks = random.randint(5, 15)
        deadline = arrival_tick + execution_time + buffer_ticks

        return {
            "id": task_id,
            "cpu_requirement": float(cpu_cores),
            "ram_requirement": float(ram_mb),
            "storage_requirement": storage_gb,
            "bandwidth_requirement": bandwidth_mbps,
            "priority": priority,
            "execution_time": execution_time,
            "deadline": deadline,
            "arrival_time": arrival_tick,
            "status": "WAITING",
            "vm_id": None
        }

    def generate_batch(self, start_task_id: int, count: int, arrival_tick: int) -> List[Dict[str, Any]]:
        """
        Generate a batch of tasks.
        """
        tasks = []
        for i in range(count):
            tasks.append(self.generate_task(start_task_id + i, arrival_tick))
        return tasks
