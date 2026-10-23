"""
Unit tests for the InputValidator module and edge cases.
Covers requirements 10, 11, 12, 13, 14, 15, 22.
"""

import pytest
import pandas as pd
from src.validation.input_validator import InputValidator


class TestValidation:
    def test_empty_dataframe(self):
        """Test 10 & 11: Empty workload validation."""
        empty_df = pd.DataFrame()
        is_valid, errors, _ = InputValidator.validate_workload_dataframe(empty_df)
        assert is_valid is False
        assert any("empty" in e.lower() for e in errors)

    def test_missing_required_columns(self):
        """Test 12: Malformed schema missing mandatory columns."""
        df = pd.DataFrame({
            "task_id": ["T1", "T2"],
            "arrival_time": [0.0, 1.0],
            "cpu_demand": [2.0, 4.0]
            # Missing memory_demand and duration
        })
        is_valid, errors, _ = InputValidator.validate_workload_dataframe(df)
        assert is_valid is False
        assert any("missing mandatory columns" in e.lower() for e in errors)

    def test_duplicate_task_ids(self):
        """Test 13: Duplicate task ID detection."""
        df = pd.DataFrame({
            "task_id": ["T1", "T1", "T2"],
            "arrival_time": [0.0, 1.0, 2.0],
            "cpu_demand": [2.0, 4.0, 1.0],
            "memory_demand": [4.0, 8.0, 2.0],
            "duration": [10.0, 15.0, 20.0]
        })
        is_valid, errors, _ = InputValidator.validate_workload_dataframe(df)
        assert is_valid is False
        assert any("duplicate task_id" in e.lower() for e in errors)

    def test_invalid_negative_and_zero_values(self):
        """Test 14: Invalid negative and zero resource fields."""
        df = pd.DataFrame({
            "task_id": ["T1"],
            "arrival_time": [-5.0],  # Negative arrival
            "cpu_demand": [0.0],    # Zero CPU
            "memory_demand": [-4.0],# Negative memory
            "duration": [0.0]       # Zero duration
        })
        is_valid, errors, _ = InputValidator.validate_workload_dataframe(df)
        assert is_valid is False
        assert len(errors) >= 3

    def test_impossible_deadlines(self):
        """Test 15: Detection of impossible deadlines."""
        # 1. Deadline earlier than arrival time (Fatal Error)
        df_fatal = pd.DataFrame({
            "task_id": ["T1"],
            "arrival_time": [10.0],
            "cpu_demand": [2.0],
            "memory_demand": [4.0],
            "duration": [20.0],
            "deadline": [5.0] # Earlier than arrival!
        })
        is_valid, errors, _ = InputValidator.validate_workload_dataframe(df_fatal)
        assert is_valid is False
        assert any("cannot be earlier than arrival_time" in e.lower() for e in errors)

        # 2. Deadline earlier than arrival + duration (Warning)
        df_warn = pd.DataFrame({
            "task_id": ["T2"],
            "arrival_time": [0.0],
            "cpu_demand": [2.0],
            "memory_demand": [4.0],
            "duration": [20.0],
            "deadline": [15.0] # 15 < 0 + 20
        })
        is_valid, errors, warnings = InputValidator.validate_workload_dataframe(df_warn)
        assert is_valid is True
        assert len(warnings) > 0
        assert any("impossible deadline" in w.lower() for w in warnings)

    def test_invalid_server_configuration(self):
        """Test 22: Detection of invalid server configuration parameters."""
        bad_server = {
            "server_id": "BadSrv",
            "cpu_capacity": -8.0,
            "memory_capacity": 16.0,
            "idle_power": 300.0,
            "max_power": 200.0,  # Idle exceeds max!
            "sleep_power": -10.0,
            "alpha": 0.5         # Alpha < 1.0!
        }
        is_valid, errors = InputValidator.validate_server_config(bad_server)
        assert is_valid is False
        assert len(errors) >= 3

    def test_invalid_scheduler_weights(self):
        """Test 22: Detection of invalid scheduler weights."""
        bad_weights = {"w_energy": -0.5, "w_time": 0.0}
        is_valid, errors = InputValidator.validate_weights(bad_weights)
        assert is_valid is False
