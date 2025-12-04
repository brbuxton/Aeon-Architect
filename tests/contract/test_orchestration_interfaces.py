"""Contract tests for orchestration module interfaces."""

import ast
import importlib.util
import inspect
from pathlib import Path
import pytest


def get_module_imports(module_path: Path) -> list[str]:
    """Extract all import statements from a Python module."""
    with open(module_path, "r") as f:
        tree = ast.parse(f.read(), filename=str(module_path))
    
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)
    
    return imports


def get_module_source_file(module_name: str) -> Path:
    """Get the source file path for a module."""
    try:
        spec = importlib.util.find_spec(module_name)
        if spec and spec.origin:
            return Path(spec.origin)
        raise ImportError(f"Cannot find module {module_name}")
    except (ImportError, AttributeError) as e:
        raise ImportError(f"Cannot find module {module_name}: {e}")


class TestOrchestrationModuleImports:
    """Test that orchestration modules have no kernel imports (except state.py)."""

    def test_phases_module_no_kernel_imports(self):
        """Test that phases.py has no kernel imports except state.py."""
        module_path = get_module_source_file("aeon.orchestration.phases")
        imports = get_module_imports(module_path)
        
        # Check for kernel imports (except state.py)
        kernel_imports = [
            imp for imp in imports
            if "aeon.kernel" in imp and "aeon.kernel.state" not in imp
        ]
        
        # Also check for direct imports like "from aeon.kernel import"
        # state.py is allowed via TYPE_CHECKING
        assert len(kernel_imports) == 0, (
            f"phases.py contains kernel imports (except state.py): {kernel_imports}"
        )

    def test_refinement_module_no_kernel_imports(self):
        """Test that refinement.py has no kernel imports."""
        module_path = get_module_source_file("aeon.orchestration.refinement")
        imports = get_module_imports(module_path)
        
        # Check for any kernel imports
        kernel_imports = [imp for imp in imports if "aeon.kernel" in imp]
        
        assert len(kernel_imports) == 0, (
            f"refinement.py contains kernel imports: {kernel_imports}"
        )

    def test_step_prep_module_no_kernel_imports(self):
        """Test that step_prep.py has no kernel imports."""
        module_path = get_module_source_file("aeon.orchestration.step_prep")
        imports = get_module_imports(module_path)
        
        # Check for any kernel imports
        kernel_imports = [imp for imp in imports if "aeon.kernel" in imp]
        
        assert len(kernel_imports) == 0, (
            f"step_prep.py contains kernel imports: {kernel_imports}"
        )

    def test_ttl_module_only_state_import(self):
        """Test that ttl.py only imports from kernel.state."""
        module_path = get_module_source_file("aeon.orchestration.ttl")
        imports = get_module_imports(module_path)
        
        # Check for kernel imports (only state.py allowed)
        kernel_imports = [
            imp for imp in imports
            if "aeon.kernel" in imp and "aeon.kernel.state" not in imp
        ]
        
        # state.py is allowed
        state_imports = [imp for imp in imports if "aeon.kernel.state" in imp]
        
        assert len(kernel_imports) == 0, (
            f"ttl.py contains kernel imports (except state.py): {kernel_imports}"
        )
        # ttl.py should import from state.py for ExecutionPass, ExecutionHistory, etc.
        assert len(state_imports) > 0, (
            "ttl.py should import from aeon.kernel.state for data structures"
        )

    def test_phases_module_state_import_via_type_checking(self):
        """Test that phases.py imports state.py only via TYPE_CHECKING."""
        module_path = get_module_source_file("aeon.orchestration.phases")
        
        with open(module_path, "r") as f:
            source = f.read()
        
        # Check that state imports are within TYPE_CHECKING block
        # This is a simple check - we verify TYPE_CHECKING is used
        assert "TYPE_CHECKING" in source, (
            "phases.py should use TYPE_CHECKING for state imports"
        )
        assert "from aeon.kernel.state import" in source or "from aeon.kernel.state import" in source, (
            "phases.py should import from aeon.kernel.state via TYPE_CHECKING"
        )

    def test_ttl_module_state_import_allowed(self):
        """Test that ttl.py can import from kernel.state (allowed)."""
        module_path = get_module_source_file("aeon.orchestration.ttl")
        
        with open(module_path, "r") as f:
            source = f.read()
        
        # ttl.py should import from kernel.state (this is allowed)
        assert "from aeon.kernel.state import" in source or "from aeon.kernel.state import" in source, (
            "ttl.py should import from aeon.kernel.state for data structures"
        )

