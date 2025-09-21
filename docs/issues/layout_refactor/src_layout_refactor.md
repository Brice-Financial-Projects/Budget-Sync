# BudgetSync – Refactoring Notes for `src/` Layout

## Background
The `budget_sync` project originally did **not** use an `src/` layout. As the codebase grew, unresolved references and module import issues made it clear that restructuring into a `src/`-based layout was necessary for long-term maintainability and production readiness.

## Issues Encountered

--------------------------------------------------------
Date: September 6, 2025
--------------------------------------------------------

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

--------------------------------------------------------
Date: September 21, 2025
--------------------------------------------------------

### 5. Flask Template Path Issues
- After the `src/` restructuring, Flask couldn't find templates due to incorrect relative paths.
- Routes were using outdated template paths like `../templates/home.html` and blueprint-specific `template_folder` parameters.
- Templates were trying to extend `../base.html` which failed with `TemplateNotFound` errors.
- **Resolution:** 
  - Simplified all route template paths (e.g., `../templates/home.html` → `home.html`)
  - Removed unnecessary `template_folder` parameters from blueprints
  - Updated all template inheritance from `{% extends '../base.html' %}` to `{% extends 'base.html' %}`

### 6. Circular Import Issues in Helpers
- The `budget_helpers.py` module had circular imports after the refactoring, causing table redefinition errors.
- Import statements were pulling in conflicting database model definitions.
- **Resolution:** Refactored import statements in helper modules to avoid circular dependencies and use proper relative imports.

### 7. Authentication Route Template References  
- Auth routes were still using legacy template paths like `'auth/../templates/auth/login.html'`.
- This caused `TemplateNotFound` errors when users tried to access login/registration pages.
- **Resolution:** Updated all auth route template references to use simplified paths (`'auth/login.html'`, `'auth/register.html'`).

## Current Status
- `src/` is now the root directory.
- PyCharm recognizes `src/` as the sources root.
- `pyproject.toml` has been updated for `src/`.
- `run.py` imports resolved.
- Flask template discovery working correctly.
- All route template paths simplified and functional.
- Template inheritance paths corrected across all HTML files.
- Circular import issues in helpers resolved.
- Authentication routes fully operational.
- Application successfully starts and serves pages without template errors.

## Lessons Learned
- Always define `src/` as the project root early in development to avoid large refactors later.
- IDEs (like PyCharm) need explicit configuration when shifting project roots.
- Cleaning up branches is sometimes faster than trying to salvage broken refactor attempts.
- Documenting each fix helps avoid repeating the same troubleshooting steps.
- **Flask template paths should be simplified after restructuring** - avoid relative paths in both routes and template inheritance.
- **Blueprint template_folder parameters can cause confusion** - let Flask use default template discovery instead.
- **Circular imports become more apparent with src/ layouts** - proper import organization is crucial.
- **Systematic approach to fixing template paths** - update routes first, then template inheritance, then test thoroughly.

---
