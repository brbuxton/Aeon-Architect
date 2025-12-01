"""Base exception hierarchy for Aeon Core."""


class AeonError(Exception):
    """Base exception for all Aeon errors."""

    pass


class ValidationError(AeonError):
    """Raised when validation fails."""

    pass


class PlanError(AeonError):
    """Raised when plan operations fail."""

    pass


class ToolError(AeonError):
    """Raised when tool operations fail."""

    pass


class MemoryError(AeonError):
    """Raised when memory operations fail."""

    pass


class LLMError(AeonError):
    """Raised when LLM adapter operations fail."""

    pass


class SupervisorError(AeonError):
    """Raised when supervisor cannot repair an error."""

    pass


class TTLExpiredError(AeonError):
    """Raised when TTL expires."""

    pass







