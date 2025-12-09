#!/usr/bin/env python3
"""
Fix the logger initialization in the notebook.
This ensures the notebook file has the correct code.
"""

import json
from pathlib import Path

NOTEBOOK_PATH = Path(__file__).parent / "test_sprint_results.ipynb"

def fix_notebook():
    """Fix the JSONLLogger initialization in the notebook."""
    print(f"Reading notebook: {NOTEBOOK_PATH}")
    
    with open(NOTEBOOK_PATH, 'r') as f:
        nb = json.load(f)
    
    fixed = False
    
    # Find and fix all code cells
    for i, cell in enumerate(nb['cells']):
        if cell['cell_type'] == 'code':
            source = ''.join(cell['source'])
            
            # Check if this cell has the old log_file parameter
            if 'JSONLLogger(log_file=' in source:
                print(f"\nFound problematic code in cell {i}")
                print("Fixing...")
                
                # Replace the old code
                new_source = []
                for line in cell['source']:
                    if 'logger = JSONLLogger(log_file=LOG_FILE)' in line:
                        # Replace with correct code
                        new_source.append('    # JSONLLogger expects file_path as Optional[Path], not log_file\n')
                        new_source.append('    log_path = Path(LOG_FILE) if LOG_FILE else None\n')
                        new_source.append('    logger = JSONLLogger(file_path=log_path)\n')
                        fixed = True
                    else:
                        new_source.append(line)
                
                cell['source'] = new_source
                print("✓ Fixed!")
    
    # Also ensure Path is imported
    for i, cell in enumerate(nb['cells']):
        if cell['cell_type'] == 'code':
            source = ''.join(cell['source'])
            if 'from datetime import datetime' in source and 'from pathlib import Path' not in source:
                print(f"\nAdding Path import to cell {i}")
                new_source = []
                for line in cell['source']:
                    new_source.append(line)
                    if 'from datetime import datetime' in line:
                        new_source.append('from pathlib import Path\n')
                cell['source'] = new_source
                fixed = True
                print("✓ Added Path import!")
    
    if fixed:
        print(f"\nSaving fixed notebook to {NOTEBOOK_PATH}")
        with open(NOTEBOOK_PATH, 'w') as f:
            json.dump(nb, f, indent=1)
        print("✓ Notebook saved!")
        print("\nPlease:")
        print("  1. Close and reopen the notebook in VS Code/Jupyter")
        print("  2. Restart the kernel")
        print("  3. Re-run the cells from the beginning")
    else:
        print("\n✓ Notebook already has correct code!")
        print("If you're still seeing errors, try:")
        print("  1. Close and reopen the notebook")
        print("  2. Restart the kernel")
        print("  3. Make sure you're running the correct cell")

if __name__ == '__main__':
    fix_notebook()
