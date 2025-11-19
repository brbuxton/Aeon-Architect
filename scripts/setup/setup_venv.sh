#!/bin/bash
# Setup script for Aeon Core virtual environment

set -e

echo "Setting up virtual environment for Aeon Core..."

# Check if venv module is available
if ! python3 -m venv --help > /dev/null 2>&1; then
    echo "❌ Error: python3-venv is not installed."
    echo ""
    echo "On Debian/Ubuntu systems, install it with:"
    echo "  sudo apt install python3.12-venv"
    echo ""
    echo "Or use python3.12 directly if available:"
    echo "  python3.12 -m venv venv"
    exit 1
fi

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install core dependencies
echo "Installing core dependencies..."
pip install -r requirements.txt

# Install development dependencies
echo "Installing development dependencies..."
pip install -r requirements-dev.txt

# Install package in development mode
echo "Installing Aeon Core in development mode..."
pip install -e .

echo ""
echo "✅ Virtual environment setup complete!"
echo ""
echo "To activate the virtual environment, run:"
echo "  source venv/bin/activate"
echo ""
echo "To run tests, use:"
echo "  pytest tests/unit/plan/ tests/integration/test_plan_generation.py -v"
echo "  # Or run all tests:"
echo "  pytest tests/ -v"
echo ""
echo "To deactivate, run:"
echo "  deactivate"

