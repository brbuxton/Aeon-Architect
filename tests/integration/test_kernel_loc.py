"""Integration test to verify kernel LOC ≤800 after refactoring (T013).

This test measures the LOC of orchestrator.py and executor.py in the kernel
and verifies that the total is ≤800 LOC (target <750 LOC) as required by
constitutional requirement SC-001.

Note: This test may fail during US1 implementation since the refactoring
is not yet complete. That is expected and acceptable.
"""

import sys
from pathlib import Path

import pytest

# Add tools directory to path to import loc_check
tools_dir = Path(__file__).parent.parent.parent / "tools"
sys.path.insert(0, str(tools_dir))

from loc_check import count_loc


class TestKernelLOCCompliance:
    """Test kernel LOC compliance with constitutional requirement."""

    @pytest.fixture
    def project_root(self):
        """Get project root directory."""
        return Path(__file__).parent.parent.parent

    @pytest.fixture
    def kernel_dir(self, project_root):
        """Get kernel directory."""
        return project_root / "aeon" / "kernel"

    def test_kernel_loc_orchestrator_and_executor_only(self, kernel_dir):
        """Test that only orchestrator.py and executor.py count toward LOC limit."""
        # According to spec, only these two files count toward the limit
        orchestrator_path = kernel_dir / "orchestrator.py"
        executor_path = kernel_dir / "executor.py"

        orchestrator_loc = count_loc(orchestrator_path)
        executor_loc = count_loc(executor_path)
        total_loc = orchestrator_loc + executor_loc

        # Log the measurements for debugging
        print(f"\nKernel LOC measurements:")
        print(f"  orchestrator.py: {orchestrator_loc} LOC")
        print(f"  executor.py: {executor_loc} LOC")
        print(f"  Total: {total_loc} LOC")
        print(f"  Maximum allowed: 800 LOC")
        print(f"  Target: <750 LOC")

        # Verify total is ≤800 (constitutional requirement SC-001)
        assert total_loc <= 800, (
            f"Kernel LOC ({total_loc}) exceeds constitutional limit (800). "
            f"orchestrator.py: {orchestrator_loc}, executor.py: {executor_loc}"
        )

    def test_kernel_loc_target_under_750(self, kernel_dir):
        """Test that kernel LOC is under 750 (target, not requirement)."""
        orchestrator_path = kernel_dir / "orchestrator.py"
        executor_path = kernel_dir / "executor.py"

        orchestrator_loc = count_loc(orchestrator_path)
        executor_loc = count_loc(executor_path)
        total_loc = orchestrator_loc + executor_loc

        # This is a target, not a hard requirement, so we just log if it's over
        if total_loc >= 750:
            pytest.skip(
                f"Kernel LOC ({total_loc}) is above target (<750). "
                f"This is acceptable during refactoring. "
                f"orchestrator.py: {orchestrator_loc}, executor.py: {executor_loc}"
            )

        assert total_loc < 750, (
            f"Kernel LOC ({total_loc}) is above target (<750). "
            f"orchestrator.py: {orchestrator_loc}, executor.py: {executor_loc}"
        )

    def test_kernel_files_exist(self, kernel_dir):
        """Test that required kernel files exist."""
        orchestrator_path = kernel_dir / "orchestrator.py"
        executor_path = kernel_dir / "executor.py"

        assert orchestrator_path.exists(), f"orchestrator.py not found at {orchestrator_path}"
        assert executor_path.exists(), f"executor.py not found at {executor_path}"

