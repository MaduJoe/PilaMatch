---
description: Code review — 5 perspectives with confidence scoring
argument: File path, PR number, or scope description
---

# /review — Code Review

Review the specified code from 5 perspectives. Only report issues with HIGH or MEDIUM confidence.

**Review target**: $ARGUMENTS

---

## Review Process

1. Read all files in scope
2. For each file, evaluate from these 5 perspectives:

### Perspective 1: Correctness
- Logic errors, off-by-one, null handling
- State machine violations
- Async/await correctness

### Perspective 2: Security
- Input validation gaps (OWASP Top 10)
- Auth/authz bypasses
- SQL injection, XSS risks
- Hardcoded secrets
- For deep security review: delegate to security-reviewer agent

### Perspective 3: Pattern Compliance
- GUID type usage (not UUID)
- String(20) for enums (not SQLEnum)
- Service layer pattern (endpoint → service → DB)
- Async/await for all I/O
- Type hints on all functions

### Perspective 4: Test Coverage
- Are there tests for the changed code?
- Do tests cover happy path + edge case + error case?
- Are mocks used appropriately?

### Perspective 5: Unnecessary Changes
- Over-engineering or premature abstractions
- Unrelated refactoring mixed with feature work
- Added complexity without justification

## Output Format

For each issue found:
```
[HIGH|MEDIUM] file:line — [perspective] description
  → Suggestion: [how to fix]
```

Summary:
```
📊 Review: [N files reviewed]
🔴 HIGH: [count] issues
🟡 MEDIUM: [count] issues
✅ No issues: [count] files
```

Skip LOW confidence issues — they add noise without value.
