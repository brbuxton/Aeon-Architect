"""JSONL logger for orchestration cycles."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from aeon.observability.models import ExecutionMetrics, LogEntry


class JSONLLogger:
    """JSONL logger for orchestration cycle logging."""

    def __init__(self, file_path: Optional[Path] = None) -> None:
        """
        Initialize JSONL logger.

        Args:
            file_path: Path to JSONL log file (optional, defaults to None for no-op logger)
        """
        self.file_path = file_path

    def log_entry(self, entry: LogEntry) -> None:
        """
        Write a log entry to the JSONL file.

        Args:
            entry: LogEntry to write

        Note:
            This method is non-blocking and will silently fail if file write fails.
        """
        if not self.file_path:
            return  # No-op if no file path provided

        try:
            # Append mode - creates file if it doesn't exist
            with open(self.file_path, 'a', encoding='utf-8') as f:
                json_str = entry.model_dump_json()
                f.write(json_str + '\n')
        except Exception:
            # Non-blocking: silently fail on write errors
            pass

    def format_entry(
        self,
        step_number: int,
        plan_state: dict,
        llm_output: dict,
        supervisor_actions: list = None,
        tool_calls: list = None,
        ttl_remaining: int = 0,
        errors: list = None,
        pass_number: Optional[int] = None,
        phase: Optional[str] = None,
    ) -> LogEntry:
        """
        Format a log entry from orchestration cycle data.

        Args:
            step_number: Sequential cycle identifier
            plan_state: Snapshot of plan at cycle start
            llm_output: Raw LLM response
            supervisor_actions: Supervisor repairs in this cycle (optional)
            tool_calls: Tool invocations in this cycle (optional)
            ttl_remaining: Cycles left before expiration
            errors: Errors in this cycle (optional)
            pass_number: Pass number in multi-pass execution (optional, for Sprint 2)
            phase: Current phase in multi-pass execution (optional, for Sprint 2)

        Returns:
            Formatted LogEntry
        """
        return LogEntry(
            step_number=step_number,
            plan_state=plan_state,
            llm_output=llm_output,
            supervisor_actions=supervisor_actions or [],
            tool_calls=tool_calls or [],
            ttl_remaining=ttl_remaining,
            errors=errors or [],
            timestamp=datetime.now().isoformat(),
            pass_number=pass_number,
            phase=phase,
        )

    def log_multipass_entry(
        self,
        pass_number: int,
        phase: str,
        plan_state: dict,
        execution_results: list = None,
        evaluation_results: dict = None,
        refinement_changes: list = None,
        ttl_remaining: int = 0,
        errors: list = None,
    ) -> None:
        """
        Log a multi-pass execution entry (Sprint 2).

        Args:
            pass_number: Pass number in multi-pass execution
            phase: Current phase (A, B, C, D)
            plan_state: Snapshot of plan at pass start
            execution_results: Step outputs and tool results (optional)
            evaluation_results: Convergence assessment and semantic validation (optional)
            refinement_changes: Plan/step modifications (optional)
            ttl_remaining: TTL cycles remaining
            errors: Errors in this pass (optional)
        """
        if not self.file_path:
            return  # No-op if no file path provided

        try:
            entry = {
                "type": "multipass_entry",
                "pass_number": pass_number,
                "phase": phase,
                "plan_state": plan_state,
                "execution_results": execution_results or [],
                "evaluation_results": evaluation_results or {},
                "refinement_changes": refinement_changes or [],
                "ttl_remaining": ttl_remaining,
                "errors": errors or [],
                "timestamp": datetime.now().isoformat(),
            }
            with open(self.file_path, 'a', encoding='utf-8') as f:
                json_str = json.dumps(entry, default=str)
                f.write(json_str + '\n')
        except Exception:
            # Non-blocking: silently fail on write errors
            pass

