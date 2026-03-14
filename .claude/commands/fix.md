---
description: Bug fix workflow — minimal, focused fixes
argument: Bug description or error message
---

# /fix — Bug Fix Workflow

Fix ONE bug with MINIMAL changes. Do NOT refactor surrounding code.

**Bug report**: $ARGUMENTS

---

## Step 1: UNDERSTAND

- Read the error message or bug description carefully
- Identify the affected file(s) and function(s)
- Read those files to understand current behavior

## Step 2: REPRODUCE (if possible)

- Run the failing test or reproduce the error
- Confirm the bug exists before attempting a fix

```bash
cd backend && SECRET_KEY=test uv run pytest tests/test_{relevant}.py -v
```

## Step 3: DIAGNOSE

- Identify the ROOT CAUSE in ONE sentence
- Trace the execution path to find where it breaks
- Do NOT guess — read the code

Output: `🔍 Root cause: [one sentence]`

## Step 4: FIX

- Make the MINIMUM change needed to fix the bug
- Do NOT:
  - Refactor unrelated code
  - Add "while we're here" improvements
  - Change function signatures unnecessarily
  - Add extra error handling beyond what's needed

## Step 5: VERIFY

- Run the relevant test(s)
- Confirm the fix works
- Check for regressions (run related tests too)

```bash
cd backend && SECRET_KEY=test uv run pytest tests/test_{relevant}.py -v
```

Output format:
```
🐛 Bug: [description]
🔍 Root cause: [one sentence]
✅ Fix: [what was changed]
🧪 Tests: [pass/fail]
```
