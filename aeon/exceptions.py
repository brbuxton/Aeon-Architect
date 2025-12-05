"""Base exception hierarchy for Aeon Core."""

import traceback
from typing import Any, Dict, Optional

from aeon.observability.models import ErrorRecord, ErrorSeverity


class AeonError(Exception):
    """Base exception for all Aeon errors."""

    # Base error code - subclasses should override
    ERROR_CODE: str = "AEON.UNKNOWN.000"
    SEVERITY: ErrorSeverity = ErrorSeverity.ERROR

    def to_error_record(self, context: Optional[Dict[str, Any]] = None) -> ErrorRecord:
        """
        Convert exception to ErrorRecord for structured logging.

        Args:
            context: Optional additional context for diagnosis

        Returns:
            ErrorRecord with error code, severity, message, and context
        """
        return ErrorRecord(
            code=self.ERROR_CODE,
            severity=self.SEVERITY,
            message=str(self),
            affected_component="unknown",
            context=context,
            stack_trace="".join(traceback.format_exception(type(self), self, self.__traceback__)),
        )


class RefinementError(AeonError):
    """Raised when refinement operations fail."""

    ERROR_CODE: str = "AEON.REFINEMENT.001"
    SEVERITY: ErrorSeverity = ErrorSeverity.ERROR

    def to_error_record(self, context: Optional[Dict[str, Any]] = None) -> ErrorRecord:
        """Convert RefinementError to ErrorRecord."""
        error_context = context or {}
        error_context.setdefault("affected_component", "refinement")
        return ErrorRecord(
            code=self.ERROR_CODE,
            severity=self.SEVERITY,
            message=str(self),
            affected_component="refinement",
            context=error_context,
            stack_trace="".join(traceback.format_exception(type(self), self, self.__traceback__)),
        )


class ExecutionError(AeonError):
    """Raised when step execution fails."""

    ERROR_CODE: str = "AEON.EXECUTION.001"
    SEVERITY: ErrorSeverity = ErrorSeverity.ERROR

    def to_error_record(self, context: Optional[Dict[str, Any]] = None) -> ErrorRecord:
        """Convert ExecutionError to ErrorRecord."""
        error_context = context or {}
        error_context.setdefault("affected_component", "execution")
        return ErrorRecord(
            code=self.ERROR_CODE,
            severity=self.SEVERITY,
            message=str(self),
            affected_component="execution",
            context=error_context,
            stack_trace="".join(traceback.format_exception(type(self), self, self.__traceback__)),
        )


class ValidationError(AeonError):
    """Raised when validation fails."""

    ERROR_CODE: str = "AEON.VALIDATION.001"
    SEVERITY: ErrorSeverity = ErrorSeverity.ERROR

    def to_error_record(self, context: Optional[Dict[str, Any]] = None) -> ErrorRecord:
        """Convert ValidationError to ErrorRecord."""
        error_context = context or {}
        error_context.setdefault("affected_component", "validation")
        return ErrorRecord(
            code=self.ERROR_CODE,
            severity=self.SEVERITY,
            message=str(self),
            affected_component="validation",
            context=error_context,
            stack_trace="".join(traceback.format_exception(type(self), self, self.__traceback__)),
        )


class PlanError(AeonError):
    """Raised when plan operations fail."""

    ERROR_CODE: str = "AEON.PLAN.001"
    SEVERITY: ErrorSeverity = ErrorSeverity.ERROR

    def to_error_record(self, context: Optional[Dict[str, Any]] = None) -> ErrorRecord:
        """Convert PlanError to ErrorRecord."""
        error_context = context or {}
        error_context.setdefault("affected_component", "plan")
        return ErrorRecord(
            code=self.ERROR_CODE,
            severity=self.SEVERITY,
            message=str(self),
            affected_component="plan",
            context=error_context,
            stack_trace="".join(traceback.format_exception(type(self), self, self.__traceback__)),
        )


class ToolError(AeonError):
    """Raised when tool operations fail."""

    ERROR_CODE: str = "AEON.TOOL.001"
    SEVERITY: ErrorSeverity = ErrorSeverity.ERROR

    def to_error_record(self, context: Optional[Dict[str, Any]] = None) -> ErrorRecord:
        """Convert ToolError to ErrorRecord."""
        error_context = context or {}
        error_context.setdefault("affected_component", "tool")
        return ErrorRecord(
            code=self.ERROR_CODE,
            severity=self.SEVERITY,
            message=str(self),
            affected_component="tool",
            context=error_context,
            stack_trace="".join(traceback.format_exception(type(self), self, self.__traceback__)),
        )


class MemoryError(AeonError):
    """Raised when memory operations fail."""

    ERROR_CODE: str = "AEON.MEMORY.001"
    SEVERITY: ErrorSeverity = ErrorSeverity.ERROR

    def to_error_record(self, context: Optional[Dict[str, Any]] = None) -> ErrorRecord:
        """Convert MemoryError to ErrorRecord."""
        error_context = context or {}
        error_context.setdefault("affected_component", "memory")
        return ErrorRecord(
            code=self.ERROR_CODE,
            severity=self.SEVERITY,
            message=str(self),
            affected_component="memory",
            context=error_context,
            stack_trace="".join(traceback.format_exception(type(self), self, self.__traceback__)),
        )


class LLMError(AeonError):
    """Raised when LLM adapter operations fail."""

    ERROR_CODE: str = "AEON.LLM.001"
    SEVERITY: ErrorSeverity = ErrorSeverity.ERROR

    def to_error_record(self, context: Optional[Dict[str, Any]] = None) -> ErrorRecord:
        """Convert LLMError to ErrorRecord."""
        error_context = context or {}
        error_context.setdefault("affected_component", "llm")
        return ErrorRecord(
            code=self.ERROR_CODE,
            severity=self.SEVERITY,
            message=str(self),
            affected_component="llm",
            context=error_context,
            stack_trace="".join(traceback.format_exception(type(self), self, self.__traceback__)),
        )


class SupervisorError(AeonError):
    """Raised when supervisor cannot repair an error."""

    ERROR_CODE: str = "AEON.SUPERVISOR.001"
    SEVERITY: ErrorSeverity = ErrorSeverity.ERROR

    def to_error_record(self, context: Optional[Dict[str, Any]] = None) -> ErrorRecord:
        """Convert SupervisorError to ErrorRecord."""
        error_context = context or {}
        error_context.setdefault("affected_component", "supervisor")
        return ErrorRecord(
            code=self.ERROR_CODE,
            severity=self.SEVERITY,
            message=str(self),
            affected_component="supervisor",
            context=error_context,
            stack_trace="".join(traceback.format_exception(type(self), self, self.__traceback__)),
        )


class TTLExpiredError(AeonError):
    """Raised when TTL expires."""

    ERROR_CODE: str = "AEON.PHASE.001"
    SEVERITY: ErrorSeverity = ErrorSeverity.CRITICAL

    def to_error_record(self, context: Optional[Dict[str, Any]] = None) -> ErrorRecord:
        """Convert TTLExpiredError to ErrorRecord."""
        error_context = context or {}
        error_context.setdefault("affected_component", "phase")
        return ErrorRecord(
            code=self.ERROR_CODE,
            severity=self.SEVERITY,
            message=str(self),
            affected_component="phase",
            context=error_context,
            stack_trace="".join(traceback.format_exception(type(self), self, self.__traceback__)),
        )








