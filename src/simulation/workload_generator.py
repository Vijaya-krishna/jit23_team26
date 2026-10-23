"""
Workload Generator for the Energy-Aware Dynamic Task Scheduling Framework.
Generates reproducible synthetic big data workloads (Low, Medium, Bursty) and manages CSV persistence.
"""

import random
import pandas as pd
from typing import List, Dict, Any, Optional
from src.models.task import Task
from src.utils.exceptions import ValidationError


class WorkloadCategory:
    LOW = "low"
    MEDIUM = "medium"
    BURSTY = "bursty"


class WorkloadGenerator:
    """
    Generates synthetic traces of big data processing tasks with realistic arrival patterns,
    resource requirements (CPU cores, RAM), execution durations, and deadlines.
    """

    @staticmethod
    def generate_workload(
        num_tasks: int = 100,
        category: str = WorkloadCategory.MEDIUM,
        seed: int = 42,
        max_arrival_span: float = 300.0
    ) -> List[Task]:
        """
        Generates deterministic list of Task instances based on specified category profile.
        """
        rng = random.Random(seed)
        tasks: List[Task] = []

        if num_tasks <= 0:
            return []

        # Parameter presets for workload categories
        if category == WorkloadCategory.LOW:
            # Low load: sparse arrivals, moderate task durations, plenty of deadline slack
            arrival_rate_lambda = 0.5  # tasks per second
            cpu_choices = [1.0, 2.0, 4.0]
            mem_choices = [2.0, 4.0, 8.0]
            min_dur, max_dur = 10.0, 35.0
            slack_multiplier = 3.5

        elif category == WorkloadCategory.BURSTY:
            # Bursty load: arrival clusters, high peak CPU demand, tighter deadlines
            arrival_rate_lambda = 2.5
            cpu_choices = [2.0, 4.0, 8.0, 16.0]
            mem_choices = [4.0, 8.0, 16.0, 32.0]
            min_dur, max_dur = 5.0, 45.0
            slack_multiplier = 1.8

        else: # MEDIUM (Default)
            arrival_rate_lambda = 1.0
            cpu_choices = [1.0, 2.0, 4.0, 8.0]
            mem_choices = [2.0, 4.0, 8.0, 16.0]
            min_dur, max_dur = 10.0, 40.0
            slack_multiplier = 2.5

        current_arrival = 0.0

        for i in range(1, num_tasks + 1):
            if category == WorkloadCategory.BURSTY:
                # Intermittent burst logic: 30% chance of sudden burst arrival
                if rng.random() < 0.35:
                    inter_arrival = rng.uniform(0.0, 0.2)
                else:
                    inter_arrival = rng.expovariate(arrival_rate_lambda)
            else:
                inter_arrival = rng.expovariate(arrival_rate_lambda)

            current_arrival += inter_arrival
            if current_arrival > max_arrival_span:
                current_arrival = rng.uniform(0.0, max_arrival_span)

            cpu = float(rng.choice(cpu_choices))
            mem = float(rng.choice(mem_choices))
            duration = round(rng.uniform(min_dur, max_dur), 2)
            priority = rng.randint(1, 10)

            # Deadline: 80% of tasks have deadline, 20% open-ended
            deadline = None
            if rng.random() < 0.85:
                slack = round(duration * rng.uniform(1.2, slack_multiplier), 2)
                deadline = round(current_arrival + duration + slack, 2)

            task = Task(
                task_id=f"T{i:04d}",
                name=f"BigDataJob_{i:04d}",
                arrival_time=round(current_arrival, 2),
                cpu_demand=cpu,
                memory_demand=mem,
                duration=duration,
                priority=priority,
                deadline=deadline
            )
            tasks.append(task)

        # Sort tasks by arrival time
        tasks.sort(key=lambda t: t.arrival_time)
        return tasks

    @staticmethod
    def tasks_to_dataframe(tasks: List[Task]) -> pd.DataFrame:
        """Converts task objects into a structured pandas DataFrame."""
        rows = [t.to_dict() for t in tasks]
        return pd.DataFrame(rows)

    @staticmethod
    def dataframe_to_tasks(df: pd.DataFrame) -> List[Task]:
        """Converts a pandas DataFrame into a list of validated Task objects."""
        tasks: List[Task] = []
        for idx, row in df.iterrows():
            tasks.append(Task.from_dict(row.to_dict()))
        return tasks

    @staticmethod
    def export_to_csv(tasks: List[Task], file_path: str):
        """Exports task workload to a CSV file."""
        df = WorkloadGenerator.tasks_to_dataframe(tasks)
        df.to_csv(file_path, index=False)

    @staticmethod
    def load_from_csv(file_path: str) -> List[Task]:
        """Loads and parses tasks from a CSV file."""
        df = pd.read_csv(file_path)
        return WorkloadGenerator.dataframe_to_tasks(df)
