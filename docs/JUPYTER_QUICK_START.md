# Jupyter Quick Start - Cheat Sheet

## Start Jupyter

```bash
cd /home/brian/projects/Aeon-Architect
jupyter lab
# or
jupyter notebook
```

Then click on `test_sprint_results.ipynb`

## Essential Commands

| Action | Keyboard Shortcut | Button |
|-------|------------------|--------|
| Run cell | `Shift+Enter` | ▶️ Run |
| Run & stay | `Ctrl+Enter` | - |
| Stop execution | `Ctrl+C` | ⏹️ Stop |
| Restart kernel | - | 🔄 Restart |
| Save | `Ctrl+S` | 💾 Save |

## Running Your Test Notebook

1. **Run cells 1-4**: Setup (imports, config, components)
2. **Edit cell 5**: Change `user_prompt = "your test here"`
3. **Run cell 6**: Execute test (takes time!)
4. **Run cells 7-12**: View results

## Cell States

- `[ ]` = Not run yet
- `[1]` = Executed (number = order)
- `[*]` = Currently running

## If Something Goes Wrong

1. **Kernel died?** → `Kernel` → `Restart`
2. **Import error?** → Check you're in right directory
3. **Stuck running?** → Click ⏹️ Stop button
4. **Want fresh start?** → `Kernel` → `Restart & Clear Output`

## Quick Test Workflow

```
1. Start Jupyter → jupyter lab
2. Open notebook → Click test_sprint_results.ipynb
3. Run cells 1-4 → Shift+Enter for each
4. Edit prompt → Change user_prompt in cell 5
5. Run execution → Shift+Enter on cell 6 (wait!)
6. View results → Run remaining cells
```

## Pro Tips

- ✅ Always run cells top-to-bottom
- ✅ Wait for each cell to finish before next
- ✅ Read the markdown cells (instructions!)
- ✅ Check for error messages in red
- ✅ The Final Answer section shows Phase E output
