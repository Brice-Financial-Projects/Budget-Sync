# BudgetSync – Refactoring Notes for `src/` Layout

## Background
The `budget_sync` project originally did **not** use an `src/` layout. As the codebase grew, unresolved references and module import issues made it clear that restructuring into a `src/`-based layout was necessary for long-term maintainability and production readiness.

## Issues Encountered

### 1. PyCharm Project Root
- After moving code into `src/`, PyCharm continued to treat the old structure as the project root.
- This caused unresolved reference warnings across the project.
- **Resolution:** Explicitly marked `src/` as the **Sources Root** in PyCharm.

### 2. `pyproject.toml` Adjustments
- The default configuration did not account for the new `src/` layout.
- Import paths broke when running scripts outside of PyCharm (e.g., `flask run`).
- **Resolution:** Added `pyproject.toml` configuration to align with the new `src/` directory structure.

### 3. Entry Point Script (`run.py`)
- The old `run.py` referenced modules as if they were in the project root.
- After restructuring, all imports inside `run.py` broke with `ModuleNotFoundError`.
- **Resolution:** Updated `run.py` to reference packages correctly relative to `src/`.

### 4. Branch Cleanup
- Multiple failed attempts to restructure left stale branches with broken imports and inconsistent configs.
- **Resolution:** Deleted the old branches and restarted with a clean, consistent `src/` layout from scratch.

## Current Status
- ✅ `src/` is now the root directory.
- ✅ PyCharm recognizes `src/` as the sources root.
- ✅ `pyproject.toml` has been updated for `src/`.
- ✅ `run.py` imports resolved.
- 🔄 Continuing to fix remaining runtime and configuration errors as they appear.

## Lessons Learned
- Always define `src/` as the project root early in development to avoid large refactors later.
- IDEs (like PyCharm) need explicit configuration when shifting project roots.
- Cleaning up branches is sometimes faster than trying to salvage broken refactor attempts.
- Documenting each fix helps avoid repeating the same troubleshooting steps.

---
