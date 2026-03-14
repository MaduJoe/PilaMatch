---
description: Test loop — run tests, fix failures, repeat (max 3 rounds)
argument: Test path or scope (e.g., tests/test_auth.py, --cov=app)
---

# /test-and-fix — Test Loop

Run tests, analyze failures, fix code (NOT tests unless tests are wrong). Max 3 rounds.

**Test target**: $ARGUMENTS

---

## Rules

- Do NOT modify passing tests
- Do NOT refactor while fixing
- Fix the CODE, not the test (unless the test is genuinely wrong)
- If a test is wrong: explain WHY before modifying it

## Round N (repeat up to 3 times)

### RUN
```bash
cd backend && SECRET_KEY=test uv run pytest $ARGUMENTS -v
```

### ANALYZE (if failures)
For each failure:
- Read the error message and traceback
- Identify whether the bug is in CODE or TEST
- Determine the minimal fix

### FIX
- Apply minimal fixes
- Re-run immediately

## REPORT (after all rounds)

Output format:
```
🧪 Test Results: [scope]
  Round 1: [X passed, Y failed]
  Round 2: [X passed, Y failed] (if needed)
  Round 3: [X passed, Y failed] (if needed)

✅ All passing | ❌ [N] still failing

Fixed:
- [file:line] — [what was wrong and what was changed]

Still failing (if any):
- [test name] — [diagnosis, why 3 rounds weren't enough]
```
