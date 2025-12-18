"""Short-Term Memory (STM) implementation.

This module implements the STM class that provides in-memory storage
for session-scoped memory entries with capacity and TTL bounds.
"""

import json
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from uuid import uuid4

from aeon.memory.interface import MemoryAccessInterface
from aeon.memory.models import (
    MemoryDeleteResult,
    MemoryEntry,
    MemoryEntryMetadata,
    MemoryUsageStats,
    MemoryWriteResult,
)

if TYPE_CHECKING:
    from aeon.observability.logger import JSONLLogger


class STM(MemoryAccessInterface):
    """Short-Term Memory (STM) implementation.

    Stores memory entries in-memory only with capacity and TTL bounds.
    All operations degrade gracefully and never raise exceptions.
    """

    def __init__(
        self, 
        capacity: int = 1000, 
        initial_ttl: int = 10,
        logger: Optional["JSONLLogger"] = None,
    ) -> None:
        """
        Initialize STM.

        Args:
            capacity: Maximum entries per session (default: 1000)
            initial_ttl: Initial TTL value for new entries (default: 10)
            logger: Optional JSONLLogger for observability (default: None for no-op logging)
        """
        self._store: Dict[str, Dict[str, MemoryEntry]] = {}
        self._capacity: int = capacity
        self._initial_ttl: int = initial_ttl
        self._logger: Optional["JSONLLogger"] = logger
        # Usage statistics tracking (T102)
        # Track statistics per session for observability
        self._usage_stats: Dict[str, Dict[str, int]] = {}  # {session_id: {"considered": int, "injected": int, "failures": int}}

    def _log_memory_operation(
        self,
        operation_type: str,
        session_id: str,
        execution_id: Optional[str] = None,
        phase: Optional[str] = None,
        entry_count: Optional[int] = None,
        success: Optional[bool] = None,
        error_type: Optional[str] = None,
    ) -> None:
        """
        Log a memory operation using JSONLLogger (content-free observability) (T100, T101).

        This is a helper method that wraps JSONLLogger.log_memory_operation().
        It gracefully handles the case where logger is None (no-op).
        """
        if self._logger:
            self._logger.log_memory_operation(
                operation_type=operation_type,
                session_id=session_id,
                correlation_id=None,  # Will be available when wired in Phase 8
                execution_id=execution_id,
                phase=phase,
                entry_count=entry_count,
                success=success,
                error_type=error_type,
            )

    def _decrement_ttl_for_session(self, session_id: str) -> None:
        """
        Autonomously decrement TTL for all entries in a session.

        This method is called on any STM operation (read, write, select) for session_id
        to preserve recency bias. After decrementing, expired entries (TTL <= 0) are
        removed from physical memory.

        Args:
            session_id: Session to decrement TTL for
        """
        try:
            if session_id not in self._store:
                return

            session_entries = self._store[session_id]
            expired_entry_ids = []

            # Decrement TTL for all entries in session
            for entry_id, entry in session_entries.items():
                if entry.ttl > 0:
                    entry.ttl -= 1
                    # Track expired entries for removal
                    if entry.ttl <= 0:
                        expired_entry_ids.append(entry_id)

            # Remove expired entries from physical memory
            for entry_id in expired_entry_ids:
                del session_entries[entry_id]

            if expired_entry_ids:
                self._log_memory_operation(
                    operation_type="_decrement_ttl_for_session",
                    session_id=session_id,
                    entry_count=len(expired_entry_ids),
                    success=True,
                )

        except Exception as e:
            # Graceful degradation: log error but continue
            error_type = type(e).__name__
            self._log_memory_operation(
                operation_type="_decrement_ttl_for_session",
                session_id=session_id,
                success=False,
                error_type=error_type,
            )

    def write_entry(
        self,
        session_id: str,
        execution_id: str,
        phase: str,
        content: Dict[str, Any],
    ) -> MemoryWriteResult:
        """
        Store a memory entry with annotations.

        Args:
            session_id: Session owning the entry (required)
            execution_id: Execution (turn) that created the entry (required)
            phase: Phase (A, B, C, D, E) that created the entry (required)
            content: Phase-native, raw execution artifacts (JSON-compatible, required)

        Returns:
            MemoryWriteResult with success, entry_id, evicted_count, error
        """
        try:
            # Validate required annotations
            if not session_id or not isinstance(session_id, str):
                self._log_memory_operation(
                    operation_type="write_entry",
                    session_id=str(session_id) if session_id else "unknown",
                    execution_id=execution_id,
                    phase=phase,
                    success=False,
                    error_type="ValidationError",
                )
                return MemoryWriteResult(
                    success=False,
                    error="Invalid session_id: must be non-empty string",
                )

            if not execution_id or not isinstance(execution_id, str):
                self._log_memory_operation(
                    operation_type="write_entry",
                    session_id=session_id,
                    execution_id=str(execution_id) if execution_id else "unknown",
                    phase=phase,
                    success=False,
                    error_type="ValidationError",
                )
                return MemoryWriteResult(
                    success=False,
                    error="Invalid execution_id: must be non-empty string",
                )

            if phase not in ["A", "B", "C", "D", "E"]:
                self._log_memory_operation(
                    operation_type="write_entry",
                    session_id=session_id,
                    execution_id=execution_id,
                    phase=phase,
                    success=False,
                    error_type="ValidationError",
                )
                return MemoryWriteResult(
                    success=False,
                    error=f"Invalid phase: must be one of A, B, C, D, E, got {phase}",
                )

            # Validate content serializability
            try:
                json.dumps(content)
            except (TypeError, ValueError) as e:
                self._log_memory_operation(
                    operation_type="write_entry",
                    session_id=session_id,
                    execution_id=execution_id,
                    phase=phase,
                    success=False,
                    error_type=type(e).__name__,
                )
                return MemoryWriteResult(
                    success=False,
                    error=f"Content not JSON-serializable: {e}",
                )

            # Initialize session store if needed
            if session_id not in self._store:
                self._store[session_id] = {}

            # Autonomously decrement TTL for all entries in session (preserves recency bias)
            self._decrement_ttl_for_session(session_id)

            # Get session entries
            session_entries = self._store[session_id]

            # Check capacity and evict if needed
            evicted_count = 0
            if len(session_entries) >= self._capacity:
                # Perform deterministic eviction (FIFO: oldest first)
                # Sort by created_at, then evict oldest entries
                sorted_entries = sorted(
                    session_entries.items(),
                    key=lambda x: (x[1].created_at, x[0]),
                )
                # Evict enough entries to make room for one new entry
                entries_to_evict = len(session_entries) - self._capacity + 1
                for i in range(entries_to_evict):
                    entry_id_to_evict = sorted_entries[i][0]
                    del session_entries[entry_id_to_evict]
                    evicted_count += 1

                self._log_memory_operation(
                    operation_type="write_entry",
                    session_id=session_id,
                    execution_id=execution_id,
                    phase=phase,
                    entry_count=evicted_count,
                    success=True,
                )

            # Generate unique entry_id
            entry_id = str(uuid4())

            # Create memory entry
            entry = MemoryEntry(
                session_id=session_id,
                execution_id=execution_id,
                phase=phase,
                content=content,
                ttl=self._initial_ttl,
                created_at=datetime.now(),
            )

            # Store entry
            session_entries[entry_id] = entry

            # Initialize usage stats for session if needed (T102)
            if session_id not in self._usage_stats:
                self._usage_stats[session_id] = {
                    "considered": 0,
                    "injected": 0,
                    "failures": 0,
                }

            # Log successful write with structural metadata only (T100)
            self._log_memory_operation(
                operation_type="write_entry",
                session_id=session_id,
                execution_id=execution_id,
                phase=phase,
                entry_count=len(session_entries),
                success=True,
            )

            return MemoryWriteResult(
                success=True,
                entry_id=entry_id,
                evicted_count=evicted_count,
            )

        except Exception as e:
            # Initialize usage stats for session if needed (T102)
            if session_id not in self._usage_stats:
                self._usage_stats[session_id] = {
                    "considered": 0,
                    "injected": 0,
                    "failures": 0,
                }
            # Track failure (T102)
            self._usage_stats[session_id]["failures"] += 1

            # Log memory failure with error type and context but NO content (T101)
            error_type = type(e).__name__
            self._log_memory_operation(
                operation_type="write_entry",
                session_id=session_id,
                execution_id=execution_id,
                phase=phase,
                success=False,
                error_type=error_type,
            )
            return MemoryWriteResult(
                success=False,
                error=str(e),
            )

    def read_entries(
        self,
        session_id: str,
        execution_id: Optional[str] = None,
        phase: Optional[str] = None,
    ) -> List[MemoryEntry]:
        """
        Retrieve memory entries matching filters.

        Args:
            session_id: Session to query (required)
            execution_id: Filter by execution_id (optional)
            phase: Filter by phase (optional)

        Returns:
            List of MemoryEntry objects matching filters. Empty list if no matches or on failure.
        """
        try:
            # Check if session exists
            if session_id not in self._store:
                return []

            # Autonomously decrement TTL for all entries in session (preserves recency bias)
            self._decrement_ttl_for_session(session_id)

            session_entries = self._store[session_id]

            # Filter entries (exclude expired entries with TTL <= 0)
            # Note: expired entries are already removed by _decrement_ttl_for_session,
            # but we double-check here for safety
            filtered_entries = []
            for entry in session_entries.values():
                # Exclude expired entries
                if entry.ttl <= 0:
                    continue

                # Apply filters
                if execution_id is not None and entry.execution_id != execution_id:
                    continue
                if phase is not None and entry.phase != phase:
                    continue

                filtered_entries.append(entry)

            # Log read operation with structural metadata only (T100)
            self._log_memory_operation(
                operation_type="read_entries",
                session_id=session_id,
                execution_id=execution_id,
                phase=phase,
                entry_count=len(filtered_entries),
                success=True,
            )

            return filtered_entries

        except Exception as e:
            # Initialize usage stats for session if needed (T102)
            if session_id not in self._usage_stats:
                self._usage_stats[session_id] = {
                    "considered": 0,
                    "injected": 0,
                    "failures": 0,
                }
            # Track failure (T102)
            self._usage_stats[session_id]["failures"] += 1

            # Log memory failure with error type and context but NO content (T101)
            error_type = type(e).__name__
            self._log_memory_operation(
                operation_type="read_entries",
                session_id=session_id,
                execution_id=execution_id,
                phase=phase,
                success=False,
                error_type=error_type,
            )
            return []

    def select_for_injection(
        self,
        session_id: str,
        context: Dict[str, Any],
        budget: int,
    ) -> Dict[str, Any]:
        """
        Select relevant entries and emit a deterministic, field-extracted contextual
        projection for prompt injection.

        Args:
            session_id: Session to query (required)
            context: Selection context (required). MUST include:
                - current_phase: str (required) - Current phase (A, B, C, D, E)
                - current_execution_id: Optional[str] - Current execution ID (for excluding current execution)
                - injection_point: str (required) - Injection point identifier
            budget: Injection budget (hard upper bound, no truncation of individual entries)

        Returns:
            Dict with keys:
                - context_blocks: List[str] - List of formatted context strings/blocks ready for prompt injection
                - non_authoritative_marker: str - Single header/footer wrapper text marking context as non-authoritative
        """
        try:
            # Check if session exists
            if session_id not in self._store:
                return {
                    "context_blocks": [],
                    "non_authoritative_marker": "Non-authoritative context from this session (for reference only)",
                }

            # Autonomously decrement TTL for all entries in session (preserves recency bias)
            self._decrement_ttl_for_session(session_id)

            # Extract context parameters (T082)
            current_phase = context.get("current_phase", "A")
            current_execution_id = context.get("current_execution_id")
            injection_point = context.get("injection_point", "")

            # Get session entries (expired entries already removed by _decrement_ttl_for_session)
            session_entries = self._store.get(session_id, {})
            
            # Filter entries by phase (T083)
            # Phase B prefers Phase B entries (primary), Phase D entries (secondary)
            # Phase D prefers Phase D entries (primary), Phase B entries (secondary)
            # Phase A rarely uses memory
            # Phase C and E never inject (handled by prompt registry, but we filter here too)
            filtered_entries = []
            for entry in session_entries.values():
                # Exclude expired entries (already removed, but double-check)
                if entry.ttl <= 0:
                    continue
                
                # Phase filtering (T083)
                if current_phase == "B":
                    # Phase B: prefer Phase B (primary), Phase D (secondary)
                    if entry.phase in ["B", "D"]:
                        filtered_entries.append(entry)
                elif current_phase == "D":
                    # Phase D: prefer Phase D (primary), Phase B (secondary)
                    if entry.phase in ["D", "B"]:
                        filtered_entries.append(entry)
                elif current_phase == "A":
                    # Phase A: rarely uses memory, but allow all phases
                    filtered_entries.append(entry)
                # Phase C and E: never inject (should not reach here, but filter anyway)
                elif current_phase in ["C", "E"]:
                    continue

            # Filter by execution (T084): prefer entries from earlier executions over current execution
            if current_execution_id:
                # Separate entries by execution
                earlier_execution_entries = [
                    e for e in filtered_entries if e.execution_id != current_execution_id
                ]
                current_execution_entries = [
                    e for e in filtered_entries if e.execution_id == current_execution_id
                ]
                # Prefer earlier execution entries
                filtered_entries = earlier_execution_entries + current_execution_entries
            else:
                # No current_execution_id provided, use all filtered entries
                pass

            # Order by recency (T085): created_at (most recent first), insertion order as tie-breaker
            # Sort by created_at descending, then by entry_id (as proxy for insertion order)
            filtered_entries.sort(
                key=lambda e: (e.created_at, e.session_id + e.execution_id + e.phase),
                reverse=True,
            )

            # Extract fields and format (T086, T087)
            context_blocks = []
            for entry in filtered_entries:
                try:
                    # Field extraction based on phase (T086)
                    block_parts = []
                    
                    if entry.phase == "B":
                        # Phase B: user request, goal, step descriptions
                        content = entry.content
                        if isinstance(content, dict):
                            # Extract user request (primary field for Phase B)
                            user_request = content.get("user_request") or content.get("user_prompt", "")
                            if user_request:
                                block_parts.append(f"Previous user request: {user_request}")
                            # Extract goal
                            goal = content.get("goal", "")
                            if goal:
                                block_parts.append(f"Previous goal: {goal}")
                            # Extract step descriptions
                            step_descriptions = content.get("step_descriptions", [])
                            if step_descriptions:
                                if isinstance(step_descriptions, list):
                                    descs = [str(s) for s in step_descriptions if s]
                                    if descs:
                                        block_parts.append(f"Previous steps: {', '.join(descs)}")
                                else:
                                    block_parts.append(f"Previous steps: {step_descriptions}")
                            # If no structured fields, use content as string representation (fallback)
                            if not block_parts:
                                import json
                                block_parts.append(f"Previous context: {json.dumps(content, indent=2)}")
                    
                    elif entry.phase == "D":
                        # Phase D: refinement reason, updated goal, updated step descriptions
                        content = entry.content
                        if isinstance(content, dict):
                            refinement_reason = content.get("refinement_reason") or content.get("reason", "")
                            if refinement_reason:
                                block_parts.append(f"Refinement reason: {refinement_reason}")
                            updated_goal = content.get("updated_goal") or content.get("goal", "")
                            if updated_goal:
                                block_parts.append(f"Updated goal: {updated_goal}")
                            # Phase D stores "updated_step_descriptions", not "step_descriptions"
                            step_descriptions = content.get("updated_step_descriptions") or content.get("step_descriptions") or content.get("steps", [])
                            if step_descriptions:
                                if isinstance(step_descriptions, list):
                                    descs = [str(s.get("description", s) if isinstance(s, dict) else s) for s in step_descriptions if s]
                                    if descs:
                                        block_parts.append(f"Updated step descriptions: {', '.join(descs)}")
                                else:
                                    block_parts.append(f"Updated step descriptions: {step_descriptions}")
                            # If no structured fields, use content as string representation (fallback)
                            if not block_parts:
                                import json
                                block_parts.append(f"Previous refinement: {json.dumps(content, indent=2)}")
                    
                    elif entry.phase == "A":
                        # Phase A: goal, task profile posture fields
                        content = entry.content
                        if isinstance(content, dict):
                            goal = content.get("goal") or content.get("plan_goal", "")
                            if goal:
                                block_parts.append(f"Previous goal: {goal}")
                            # Task profile fields
                            task_profile = content.get("task_profile") or {}
                            if isinstance(task_profile, dict):
                                reasoning_depth = task_profile.get("reasoning_depth")
                                if reasoning_depth:
                                    block_parts.append(f"Task profile - reasoning depth: {reasoning_depth}")
                            # If no structured fields, use content as string representation
                            if not block_parts:
                                import json
                                block_parts.append(f"Previous plan context: {json.dumps(content, indent=2)}")
                    
                    # Light formatting (T087): string concatenation, basic punctuation, line breaks only
                    # NO semantic transformation, summarization, paraphrasing, inference, rewriting
                    if block_parts:
                        formatted_block = "\n".join(block_parts)
                        context_blocks.append(formatted_block)
                
                except Exception as e:
                    # Graceful degradation: skip entry if extraction fails
                    self._log_memory_operation(
                        operation_type="select_for_injection",
                        session_id=session_id,
                        phase=entry.phase,
                        success=False,
                        error_type=type(e).__name__,
                    )
                    continue

            # Budget enforcement (T088): include context blocks in order until budget exhausted
            # Skip blocks that would exceed budget (no partial inclusion)
            budgeted_blocks = []
            current_budget = budget
            for block in context_blocks:
                block_size = len(block)
                if block_size <= current_budget:
                    budgeted_blocks.append(block)
                    current_budget -= block_size
                else:
                    # Block would exceed budget, skip it (no partial inclusion)
                    break

            # Non-authoritative marker (T089)
            non_authoritative_marker = "Non-authoritative context from this session (for reference only)"

            # Initialize usage stats for session if needed (T102)
            if session_id not in self._usage_stats:
                self._usage_stats[session_id] = {
                    "considered": 0,
                    "injected": 0,
                    "failures": 0,
                }

            # Track entries considered and injected (T102)
            # Considered: number of entries that passed filtering and were processed
            entries_considered = len(filtered_entries)
            # Injected: number of context blocks actually included (proportional to entries)
            # Since each block comes from one entry, blocks_selected approximates entries_injected
            entries_injected = len(budgeted_blocks)
            self._usage_stats[session_id]["considered"] += entries_considered
            self._usage_stats[session_id]["injected"] += entries_injected

            # Log selection with structural metadata only (T100)
            self._log_memory_operation(
                operation_type="select_for_injection",
                session_id=session_id,
                phase=current_phase,
                entry_count=entries_injected,
                success=True,
            )

            return {
                "context_blocks": budgeted_blocks,
                "non_authoritative_marker": non_authoritative_marker,
            }

        except Exception as e:
            # Initialize usage stats for session if needed (T102)
            if session_id not in self._usage_stats:
                self._usage_stats[session_id] = {
                    "considered": 0,
                    "injected": 0,
                    "failures": 0,
                }
            # Track failure (T102)
            self._usage_stats[session_id]["failures"] += 1

            # Log memory failure with error type and context but NO content (T101)
            error_type = type(e).__name__
            self._log_memory_operation(
                operation_type="select_for_injection",
                session_id=session_id,
                success=False,
                error_type=error_type,
            )
            return {
                "context_blocks": [],
                "non_authoritative_marker": "Non-authoritative context from this session (for reference only)",
            }

    def get_usage_stats(self, session_id: str) -> MemoryUsageStats:
        """
        Get memory usage statistics for observability (T102).

        Args:
            session_id: Session to query (required)

        Returns:
            MemoryUsageStats with memory usage information including:
            - memory_used: Whether memory was used in this execution
            - memory_entries_considered: Number of entries considered for injection
            - memory_entries_injected: Number of entries actually injected
            - memory_failures: Number of memory operation failures
            - total_entries: Total entries in session (for debugging)
            - expired_entries: Number of expired entries (for debugging)
        """
        try:
            # Autonomously decrement TTL for all entries in session (preserves recency bias)
            self._decrement_ttl_for_session(session_id)

            # Get session entries (may be empty if session doesn't exist)
            session_entries = self._store.get(session_id, {})

            # Count total and expired entries
            # Note: expired entries are already removed by _decrement_ttl_for_session,
            # but we count them here for stats (they should be 0 after removal)
            total_entries = len(session_entries)
            expired_entries = sum(1 for entry in session_entries.values() if entry.ttl <= 0)

            # Get tracked usage statistics (T102)
            usage_stats = self._usage_stats.get(session_id, {
                "considered": 0,
                "injected": 0,
                "failures": 0,
            })

            memory_used = total_entries > 0
            memory_entries_considered = usage_stats.get("considered", 0)
            memory_entries_injected = usage_stats.get("injected", 0)
            memory_failures = usage_stats.get("failures", 0)

            # Log usage stats retrieval with structural metadata only (T100)
            self._log_memory_operation(
                operation_type="get_usage_stats",
                session_id=session_id,
                entry_count=total_entries,
                success=True,
            )

            return MemoryUsageStats(
                memory_used=memory_used,
                memory_entries_considered=memory_entries_considered,
                memory_entries_injected=memory_entries_injected,
                memory_failures=memory_failures,
                total_entries=total_entries,
                expired_entries=expired_entries,
            )

        except Exception as e:
            # Graceful degradation: log error and return zero stats
            error_type = type(e).__name__
            self._log_memory_operation(
                operation_type="get_usage_stats",
                session_id=session_id,
                success=False,
                error_type=error_type,
            )
            return MemoryUsageStats(
                memory_used=False,
                memory_entries_considered=0,
                memory_entries_injected=0,
                memory_failures=0,
                total_entries=0,
                expired_entries=0,
            )

    def list_entries(self, session_id: str) -> List[MemoryEntryMetadata]:
        """
        List all memory entries for a session for audit purposes.

        Args:
            session_id: Session to query (required)

        Returns:
            List of MemoryEntryMetadata objects (metadata only, no raw content).
            Empty list on failure.
        """
        try:
            # Check if session exists
            if session_id not in self._store:
                return []

            # Autonomously decrement TTL for all entries in session (preserves recency bias)
            self._decrement_ttl_for_session(session_id)

            session_entries = self._store[session_id]

            # Convert entries to metadata (no raw content)
            # Note: expired entries are already removed by _decrement_ttl_for_session,
            # but we double-check here for safety
            metadata_list = []
            for entry in session_entries.values():
                # Exclude expired entries
                if entry.ttl <= 0:
                    continue

                metadata = MemoryEntryMetadata(
                    session_id=entry.session_id,
                    execution_id=entry.execution_id,
                    phase=entry.phase,
                    created_at=entry.created_at,
                    ttl=entry.ttl,
                )
                metadata_list.append(metadata)

            # Log list operation with structural metadata only (T100)
            self._log_memory_operation(
                operation_type="list_entries",
                session_id=session_id,
                entry_count=len(metadata_list),
                success=True,
            )

            return metadata_list

        except Exception as e:
            # Initialize usage stats for session if needed (T102)
            if session_id not in self._usage_stats:
                self._usage_stats[session_id] = {
                    "considered": 0,
                    "injected": 0,
                    "failures": 0,
                }
            # Track failure (T102)
            self._usage_stats[session_id]["failures"] += 1

            # Log memory failure with error type and context but NO content (T101)
            error_type = type(e).__name__
            self._log_memory_operation(
                operation_type="list_entries",
                session_id=session_id,
                success=False,
                error_type=error_type,
            )
            return []

    def delete_session_entries(self, session_id: str) -> MemoryDeleteResult:
        """
        Delete/remove all memory entries associated with a session.

        Args:
            session_id: Session to delete entries for (required)

        Returns:
            MemoryDeleteResult with success, entries_removed, error
        """
        try:
            # Check if session exists
            if session_id not in self._store:
                return MemoryDeleteResult(
                    success=True,
                    entries_removed=0,
                )

            session_entries = self._store[session_id]
            entries_removed = len(session_entries)

            # Delete all entries for this session
            del self._store[session_id]

            # Clear usage stats for this session
            if session_id in self._usage_stats:
                del self._usage_stats[session_id]

            # Log delete operation with structural metadata only (T100)
            self._log_memory_operation(
                operation_type="delete_session_entries",
                session_id=session_id,
                entry_count=entries_removed,
                success=True,
            )

            return MemoryDeleteResult(
                success=True,
                entries_removed=entries_removed,
            )

        except Exception as e:
            # Initialize usage stats for session if needed (T102)
            if session_id not in self._usage_stats:
                self._usage_stats[session_id] = {
                    "considered": 0,
                    "injected": 0,
                    "failures": 0,
                }
            # Track failure (T102)
            self._usage_stats[session_id]["failures"] += 1

            # Log memory failure with error type and context but NO content (T101)
            error_type = type(e).__name__
            self._log_memory_operation(
                operation_type="delete_session_entries",
                session_id=session_id,
                success=False,
                error_type=error_type,
            )
            return MemoryDeleteResult(
                success=False,
                entries_removed=0,
                error=str(e),
            )
