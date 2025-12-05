# Proposed Schema Definitions for Review

This document contains proposed Pydantic model definitions for `PhaseTransitionContract` and `ContextPropagationSpecification` to be added to `contracts/interfaces.md`.

**Review Status**: Pending approval  
**Proposed By**: Analysis Report Findings A1 and U1  
**Date**: 2025-12-05

---

## 1. PhaseTransitionContract Model

**Purpose**: Define explicit structure for phase transition contracts with input requirements, output guarantees, invariants, and failure modes.

**Location**: Add to `contracts/interfaces.md` in the "Phase Transition Contract Interfaces" section (before function signatures).

### Proposed Definition

```python
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Literal
from enum import Enum

class FailureModeRetryability(str, Enum):
    """Retryability classification for failure modes."""
    RETRYABLE = "retryable"
    NON_RETRYABLE = "non_retryable"

class FailureMode(BaseModel):
    """Represents a single failure condition in a phase transition contract."""
    
    failure_condition: str = Field(..., description="Human-readable description of failure condition")
    retryable: FailureModeRetryability = Field(..., description="Whether this failure can be retried")
    error_code: str = Field(..., description="Error code in format 'AEON.PHASE_TRANSITION.<TRANSITION>.<CODE>'")
    severity: Literal["CRITICAL", "ERROR", "WARNING", "INFO"] = Field(..., description="Error severity level")
    
    model_config = {"extra": "forbid"}

class InputRequirement(BaseModel):
    """Defines a single input requirement with validation rules."""
    
    field_name: str = Field(..., description="Name of the required field")
    field_type: str = Field(..., description="Expected type (e.g., 'str', 'int', 'Dict', 'List')")
    validation_rule: str = Field(..., description="Validation rule (e.g., 'non-null', '> 0', 'UUID v4')")
    description: str = Field(..., description="Human-readable description of the requirement")
    
    model_config = {"extra": "forbid"}

class OutputGuarantee(BaseModel):
    """Defines a single output guarantee."""
    
    field_name: str = Field(..., description="Name of the guaranteed output field")
    field_type: str = Field(..., description="Expected type (e.g., 'str', 'Dict', 'ExecutionPass')")
    description: str = Field(..., description="Human-readable description of the guarantee")
    
    model_config = {"extra": "forbid"}

class Invariant(BaseModel):
    """Defines a single invariant that must hold across the transition."""
    
    assertion: str = Field(..., description="Invariant assertion (e.g., 'correlation_id unchanged', 'TTL > 0')")
    description: str = Field(..., description="Human-readable description of the invariant")
    
    model_config = {"extra": "forbid"}

class PhaseTransitionContract(BaseModel):
    """
    Explicit contract defining input requirements, output guarantees, invariants, and failure modes
    for a phase transition (A→B, B→C, C→D, D→A/B).
    
    Contracts are testable and deterministic.
    """
    
    transition_name: Literal["A→B", "B→C", "C→D", "D→A/B"] = Field(..., description="Transition identifier")
    input_requirements: List[InputRequirement] = Field(..., description="Required inputs with validation rules")
    output_guarantees: List[OutputGuarantee] = Field(..., description="Guaranteed outputs")
    invariants: List[Invariant] = Field(..., description="Invariants that must hold across transition")
    failure_modes: List[FailureMode] = Field(..., description="Enumerated failure conditions with retryability")
    
    model_config = {"extra": "forbid"}
    
    def validate_inputs(self, inputs: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate inputs against contract requirements.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Implementation validates all input_requirements are present and match validation_rules
        pass
    
    def validate_outputs(self, outputs: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate outputs against contract guarantees.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Implementation validates all output_guarantees are present
        pass
    
    def check_invariants(self, inputs: Dict[str, Any], outputs: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Check invariants hold across transition.
        
        Returns:
            Tuple of (all_satisfied, error_message)
        """
        # Implementation checks all invariants are satisfied
        pass
```

---

## 2. ContextPropagationSpecification Model

**Purpose**: Define explicit structure for context propagation specifications with per-phase field requirements.

**Location**: Add to `contracts/interfaces.md` in the "Context Propagation Interfaces" section (before function signatures).

### Proposed Definition

```python
from pydantic import BaseModel, Field, field_validator
from typing import Dict, Any, List, Literal, Set
from enum import Enum

class FieldRequirementType(str, Enum):
    """Type of field requirement in context propagation."""
    MUST_HAVE = "must_have"
    MUST_PASS_UNCHANGED = "must_pass_unchanged"
    MAY_MODIFY = "may_modify"
    PROHIBITED = "prohibited"

class ContextFieldSpec(BaseModel):
    """Specification for a single context field."""
    
    field_name: str = Field(..., description="Name of the context field")
    field_type: str = Field(..., description="Expected type (e.g., 'str', 'int', 'Dict', 'List')")
    requirement_type: FieldRequirementType = Field(..., description="Type of requirement for this field")
    validation_rule: str = Field(..., description="Validation rule (e.g., 'non-null', 'UUID v4', 'ISO 8601')")
    description: str = Field(..., description="Human-readable description of the field")
    
    model_config = {"extra": "forbid"}

class ContextPropagationSpecification(BaseModel):
    """
    Structured specification defining, for each phase (A, B, C, D), what fields must be constructed
    before phase entry (must-have), what fields must be passed unchanged between phases (must-pass-unchanged),
    and what fields may be produced/modified only by specific phases (may-modify).
    
    This is process context only (not memory). The specification must be explicit and testable,
    enabling validation that all required fields are present before LLM calls.
    """
    
    phase: Literal["A", "B", "C", "C1", "C2", "C3", "D"] = Field(..., description="Phase identifier (C1=Execute, C2=Evaluate, C3=Refine)")
    transition_from: Optional[Literal["A", "B", "C", "D"]] = Field(None, description="Previous phase (for transition context)")
    must_have_fields: List[ContextFieldSpec] = Field(..., description="Fields that MUST be present and non-null before phase entry")
    must_pass_unchanged_fields: List[ContextFieldSpec] = Field(..., description="Fields that MUST retain same value across phases")
    may_modify_fields: List[ContextFieldSpec] = Field(..., description="Fields that MAY be added/modified only by this phase")
    prohibited_fields: List[ContextFieldSpec] = Field(default_factory=list, description="Fields that MUST NOT appear in this phase's input context")
    
    model_config = {"extra": "forbid"}
    
    @field_validator('must_have_fields')
    @classmethod
    def validate_must_have_fields(cls, v: List[ContextFieldSpec]) -> List[ContextFieldSpec]:
        """Ensure must_have fields have requirement_type MUST_HAVE."""
        for field in v:
            if field.requirement_type != FieldRequirementType.MUST_HAVE:
                raise ValueError(f"Field {field.field_name} in must_have_fields must have requirement_type MUST_HAVE")
        return v
    
    @field_validator('must_pass_unchanged_fields')
    @classmethod
    def validate_unchanged_fields(cls, v: List[ContextFieldSpec]) -> List[ContextFieldSpec]:
        """Ensure unchanged fields have requirement_type MUST_PASS_UNCHANGED."""
        for field in v:
            if field.requirement_type != FieldRequirementType.MUST_PASS_UNCHANGED:
                raise ValueError(f"Field {field.field_name} in must_pass_unchanged_fields must have requirement_type MUST_PASS_UNCHANGED")
        return v
    
    def validate_context(self, context: Dict[str, Any]) -> Tuple[bool, Optional[str], List[str]]:
        """
        Validate context against specification.
        
        Returns:
            Tuple of (is_valid, error_message, missing_fields)
        """
        # Implementation validates:
        # - All must_have_fields are present and non-null
        # - All must_pass_unchanged_fields are present (if applicable)
        # - No prohibited_fields are present
        pass
    
    def build_llm_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build minimal LLM context from full context dictionary.
        
        Returns:
            Dictionary with only must_have_fields extracted
        """
        # Implementation extracts only must_have_fields
        pass
```

---

## 3. Example Contract Definitions

To help visualize how these models would be used, here are example contract definitions that match the spec requirements:

### Example: A→B Phase Transition Contract

```python
PHASE_TRANSITION_CONTRACT_A_TO_B = PhaseTransitionContract(
    transition_name="A→B",
    input_requirements=[
        InputRequirement(
            field_name="task_profile",
            field_type="Dict",
            validation_rule="non-null, contains required profile fields",
            description="Task profile from Phase A"
        ),
        InputRequirement(
            field_name="initial_plan",
            field_type="Dict",
            validation_rule="non-null, valid plan structure",
            description="Initial plan from Phase A"
        ),
        InputRequirement(
            field_name="ttl_remaining",
            field_type="int",
            validation_rule="> 0",
            description="TTL cycles remaining (must be > 0)"
        ),
    ],
    output_guarantees=[
        OutputGuarantee(
            field_name="refined_plan",
            field_type="Dict",
            description="Refined plan with valid step fragments"
        ),
    ],
    invariants=[
        Invariant(
            assertion="correlation_id unchanged",
            description="correlation_id MUST remain identical across transition"
        ),
        Invariant(
            assertion="execution_start_timestamp unchanged",
            description="execution_start_timestamp MUST remain identical across transition"
        ),
        Invariant(
            assertion="TTL_remaining > 0 at phase entry",
            description="TTL_remaining MUST be > 0 at phase entry"
        ),
    ],
    failure_modes=[
        FailureMode(
            failure_condition="incomplete profile",
            retryable=FailureModeRetryability.NON_RETRYABLE,
            error_code="AEON.PHASE_TRANSITION.A_TO_B.INCOMPLETE_PROFILE",
            severity="CRITICAL"
        ),
        FailureMode(
            failure_condition="malformed plan (JSON parsing error)",
            retryable=FailureModeRetryability.RETRYABLE,
            error_code="AEON.PHASE_TRANSITION.A_TO_B.MALFORMED_PLAN_JSON",
            severity="ERROR"
        ),
        FailureMode(
            failure_condition="malformed plan (structural invalidity)",
            retryable=FailureModeRetryability.NON_RETRYABLE,
            error_code="AEON.PHASE_TRANSITION.A_TO_B.MALFORMED_PLAN_STRUCTURE",
            severity="CRITICAL"
        ),
    ]
)
```

### Example: Phase B Context Propagation Specification

```python
CONTEXT_PROPAGATION_SPEC_PHASE_B = ContextPropagationSpecification(
    phase="B",
    transition_from="A",
    must_have_fields=[
        ContextFieldSpec(
            field_name="request",
            field_type="str",
            requirement_type=FieldRequirementType.MUST_HAVE,
            validation_rule="non-null, non-empty string",
            description="Original user input string"
        ),
        ContextFieldSpec(
            field_name="task_profile",
            field_type="Dict",
            requirement_type=FieldRequirementType.MUST_HAVE,
            validation_rule="non-null",
            description="Task profile from Phase A"
        ),
        ContextFieldSpec(
            field_name="initial_plan",
            field_type="Dict",
            requirement_type=FieldRequirementType.MUST_HAVE,
            validation_rule="non-null, valid plan structure",
            description="Initial plan from Phase A"
        ),
        ContextFieldSpec(
            field_name="pass_number",
            field_type="int",
            requirement_type=FieldRequirementType.MUST_HAVE,
            validation_rule=">= 0",
            description="Pass number in multi-pass execution"
        ),
        ContextFieldSpec(
            field_name="phase",
            field_type="str",
            requirement_type=FieldRequirementType.MUST_HAVE,
            validation_rule="== 'B'",
            description="Current phase identifier"
        ),
        ContextFieldSpec(
            field_name="ttl_remaining",
            field_type="int",
            requirement_type=FieldRequirementType.MUST_HAVE,
            validation_rule="> 0",
            description="TTL cycles remaining"
        ),
        ContextFieldSpec(
            field_name="correlation_id",
            field_type="str",
            requirement_type=FieldRequirementType.MUST_HAVE,
            validation_rule="non-null, UUID v4",
            description="Correlation ID for this execution"
        ),
        ContextFieldSpec(
            field_name="execution_start_timestamp",
            field_type="str",
            requirement_type=FieldRequirementType.MUST_HAVE,
            validation_rule="non-null, ISO 8601 timestamp",
            description="Execution start timestamp"
        ),
    ],
    must_pass_unchanged_fields=[
        ContextFieldSpec(
            field_name="correlation_id",
            field_type="str",
            requirement_type=FieldRequirementType.MUST_PASS_UNCHANGED,
            validation_rule="UUID v4, immutable",
            description="Correlation ID MUST remain identical across all phases"
        ),
        ContextFieldSpec(
            field_name="execution_start_timestamp",
            field_type="str",
            requirement_type=FieldRequirementType.MUST_PASS_UNCHANGED,
            validation_rule="ISO 8601, immutable",
            description="Execution start timestamp MUST remain identical across all phases"
        ),
    ],
    may_modify_fields=[
        ContextFieldSpec(
            field_name="refined_plan",
            field_type="Dict",
            requirement_type=FieldRequirementType.MAY_MODIFY,
            validation_rule="valid plan structure",
            description="Refined plan (may be added/modified only by Phase B)"
        ),
        ContextFieldSpec(
            field_name="refinement_changes",
            field_type="List",
            requirement_type=FieldRequirementType.MAY_MODIFY,
            validation_rule="list of change dictionaries",
            description="Refinement changes (may be added/modified only by Phase B)"
        ),
    ],
    prohibited_fields=[
        ContextFieldSpec(
            field_name="execution_results",
            field_type="Any",
            requirement_type=FieldRequirementType.PROHIBITED,
            validation_rule="must not appear",
            description="Execution results MUST NOT appear in Phase B context"
        ),
    ]
)
```

---

## 4. Recommended Edits to interfaces.md

### Edit Location 1: After line 18 (after "Backward Compatible" principle)

Add a new section:

```markdown
## Data Models

This section defines the Pydantic models used by the interface contracts.
These models provide explicit, testable structures for phase transition contracts
and context propagation specifications.

### PhaseTransitionContract Model

[Insert the PhaseTransitionContract model definition from section 1 above]

### ContextPropagationSpecification Model

[Insert the ContextPropagationSpecification model definition from section 2 above]
```

### Edit Location 2: Update interface signatures to use models

The existing function signatures already reference these types, so no changes needed.
However, we should add notes that these are the defined models:

- Line 32: `contract: PhaseTransitionContract` → Already correct, will now reference defined model
- Line 129: `specification: ContextPropagationSpecification` → Already correct, will now reference defined model

---

## 5. Questions for Review

1. **Field types**: Should `field_type` be a string (as proposed) or use Python types (e.g., `str`, `Dict[str, Any]`)? Using strings allows JSON serialization but loses type checking.

2. **Validation methods**: Should validation methods be part of the Pydantic models (as proposed) or separate functions? Pydantic models could use `@field_validator` but complex validation might be better as separate functions.

3. **Contract constants**: Should contracts be defined as Python constants (like the examples) or loaded from JSON/YAML? Constants provide type safety but JSON provides runtime flexibility.

4. **Context field specification**: Should `ContextFieldSpec` allow a field to appear in multiple requirement types (e.g., both `must_have` and `must_pass_unchanged`)? The spec table suggests this is possible (correlation_id appears in both).

5. **Phase C sub-phases**: Should Phase C be split into C1, C2, C3 specifications or one unified C specification? The spec table shows separate rows for C1/C2/C3.

---

## Review Checklist

- [ ] Review PhaseTransitionContract structure
- [ ] Review ContextPropagationSpecification structure  
- [ ] Review example contract definitions
- [ ] Answer questions 1-5 above
- [ ] Approve or request modifications
- [ ] Once approved, add to `contracts/interfaces.md`

---

**Next Steps After Approval**:
1. Add model definitions to `contracts/interfaces.md`
2. Update tasks.md to reference these models explicitly
3. Create example contract constants in orchestration/phases.py (separate task)

