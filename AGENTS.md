# Agent Instructions

## GUI Design
- The GUI must always be **harmonic, proportional, and stylish** — matching the existing dark theme (PyQt6, Fusion style)
- Consistent spacing: use 10px grid, consistent margins, proportional splitter ratios
- Colors from the established palette; no突兀 colors

## Documentation
- Keep CONTEXT.md up-to-date — add new features, update "Done" section, remove stale "In Progress" entries
- Update PLAN.md if roadmap changes

## Commit Discipline
- After any code change, run `python3 -m pytest tests/ -q` and confirm 0 failures
- Stage all changes, commit with a descriptive message, and push to `origin/main`
- Never leave failing tests in the committed code
