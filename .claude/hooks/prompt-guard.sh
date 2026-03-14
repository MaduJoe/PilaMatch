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

# --- Action verb check ---
HAS_VERB=false
ACTION_VERBS="add|fix|create|update|remove|implement|refactor|delete|move|rename|change|modify|write|build|setup|configure|enable|disable|integrate|migrate|test|debug|deploy|추가|수정|삭제|변경|구현|생성|이동|리팩|설정|배포|테스트|디버그|만들|고치|확인|분석|검토|작성|적용"

if echo "$PROMPT_LOWER" | grep -qiE "($ACTION_VERBS)"; then
  HAS_VERB=true
fi

# --- Target noun check ---
HAS_TARGET=false
TARGET_NOUNS="file|function|component|endpoint|model|service|page|route|hook|test|schema|table|column|field|config|setting|button|form|api|middleware|dependency|module|class|method|파일|함수|컴포넌트|엔드포인트|모델|서비스|페이지|라우트|훅|스키마|테이블|설정|버튼|폼|미들웨어|클래스|메서드"

if echo "$PROMPT_LOWER" | grep -qiE "($TARGET_NOUNS)"; then
  HAS_TARGET=true
fi

# --- Build error message ---
ERRORS=""

if [[ "$HAS_VERB" == "false" ]]; then
  ERRORS+="- No action verb found. What should I DO? (add/fix/update/remove/implement/...)\n"
fi

if [[ "$HAS_TARGET" == "false" ]]; then
  ERRORS+="- No target specified. WHAT should I modify? (file/endpoint/component/service/...)\n"
fi

if [[ -n "$ERRORS" ]]; then
  echo "⚠️ PROMPT NEEDS CLARIFICATION:" >&2
  echo -e "$ERRORS" >&2
  echo "Tip: Use /dev for features, /fix for bugs, /review for code review." >&2
  exit 2
fi

# All checks passed
exit 0
