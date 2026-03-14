#!/usr/bin/env bash
# post-write.sh — PostToolUse hook for Write|Edit
# Shows test reminders after code changes (advisory only, never blocks).
# Exit 0 always. Stdout is added as context for Claude.

set -uo pipefail

# Parse JSON from stdin using python3
FILE_PATH=$(python3 -c "import json,sys; print(json.loads(sys.stdin.read()).get('tool_input',{}).get('file_path',''))" 2>/dev/null || echo "")

if [[ -z "$FILE_PATH" ]]; then
  exit 0
fi

PROJECT_ROOT="/home/jkcho/PilaMatch"
REL_PATH="${FILE_PATH#$PROJECT_ROOT/}"

# --- Backend service files ---
if [[ "$REL_PATH" == backend/app/services/*.py ]]; then
  SERVICE_NAME=$(basename "$REL_PATH" .py)
  echo "🧪 Run tests: cd backend && SECRET_KEY=test uv run pytest tests/test_${SERVICE_NAME}.py -v"
fi

# --- Backend API endpoint files ---
if [[ "$REL_PATH" == backend/app/api/*.py || "$REL_PATH" == backend/app/api/**/*.py ]]; then
  ENDPOINT_NAME=$(basename "$REL_PATH" .py)
  echo "🧪 Run API tests: cd backend && SECRET_KEY=test uv run pytest tests/test_${ENDPOINT_NAME}.py -v"
fi

# --- Backend model files ---
if [[ "$REL_PATH" == backend/app/models/*.py ]]; then
  echo "🧪 Schema changed — run full test suite: cd backend && SECRET_KEY=test uv run pytest --cov=app"
fi

# --- Frontend files ---
if [[ "$REL_PATH" == frontend-next/src/*.tsx || "$REL_PATH" == frontend-next/src/**/*.tsx ]]; then
  echo "🖥️ Verify in browser: DevTools → mobile view (375px width)"
fi

# --- Core security files ---
if [[ "$REL_PATH" == backend/app/core/security.py || "$REL_PATH" == backend/app/core/deps.py ]]; then
  echo "🔒 Security file changed — run: cd backend && SECRET_KEY=test uv run pytest tests/test_auth.py -v"
fi

# --- Penalty/Trust files ---
if [[ "$REL_PATH" == backend/app/services/penalty*.py || "$REL_PATH" == backend/app/services/trust*.py || "$REL_PATH" == backend/app/services/tier*.py ]]; then
  echo "🛡️ Trust system changed — run: cd backend && SECRET_KEY=test uv run pytest tests/test_penalty*.py tests/test_trust*.py -v"
fi

# Advisory only — never block
exit 0
