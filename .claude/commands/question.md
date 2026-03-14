---
description: Ask questions about the project, codebase, or general topics
argument: Your question
---

# /question — Project & General Q&A

Answer the user's question. This is NOT a code modification request.

**Question**: $ARGUMENTS

---

## Guidelines

1. **Project questions**: Use Read/Grep/Glob to find relevant code, then explain
2. **Architecture questions**: Reference CLAUDE.md patterns and existing implementations
3. **General questions**: Answer directly from knowledge
4. **Comparison questions**: Provide structured comparison (table or list)

## Response Style

- Answer concisely and directly
- Include file paths and line numbers when referencing code
- Use code snippets only when they clarify the answer
- If the question is ambiguous, ask for clarification before researching

## Do NOT

- Modify any files
- Create new files
- Run tests or builds
- Suggest changes unless explicitly asked
