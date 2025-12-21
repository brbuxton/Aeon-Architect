# Jupyter Notebook Guide for Beginners

This guide will teach you how to use Jupyter notebooks, specifically for running the `test_sprint_results.ipynb` notebook.

## What is Jupyter?

Jupyter is an interactive computing environment that lets you write and run code in "cells" that can contain code, text, or markdown. It's perfect for:
- Testing code interactively
- Documenting your work
- Sharing results with others
- Data analysis and visualization

## Installation

### Option 1: Install Jupyter in your existing Python environment

```bash
# Make sure you're in your project directory
cd /home/brian/projects/Aeon-Architect

# Install Jupyter
pip install jupyter

# Or if you prefer JupyterLab (more modern interface)
pip install jupyterlab
```

### Option 2: Use VS Code (if you have it)

VS Code has built-in Jupyter support! Just:
1. Install the "Jupyter" extension in VS Code
2. Open the `.ipynb` file
3. VS Code will recognize it and show a "Run Cell" button

## Starting Jupyter

### Method 1: Jupyter Notebook (Classic)

```bash
# Navigate to your project directory
cd /home/brian/projects/Aeon-Architect

# Start Jupyter
jupyter notebook

# This will:
# - Start a local server
# - Open your web browser automatically
# - Show a file browser where you can click on test_sprint_results.ipynb
```

### Method 2: JupyterLab (Recommended)

```bash
cd /home/brian/projects/Aeon-Architect
jupyter lab

# Similar to above, but with a more modern interface
```

### Method 3: VS Code

1. Open VS Code
2. File → Open Folder → Select `/home/brian/projects/Aeon-Architect`
3. Click on `test_sprint_results.ipynb` in the file explorer
4. VS Code will open it as a notebook automatically

## Understanding the Notebook Interface

### Cell Types

1. **Code Cells** (gray background): Contain Python code
2. **Markdown Cells** (white background): Contain formatted text/instructions

### Cell States

- **Empty brackets `[ ]`**: Cell hasn't been run yet
- **Number in brackets `[1]`**: Cell has been executed (number shows execution order)
- **Asterisk `[*]`**: Cell is currently running

### Toolbar Buttons

- **Run**: Execute the current cell (or press `Shift+Enter`)
- **Stop**: Interrupt execution (useful if code is stuck)
- **Restart**: Restart the kernel (clears all variables)
- **Save**: Save the notebook

## How to Use Your Test Notebook

### Step 1: Open the Notebook

```bash
# Start Jupyter
jupyter notebook
# or
jupyter lab
```

Then click on `test_sprint_results.ipynb` in the file browser.

### Step 2: Run Cells Sequentially

**Important**: Run cells from top to bottom, in order!

1. **First Cell - Setup and Imports**
   - Click on the cell
   - Press `Shift+Enter` (or click "Run" button)
   - Wait for `[1]` to appear (means it finished)
   - This imports all necessary libraries

2. **Second Cell - Configuration**
   - Run it (`Shift+Enter`)
   - This sets up your LLM endpoint and TTL settings
   - You can modify the values here if needed

3. **Third Cell - Initialize Components**
   - Run it
   - This creates all the Aeon components (LLM adapter, memory, etc.)
   - You should see checkmarks (✓) for each component

4. **Fourth Cell - Create Orchestrator**
   - Run it
   - Creates the main orchestrator object

5. **Fifth Cell - Define User Prompt**
   - **THIS IS WHERE YOU ENTER YOUR TEST PROMPT**
   - Modify the `user_prompt` variable:
     ```python
     user_prompt = "Your test prompt here"
     ```
   - Run the cell

6. **Sixth Cell - Execute End-to-End Test**
   - This is the main execution cell
   - **This will take the longest** (could be minutes depending on your LLM)
   - You'll see progress output as it runs
   - Wait for it to complete before moving on

7. **Remaining Cells - View Results**
   - Run each cell to see different views of the results:
     - Execution Summary
     - Detailed Execution Log
     - Full Result JSON
     - Phase E Details
     - Prompt Registry Audit

### Step 3: Understanding the Output

After running the execution cell, you'll see:

1. **Progress Messages**: Shows which phase is running
2. **Execution Summary**: Status, execution ID, number of passes
3. **Final Answer**: The Phase E synthesis output (this is what you're testing!)
4. **Detailed Logs**: Step-by-step execution history
5. **JSON Output**: Full result for audit purposes

## Common Operations

### Running a Single Cell

- Click on the cell
- Press `Shift+Enter` (runs and moves to next cell)
- Or press `Ctrl+Enter` (runs but stays on same cell)

### Running All Cells

- Menu: `Cell` → `Run All`
- Or: `Kernel` → `Restart & Run All` (clears variables first)

### Stopping Execution

- If code is taking too long or stuck:
  - Click the "Stop" button (square icon)
  - Or press `Ctrl+C` in the terminal where Jupyter is running

### Restarting the Kernel

If things get confused or you want to start fresh:
- Menu: `Kernel` → `Restart`
- Or: `Kernel` → `Restart & Clear Output`

### Editing Code

- Click on a code cell to edit it
- Make your changes
- Run the cell again with `Shift+Enter`

### Adding a New Cell

- Click the `+` button in the toolbar
- Or press `A` (insert above) or `B` (insert below) when in command mode

## Keyboard Shortcuts

### Command Mode (press `Esc` first)
- `Enter`: Enter edit mode
- `A`: Insert cell above
- `B`: Insert cell below
- `D, D`: Delete cell (press D twice)
- `Shift+Enter`: Run cell and move to next
- `Ctrl+Enter`: Run cell and stay

### Edit Mode (when typing in a cell)
- `Shift+Enter`: Run cell
- `Ctrl+Enter`: Run cell and stay
- `Esc`: Exit to command mode

## Troubleshooting

### "Module not found" Error

If you see import errors:
1. Make sure you're in the right directory
2. Check that the project is installed: `pip install -e .`
3. Verify the path in the first cell is correct

### Kernel Died / Restarting

If the kernel keeps dying:
1. Check your llama-cpp server is running on port 8000
2. Verify the API URL is correct
3. Check system resources (memory, CPU)

### Cells Not Running

- Make sure you've selected the cell (click on it)
- Check that the kernel is running (top right should show "Python 3")
- Try restarting the kernel: `Kernel` → `Restart`

### Output is Messy

- Clear all outputs: `Cell` → `All Output` → `Clear`
- Then run cells again from the top

## Workflow for Testing

Here's the recommended workflow:

1. **Start Jupyter**
   ```bash
   cd /home/brian/projects/Aeon-Architect
   jupyter lab
   ```

2. **Open the notebook**
   - Click on `test_sprint_results.ipynb`

3. **Run setup cells** (cells 1-4)
   - Run them one by one with `Shift+Enter`
   - Wait for each to complete

4. **Set your test prompt** (cell 5)
   - Edit the `user_prompt` variable
   - Run the cell

5. **Execute the test** (cell 6)
   - This is the main execution
   - **Be patient** - this can take several minutes
   - Watch for progress messages

6. **Review results** (cells 7-12)
   - Run each cell to see different views
   - The "Final Answer" section is most important for Phase E testing

7. **Save your work**
   - File → Save (or `Ctrl+S`)
   - The notebook saves automatically, but good to save manually too

## Tips

1. **Run cells in order**: The notebook is designed to run top-to-bottom
2. **Don't skip cells**: Each cell depends on previous ones
3. **Read the markdown cells**: They contain important instructions
4. **Check the output**: Look for error messages or warnings
5. **Save frequently**: Especially after getting good results
6. **Take notes**: Add markdown cells to document your findings

## Example: Your First Run

Let's walk through a complete example:

```bash
# 1. Start Jupyter
cd /home/brian/projects/Aeon-Architect
jupyter lab
```

In the browser:
1. Click `test_sprint_results.ipynb`
2. Click on the first code cell (the one with imports)
3. Press `Shift+Enter` - wait for `[1]` to appear
4. Press `Shift+Enter` again for the next cell - wait for `[2]`
5. Continue until you reach "Define User Prompt"
6. Change the prompt to something simple like: `"Explain what a web server does"`
7. Run that cell
8. Run the "Execute End-to-End Test" cell - **this will take time!**
9. Watch the output - you'll see progress messages
10. When it finishes, run the remaining cells to see results

## Getting Help

- **Jupyter Documentation**: https://jupyter-notebook.readthedocs.io/
- **VS Code Jupyter Guide**: If using VS Code, check their Jupyter extension docs
- **Check the output**: Error messages usually tell you what's wrong

## Next Steps

Once you're comfortable:
- Try different prompts
- Modify the configuration (TTL, API URL)
- Add your own cells to experiment
- Export results to files
- Share the notebook with others

Good luck with your testing! 🚀
