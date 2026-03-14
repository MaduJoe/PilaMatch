---
description: Feature development workflow — 5-step guided process
argument: Feature description
---

# /dev — Feature Development Workflow

You MUST follow these 5 steps IN ORDER. Do NOT skip steps. Wait for user approval at Step 2.

**Feature request**: $ARGUMENTS

---

## Step 1: EXPLORE (read-only)

- Read all related files using Read/Grep/Glob tools
- Identify existing patterns and conventions
- List ALL files that need modification or creation
- Do NOT modify anything yet

Output format:
```
📂 Files to MODIFY: [list with reasons]
📄 Files to CREATE: [list with justification — minimize new files]
🔍 Patterns found: [key conventions to follow]
⚠️ Risks: [potential issues]
```

## Step 2: PLAN (await approval)

- Define the exact change sequence (order matters)
- Specify which agent to delegate to (if applicable):
  - backend-api: API endpoints, services
  - database: schema changes, migrations
  - frontend-ui: React/Next.js components
  - test-qa: test writing
- Estimate scope: small (1-2 files) / medium (3-5) / large (6+)

**⏸️ STOP HERE. Present the plan and wait for user approval before proceeding.**

## Step 3: IMPLEMENT

- Follow the approved plan file-by-file
- Do NOT create files not listed in Step 1
- Do NOT refactor unrelated code
- Delegate to domain agents per CLAUDE.md rules when applicable

## Step 4: TEST

- Run relevant tests per CLAUDE.md test matrix
- If tests fail: fix and re-run (max 3 rounds)
- If 3 rounds fail: report to user with diagnosis

```bash
# Backend services
cd backend && SECRET_KEY=test uv run pytest tests/test_{service}.py -v

# Full suite
cd backend && SECRET_KEY=test uv run pytest --cov=app

# Frontend
# Verify in browser DevTools mobile view
```

## Step 5: SUMMARY

Output format:
```
✅ DONE: [feature name]
📝 Modified: [file list]
📄 Created: [file list]
🧪 Tests: [pass/fail count]
📌 Next steps: [if any]
```
