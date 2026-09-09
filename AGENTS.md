# AGENTS.md — Development Guide for OpenJyotish

## Repository Overview

| Repo | URL | Visibility | Purpose |
|------|-----|-----------|---------|
| **OpenJyotish** | `github.com/velteyn/OpenJyotish` | Public | Official release, public-facing development |

## Workflow

1. **Develop & test** locally on a clean environment.
2. **Consolidate** — run full test suite, fix all issues.
3. **Push to GitHub** — follow the feature branch and PR pipeline below:

### Feature Branch + PR + Merge Pipeline

Every feature/fix follows this exact sequence. **Never commit directly to `main`.**

```bash
# 1. Create feature branch from main
git checkout main
git checkout -b feature/<name>

# 2. Commit (only intentional source/test changes)
git add src/ tests/
# NEVER commit: data/jhora.db (test churn), ephemeral test files, or local binaries

# 3. Push branch to origin
git push origin feature/<name>

# 4. Open PR against main
gh pr create --repo velteyn/OpenJyotish \
  --base main --head feature/<name> \
  --title "..." --body "..."

# 5. Verify PR diff is clean
gh pr view <N> --repo velteyn/OpenJyotish --json files
# Confirm: only intended files, no data/jhora.db churn

# 6. Merge (squash or merge — default merge)
gh pr merge <N> --repo velteyn/OpenJyotish --merge --delete-branch

# 7. Sync local main
git checkout main
git pull origin main

# 8. Cleanup local branch
git branch -d feature/<name>
