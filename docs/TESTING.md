# Testing Guide: User Story 1 (Plan Generation)

## Test Cases for User Story 1

### ✅ Unit Tests (T018)
**File**: `tests/unit/plan/test_parser.py`

Tests the `PlanParser` class:
- `test_parse_valid_json_plan` - Parses valid JSON plan structure
- `test_parse_malformed_json` - Handles malformed JSON gracefully
- `test_parse_invalid_plan_structure` - Validates plan structure requirements
- `test_parse_plan_with_multiple_steps` - Handles multi-step plans
- `test_parse_plan_with_duplicate_step_ids` - Rejects duplicate step IDs

### ✅ Integration Tests (T019)
**File**: `tests/integration/test_plan_generation.py`

Tests end-to-end plan generation from natural language:
- `test_generate_plan_from_simple_request` - Simple request → plan generation
- `test_generate_plan_from_complex_request` - Complex multi-step request
- `test_generate_plan_with_valid_structure` - Validates generated plan structure

## Setup Virtual Environment

### Prerequisites
If you get an error about `python3-venv` not being available, install it:
```bash
# On Debian/Ubuntu
sudo apt install python3.12-venv

# Or for your specific Python version
sudo apt install python3-venv
```

### Quick Setup (Automated)
```bash
# Run the setup script
./scripts/setup/setup_venv.sh

# Activate the virtual environment
source venv/bin/activate
```

### Manual Setup
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install package in development mode
pip install -e .
```

## Running Tests

### Run User Story 1 Tests Only
```bash
# Activate virtual environment first
source venv/bin/activate

# Run unit tests for plan parser
pytest tests/unit/plan/test_parser.py -v

# Run integration tests for plan generation
pytest tests/integration/test_plan_generation.py -v

# Run both together
pytest tests/unit/plan/ tests/integration/test_plan_generation.py -v
```

### Run All Tests
```bash
pytest tests/ -v
```

### Run with Coverage
```bash
pytest tests/ --cov=aeon --cov-report=term-missing
```

## Dependencies

### Core Dependencies (requirements.txt)
- `pydantic>=2.0.0` - Data validation and models

### Development Dependencies (requirements-dev.txt)
- `pytest>=7.4.0` - Testing framework
- `pytest-cov>=4.1.0` - Coverage reporting
- `pytest-asyncio>=0.21.0` - Async test support
- `black>=23.0.0` - Code formatter
- `ruff>=0.1.0` - Linter

## Test Fixtures

The tests use `MockLLMAdapter` from `tests/fixtures/mock_llm.py` which:
- Implements the `LLMAdapter` interface
- Returns predefined JSON plan responses
- Tracks all LLM calls for testing
- Does not require actual LLM API access

## Expected Test Results

All User Story 1 tests should pass:
- ✅ Plan parser correctly parses valid JSON plans
- ✅ Plan parser rejects invalid/malformed plans
- ✅ Orchestrator generates plans from natural language
- ✅ Generated plans have valid structure (goal, steps, unique IDs)
- ✅ All steps start with "pending" status

## Troubleshooting

### Import Errors
If you see import errors, make sure:
1. Virtual environment is activated: `source venv/bin/activate`
2. Package is installed: `pip install -e .`
3. You're in the project root directory

### Missing Dependencies
If pytest or other tools are missing:
```bash
pip install -r requirements-dev.txt
```

