#!/usr/bin/env bash
# prompt-guard.sh — UserPromptSubmit hook
# Blocks vague prompts that lack action verbs or target nouns.
# Exit 0 = allow, Exit 2 = block (reason on stderr)

set -uo pipefail

# Parse JSON from stdin using python3 (jq not available)
PROMPT=$(python3 -c "import json,sys; print(json.loads(sys.stdin.read()).get('prompt',''))" 2>/dev/null || echo "")

# If parsing fails or prompt is empty, pass through
if [[ -z "$PROMPT" ]]; then
  exit 0
fi

# --- Pass-through rules ---

# Short confirmations (yes/no/ok/확인 etc.) — always pass
CHAR_COUNT=${#PROMPT}
if (( CHAR_COUNT < 15 )); then
  exit 0
fi

# Slash commands — always pass
if [[ "$PROMPT" == /* ]]; then
  exit 0
fi

# --- Word count ---
WORD_COUNT=$(echo "$PROMPT" | wc -w)

# Short prompts (< 5 words) — pass (likely follow-ups)
if (( WORD_COUNT < 5 )); then
  exit 0
fi

# --- Check for file paths — if present, likely specific enough ---
if echo "$PROMPT" | grep -qE '(backend/|frontend-next/|app/|src/|tests/|\.py|\.tsx?|\.md)'; then
  exit 0
fi

# --- Dangerous vague expressions ---
VAGUE_PATTERNS=(
  "make it work"
  "make it better"
  "clean up everything"
  "fix everything"
  "좀 고쳐"
  "다 고쳐"
  "전부 수정"
  "알아서 해"
  "적당히 해"
  "대충 해"
)

PROMPT_LOWER=$(echo "$PROMPT" | tr '[:upper:]' '[:lower:]')

for pattern in "${VAGUE_PATTERNS[@]}"; do
  if echo "$PROMPT_LOWER" | grep -qiF "$pattern"; then
    echo "⚠️ PROMPT NEEDS CLARIFICATION:" >&2
    echo "- Detected vague expression: \"$pattern\"" >&2
    echo "- Please be specific about WHAT to change and WHERE." >&2
    echo "" >&2
    echo "Tip: Use /dev for features, /fix for bugs, /review for code review." >&2
    exit 2
  fi
done

# --- Multi-domain detection (3+ domains = too broad) ---
DOMAIN_COUNT=0
echo "$PROMPT_LOWER" | grep -qiE '(backend|api|서버|서비스|endpoint|라우터)' && ((DOMAIN_COUNT++)) || true
echo "$PROMPT_LOWER" | grep -qiE '(frontend|ui|컴포넌트|component|페이지|화면|tsx)' && ((DOMAIN_COUNT++)) || true
echo "$PROMPT_LOWER" | grep -qiE '(database|db|모델|model|migration|스키마|schema|alembic)' && ((DOMAIN_COUNT++)) || true
echo "$PROMPT_LOWER" | grep -qiE '(test|테스트|pytest|검증)' && ((DOMAIN_COUNT++)) || true

if (( DOMAIN_COUNT >= 3 )); then
  echo "⚠️ PROMPT TOO BROAD:" >&2
  echo "- Detected $DOMAIN_COUNT domains in one request." >&2
  echo "- Use /dev for multi-domain features (it handles sequencing)." >&2
  echo "- Or break into smaller, focused requests." >&2
  exit 2
fi

# --- Questions and explanations — always pass (no code change needed) ---
if echo "$PROMPT_LOWER" | grep -qiE '(질문|설명|알려|뭐야|뭔가요|어떻게|왜|차이|비교|의미|궁금|이해|개념|원리|방법|\?|what|why|how|when|where|explain|difference|compare|mean|understand|which|should)'; then
  exit 0
fi

# All checks passed
exit 0
