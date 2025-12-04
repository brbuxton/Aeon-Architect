"""Unit tests for LOC measurement functionality (T012).

Tests the LOC counting logic to ensure it correctly counts lines of code
while excluding blanks, comments, and docstrings.
"""

import tempfile
from pathlib import Path

import pytest

# Import LOC counting function from tools
import sys
from pathlib import Path as PathLib

# Add tools directory to path to import loc_check
tools_dir = Path(__file__).parent.parent.parent.parent / "tools"
sys.path.insert(0, str(tools_dir))

from loc_check import count_loc


class TestLOCMeasurement:
    """Test LOC counting functionality."""

    def test_count_loc_excludes_blank_lines(self):
        """Test that blank lines are excluded from LOC count."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""def hello():
    print("world")
    
    return True
    
""")
            temp_path = Path(f.name)

        try:
            loc = count_loc(temp_path)
            # Should count: def line, print line, return line = 3 LOC
            assert loc == 3
        finally:
            temp_path.unlink()

    def test_count_loc_excludes_comment_lines(self):
        """Test that comment-only lines are excluded from LOC count."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""# This is a comment
def hello():
    # Another comment
    print("world")
    # Yet another comment
    return True
""")
            temp_path = Path(f.name)

        try:
            loc = count_loc(temp_path)
            # Should count: def line, print line, return line = 3 LOC
            assert loc == 3
        finally:
            temp_path.unlink()

    def test_count_loc_excludes_docstrings(self):
        """Test that docstring-only lines are excluded from LOC count."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('''"""This is a docstring."""
def hello():
    """Function docstring."""
    print("world")
    return True
''')
            temp_path = Path(f.name)

        try:
            loc = count_loc(temp_path)
            # Should count: def line, print line, return line = 3 LOC
            assert loc == 3
        finally:
            temp_path.unlink()

    def test_count_loc_includes_code_with_comments(self):
        """Test that lines with code and comments are counted."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""def hello():  # inline comment
    print("world")  # another inline comment
    return True
""")
            temp_path = Path(f.name)

        try:
            loc = count_loc(temp_path)
            # Should count: def line, print line, return line = 3 LOC
            assert loc == 3
        finally:
            temp_path.unlink()

    def test_count_loc_handles_empty_file(self):
        """Test that empty file returns 0 LOC."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("")
            temp_path = Path(f.name)

        try:
            loc = count_loc(temp_path)
            assert loc == 0
        finally:
            temp_path.unlink()

    def test_count_loc_handles_file_with_only_comments(self):
        """Test that file with only comments returns 0 LOC."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""# Comment 1
# Comment 2
# Comment 3
""")
            temp_path = Path(f.name)

        try:
            loc = count_loc(temp_path)
            assert loc == 0
        finally:
            temp_path.unlink()

    def test_count_loc_counts_actual_code(self):
        """Test that actual code lines are counted correctly."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""import os
from pathlib import Path

class TestClass:
    def method1(self):
        return "value1"
    
    def method2(self):
        return "value2"

def standalone_function():
    x = 1
    y = 2
    return x + y
""")
            temp_path = Path(f.name)

        try:
            loc = count_loc(temp_path)
            # Should count: import, from, class, def method1, return, def method2, return,
            # def standalone_function, x=, y=, return = 11 LOC
            assert loc == 11
        finally:
            temp_path.unlink()

    def test_count_loc_handles_nonexistent_file(self):
        """Test that nonexistent file returns 0 LOC."""
        nonexistent_path = Path("/nonexistent/path/to/file.py")
        loc = count_loc(nonexistent_path)
        assert loc == 0

