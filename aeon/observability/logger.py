"""JSONL logger for orchestration cycles."""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from aeon.observability.models import LogEntry


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
        )

