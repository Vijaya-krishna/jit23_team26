"""
Custom exceptions hierarchy for the Energy-Aware Task Scheduling Framework.
Provides clear, actionable error reporting and diagnostic context.
"""

class SchedulerFrameworkException(Exception):
    """Base exception for all framework errors."""
    def __init__(self, message: str, context: dict = None):
        super().__init__(message)
        self.message = message
        self.context = context or {}

    def __str__(self):
        if self.context:
            ctx_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            return f"{self.message} [Context: {ctx_str}]"
        return self.message


class ValidationError(SchedulerFrameworkException):
    """Raised when an input fails validation rules (schema, range, null checks)."""
    pass


class ResourceConstraintViolation(SchedulerFrameworkException):
    """Raised when a task assignment violates CPU, Memory, or capacity limits."""
    pass


class SchedulerAllocationError(SchedulerFrameworkException):
    """Raised when a scheduler encounters an unrecoverable allocation problem."""
    pass


class SimulationError(SchedulerFrameworkException):
    """Raised when an invalid discrete-event sequence or clock inversion occurs."""
    pass


class InvalidStateTransitionError(SchedulerFrameworkException):
    """Raised when a task or server attempts an illegal state transition."""
    pass


class ConfigurationError(SchedulerFrameworkException):
    """Raised when data center, algorithm, or simulation configuration is invalid."""
    pass


class ReportingError(SchedulerFrameworkException):
    """Raised when report generation, CSV export, or formatting fails."""
    pass
