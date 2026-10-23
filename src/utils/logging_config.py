"""
Logging configuration for the Energy-Aware Task Scheduling Framework.
Provides formatted console and file logging with runtime event tracking.
"""

import os
import logging
from typing import List, Dict, Any

_LOGGER = None
_DIAGNOSTIC_EVENTS: List[Dict[str, Any]] = []

def setup_logger(log_level: int = logging.INFO, log_file: str = "logs/framework.log") -> logging.Logger:
    """Configures and returns the central framework logger."""
    global _LOGGER
    if _LOGGER is not None:
        return _LOGGER

    # Ensure log directory exists
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    logger = logging.getLogger("energy_scheduler")
    logger.setLevel(log_level)
    logger.propagate = False

    # Avoid duplicate handlers if reconfigured
    if not logger.handlers:
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] [%(name)s:%(funcName)s:%(lineno)d] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        # File Handler
        try:
            fh = logging.FileHandler(log_file, encoding="utf-8")
            fh.setLevel(log_level)
            fh.setFormatter(formatter)
            logger.addHandler(fh)
        except Exception:
            pass  # Fallback to console only if file access issues occur

        # Console Handler
        ch = logging.StreamHandler()
        ch.setLevel(log_level)
        ch.setFormatter(formatter)
        logger.addHandler(ch)

    _LOGGER = logger
    return _LOGGER


def log_diagnostic_event(event_type: str, message: str, details: Dict[str, Any] = None):
    """
    Records a high-visibility diagnostic event for display in the dashboard error/diagnostic panel.
    Tracks fallback scheduling, resource warnings, and recoverable errors.
    """
    logger = setup_logger()
    entry = {
        "event_type": event_type,
        "message": message,
        "details": details or {}
    }
    _DIAGNOSTIC_EVENTS.append(entry)
    
    if event_type in ("ERROR", "EXCEPTION", "FALLBACK_TRIGGERED"):
        logger.error(f"[DIAGNOSTIC-{event_type}] {message} | Details: {details}")
    elif event_type in ("WARNING", "RESOURCE_VIOLATION_AVOIDED"):
        logger.warning(f"[DIAGNOSTIC-{event_type}] {message} | Details: {details}")
    else:
        logger.info(f"[DIAGNOSTIC-{event_type}] {message}")


def get_diagnostic_events() -> List[Dict[str, Any]]:
    """Retrieves all logged runtime diagnostic events."""
    return list(_DIAGNOSTIC_EVENTS)


def clear_diagnostic_events():
    """Clears the diagnostic events list (e.g. before a new simulation run)."""
    global _DIAGNOSTIC_EVENTS
    _DIAGNOSTIC_EVENTS = []
