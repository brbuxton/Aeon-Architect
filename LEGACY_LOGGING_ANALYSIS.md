# Legacy Logging Methods Analysis

## Current State

### `format_entry` (Legacy - Still in Use)
- **Location**: `aeon/observability/logger.py:53`
- **Usage**: Called from `aeon/kernel/orchestrator.py:406` in `_log_cycle()` method
- **Purpose**: Creates LogEntry with `event="cycle"` (default) for legacy cycle-based logging
- **Origin**: Sprint 1 (US7 - Orchestration Cycle Logging)
- **Status**: **ACTIVE** - Still used by `orchestrator.execute()` method

### `log_multipass_entry` (Legacy - Unused)
- **Location**: `aeon/observability/logger.py:95`
- **Usage**: **NOT USED** anywhere in codebase
- **Purpose**: Was intended for Sprint 2 multi-pass logging but never integrated
- **Origin**: Sprint 2 (pre-005 spec)
- **Status**: **UNUSED** - Dead code

## Role in Post-Sprint 5 Logging Strategy

### Current Logging Architecture (Post-005)

**Primary Logging (Phase-Aware):**
- `log_phase_entry` / `log_phase_exit` - Phase transitions
- `log_state_transition` - State changes
- `log_refinement_outcome` - Refinement events
- `log_evaluation_outcome` - Evaluation events
- `log_error` / `log_error_recovery` - Error events
- `log_step_execution_outcome` - Execution events
- All use `event` field with specific event types
- All include `correlation_id` for traceability

**Legacy Logging (Cycle-Based):**
- `format_entry` - Creates LogEntry with `event="cycle"`
- Used by `orchestrator.execute()` (single-pass execution)
- Maintains backward compatibility (FR-009)

### Backward Compatibility Requirement

**FR-009**: "The system MUST ensure log schemas are stable and backward-compatible within the same major version."

This means:
- Legacy `format_entry` must continue to work
- LogEntry model supports both legacy (`event="cycle"`) and new event types
- Existing log parsers should continue to work

## Recommendations

### 1. `format_entry` - Keep for Backward Compatibility
**Action**: **MAINTAIN** - Keep method but mark as legacy
- Still used by `orchestrator.execute()` (single-pass mode)
- Required for backward compatibility (FR-009)
- Should eventually migrate to phase-aware logging

**Migration Path**:
- When `orchestrator.execute()` is refactored, migrate to phase-aware logging
- Until then, keep `format_entry` for compatibility

### 2. `log_multipass_entry` - Remove Dead Code
**Action**: **DEPRECATE AND REMOVE**
- Not used anywhere in codebase
- Superseded by phase-aware logging methods
- Creates raw dicts instead of LogEntry models (inconsistent)
- No backward compatibility concerns (never used)

## Backlog Item Recommendation

Add to BACKLOG.md:

```markdown
## [Category: infrastructure] [Impact: medium] Legacy Logging Migration

**Issue**: Legacy logging methods need refactoring for consistency
- `format_entry` is still used by `orchestrator.execute()` (single-pass mode)
- `log_multipass_entry` is unused dead code

**Current State**:
- `format_entry`: Creates LogEntry with `event="cycle"` for legacy cycle-based logging
- `log_multipass_entry`: Unused method from Sprint 2, creates raw dicts instead of LogEntry models

**Action Needed**:
1. **Remove `log_multipass_entry`** (dead code, never used)
2. **Migrate `orchestrator.execute()` to phase-aware logging**:
   - Replace `format_entry` calls with phase-aware logging methods
   - Use `log_phase_entry` / `log_phase_exit` for phase transitions
   - Use `log_state_transition` for state changes
   - Ensure correlation_id is included in all entries
3. **Deprecate `format_entry`** after migration:
   - Mark as deprecated with warning
   - Remove after migration complete
   - Maintain backward compatibility during transition (FR-009)

**Benefits**:
- Consistent logging architecture across all execution modes
- Better traceability with correlation IDs
- Cleaner codebase without dead code
- Full phase-aware logging coverage

**Dependencies**: None (can be done independently)
**Effort**: Low-Medium (mostly refactoring existing code)
```

## Summary

- **`format_entry`**: Keep for now, migrate when `orchestrator.execute()` is refactored
- **`log_multipass_entry`**: Remove (dead code)
- **Backlog Item**: Add migration task to refactor legacy logging

