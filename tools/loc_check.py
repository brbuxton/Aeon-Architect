#!/usr/bin/env python3
"""Kernel LOC verification tool.

Enforces Constitution SC-008 requiring the kernel module to remain <800 LOC.
Scans kernel/ directory, sums Python source lines excluding blanks and comments,
and fails if >800 LOC.
"""

import ast
import sys
from pathlib import Path


def count_loc(file_path: Path) -> int:
    """
    Count lines of code in a Python file, excluding blanks and comments.

    Args:
        file_path: Path to Python file

    Returns:
        Number of non-blank, non-comment lines
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Error reading {file_path}: {e}", file=sys.stderr)
        return 0

    loc = 0
    for line in lines:
        stripped = line.strip()
        # Skip blank lines
        if not stripped:
            continue
        # Skip comment-only lines
        if stripped.startswith('#'):
            continue
        # Skip docstrings (simple check - lines starting with """ or ''')
        if stripped.startswith('"""') or stripped.startswith("'''"):
            continue
        loc += 1

    return loc


def check_kernel_loc(kernel_dir: Path, max_loc: int = 800) -> tuple[bool, dict[str, int], int]:
    """
    Check kernel LOC against maximum allowed.

    Args:
        kernel_dir: Path to kernel directory
        max_loc: Maximum allowed LOC (default 800)

    Returns:
        Tuple of (passes, per_file_locs, total_loc)
    """
    if not kernel_dir.exists():
        print(f"Error: Kernel directory not found: {kernel_dir}", file=sys.stderr)
        return False, {}, 0

    per_file_locs = {}
    total_loc = 0

    # Find all Python files in kernel directory
    for py_file in sorted(kernel_dir.glob("*.py")):
        loc = count_loc(py_file)
        per_file_locs[py_file.name] = loc
        total_loc += loc

    passes = total_loc <= max_loc
    return passes, per_file_locs, total_loc


def main() -> int:
    """Main entry point for LOC check."""
    # Get kernel directory (assume we're in project root)
    project_root = Path(__file__).parent.parent
    kernel_dir = project_root / "aeon" / "kernel"

    max_loc = 800
    passes, per_file_locs, total_loc = check_kernel_loc(kernel_dir, max_loc)

    # Print per-file LOC
    print("Kernel LOC per file:")
    for filename, loc in per_file_locs.items():
        print(f"  {filename}: {loc} LOC")

    print(f"\nTotal kernel LOC: {total_loc}")
    print(f"Maximum allowed: {max_loc}")

    if passes:
        print(f"✓ PASS: Kernel LOC ({total_loc}) is within limit ({max_loc})")
        return 0
    else:
        print(f"✗ FAIL: Kernel LOC ({total_loc}) exceeds limit ({max_loc})")
        print("\nConstitutional Requirement SC-008: Kernel must remain <800 LOC")
        return 1


if __name__ == "__main__":
    sys.exit(main())

