"""
Input Validator for the Energy-Aware Dynamic Task Scheduling Framework.
Performs strict schema, constraint, and semantic validations on workloads, servers, and configurations.
"""

from typing import List, Dict, Any, Tuple, Optional
import pandas as pd
from src.utils.exceptions import ValidationError


class InputValidator:
    """
    Validates workload files, configuration dictionaries, and server parameters.
    Returns structured validation result with detailed messages and warning flags.
    """

    REQUIRED_WORKLOAD_COLUMNS = [
        "task_id",
        "arrival_time",
        "cpu_demand",
        "memory_demand",
        "duration"
    ]

    OPTIONAL_WORKLOAD_COLUMNS = [
        "name",
        "priority",
        "deadline"
    ]

    MAX_TASKS_LIMIT = 20000

    @classmethod
    def validate_workload_dataframe(cls, df: pd.DataFrame) -> Tuple[bool, List[str], List[str]]:
        """
        Validates an uploaded or generated workload DataFrame.
        Returns (is_valid, error_list, warning_list).
        """
        errors: List[str] = []
        warnings: List[str] = []

        if df is None or df.empty:
            return False, ["Workload is empty. At least 1 task record is required."], []

        # Check for task count limits
        if len(df) > cls.MAX_TASKS_LIMIT:
            errors.append(f"Workload exceeds maximum supported limit of {cls.MAX_TASKS_LIMIT} tasks (got {len(df)}).")

        # Column existence check
        missing_cols = [col for col in cls.REQUIRED_WORKLOAD_COLUMNS if col not in df.columns]
        if missing_cols:
            errors.append(f"Missing mandatory columns: {', '.join(missing_cols)}")
            return False, errors, warnings

        # Null value checks in required columns
        for col in cls.REQUIRED_WORKLOAD_COLUMNS:
            null_count = df[col].isnull().sum()
            if null_count > 0:
                errors.append(f"Column '{col}' contains {null_count} missing (NaN/null) values.")

        if errors:
            return False, errors, warnings

        # Duplicate Task ID check
        duplicates = df[df.duplicated(subset=["task_id"], keep=False)]
        if not duplicates.empty:
            dup_ids = duplicates["task_id"].unique()[:5]
            errors.append(
                f"Duplicate task_id entries detected ({len(duplicates)} occurrences). "
                f"Examples: {', '.join(map(str, dup_ids))}"
            )

        # Numeric type and boundary checks
        for idx, row in df.iterrows():
            tid = row["task_id"]
            # Arrival time
            try:
                arr = float(row["arrival_time"])
                if arr < 0.0:
                    errors.append(f"Row {idx} (Task {tid}): arrival_time must be >= 0.0 (got {arr}).")
            except (ValueError, TypeError):
                errors.append(f"Row {idx} (Task {tid}): arrival_time is not a valid number.")

            # CPU demand
            try:
                cpu = float(row["cpu_demand"])
                if cpu <= 0.0:
                    errors.append(f"Row {idx} (Task {tid}): cpu_demand must be > 0.0 (got {cpu}).")
            except (ValueError, TypeError):
                errors.append(f"Row {idx} (Task {tid}): cpu_demand is not a valid number.")

            # Memory demand
            try:
                mem = float(row["memory_demand"])
                if mem <= 0.0:
                    errors.append(f"Row {idx} (Task {tid}): memory_demand must be > 0.0 (got {mem}).")
            except (ValueError, TypeError):
                errors.append(f"Row {idx} (Task {tid}): memory_demand is not a valid number.")

            # Duration
            try:
                dur = float(row["duration"])
                if dur <= 0.0:
                    errors.append(f"Row {idx} (Task {tid}): duration must be > 0.0 (got {dur}).")
            except (ValueError, TypeError):
                errors.append(f"Row {idx} (Task {tid}): duration is not a valid number.")

            # Priority (if present)
            if "priority" in row and pd.notnull(row["priority"]):
                try:
                    prio = int(row["priority"])
                    if prio < 1 or prio > 10:
                        warnings.append(f"Row {idx} (Task {tid}): priority {prio} is outside standard range [1, 10].")
                except (ValueError, TypeError):
                    warnings.append(f"Row {idx} (Task {tid}): priority is not an integer.")

            # Deadline (if present)
            if "deadline" in row and pd.notnull(row["deadline"]):
                try:
                    dl = float(row["deadline"])
                    arr = float(row["arrival_time"]) if "arrival_time" in row else 0.0
                    dur = float(row["duration"]) if "duration" in row else 0.0
                    if dl < arr:
                        errors.append(
                            f"Row {idx} (Task {tid}): deadline ({dl}) cannot be earlier than arrival_time ({arr})."
                        )
                    elif dl < (arr + dur):
                        warnings.append(
                            f"Row {idx} (Task {tid}): impossible deadline ({dl} < arrival {arr} + duration {dur}). "
                            f"Task is guaranteed to miss deadline."
                        )
                except (ValueError, TypeError):
                    errors.append(f"Row {idx} (Task {tid}): deadline is not a valid number.")

            # Cap error reporting to avoid massive logs on catastrophic inputs
            if len(errors) >= 30:
                errors.append("... and more errors encountered. Processing truncated.")
                break

        is_valid = len(errors) == 0
        return is_valid, errors, warnings

    @classmethod
    def validate_server_config(cls, server_dict: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validates individual server configuration dictionary.
        """
        errors: List[str] = []
        sid = server_dict.get("server_id", "Unknown")

        cpu = server_dict.get("cpu_capacity", 0.0)
        mem = server_dict.get("memory_capacity", 0.0)
        p_idle = server_dict.get("idle_power", 0.0)
        p_max = server_dict.get("max_power", 0.0)
        p_sleep = server_dict.get("sleep_power", 0.0)
        alpha = server_dict.get("alpha", 1.5)

        if cpu <= 0.0:
            errors.append(f"Server {sid}: cpu_capacity must be > 0.0 (got {cpu}).")
        if mem <= 0.0:
            errors.append(f"Server {sid}: memory_capacity must be > 0.0 (got {mem}).")
        if p_idle < 0.0 or p_max < 0.0:
            errors.append(f"Server {sid}: power parameters cannot be negative.")
        if p_idle > p_max:
            errors.append(f"Server {sid}: idle_power ({p_idle}W) cannot exceed max_power ({p_max}W).")
        if p_sleep < 0.0 or p_sleep > p_idle:
            errors.append(f"Server {sid}: sleep_power ({p_sleep}W) must be between 0.0 and idle_power ({p_idle}W).")
        if alpha < 1.0:
            errors.append(f"Server {sid}: alpha exponent must be >= 1.0 (got {alpha}).")

        return len(errors) == 0, errors

    @classmethod
    def validate_weights(cls, weights: Dict[str, float]) -> Tuple[bool, List[str]]:
        """
        Validates algorithm objective weights.
        """
        errors = []
        for k, v in weights.items():
            if v < 0.0:
                errors.append(f"Weight '{k}' cannot be negative (got {v}).")
        if sum(weights.values()) <= 0.0:
            errors.append("At least one objective weight must be strictly positive.")
        return len(errors) == 0, errors
