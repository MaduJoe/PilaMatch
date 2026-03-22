#!/usr/bin/env bash
# write-guard.sh — PreToolUse hook for Write|Edit
# Blocks writes outside allowed directories.
# Exit 0 = allow, Exit 2 = block (reason on stderr)
# For "ask" behavior: output JSON with permissionDecision:"ask"

set -uo pipefail

# Parse JSON from stdin using python3
INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | python3 -c "import json,sys; print(json.loads(sys.stdin.read()).get('tool_name',''))" 2>/dev/null || echo "")
FILE_PATH=$(echo "$INPUT" | python3 -c "import json,sys; print(json.loads(sys.stdin.read()).get('tool_input',{}).get('file_path',''))" 2>/dev/null || echo "")

# If we can't parse, pass through
if [[ -z "$FILE_PATH" ]]; then
  exit 0
fi

# Normalize to relative path from project root
PROJECT_ROOT="/home/jkcho/PilaMatch"
REL_PATH="${FILE_PATH#$PROJECT_ROOT/}"

# --- Config file protection (advisory warning) ---
CONFIG_FILES=(
  "docker-compose.yml"
  "docker-compose.yaml"
  ".env"
  "pyproject.toml"
  "package.json"
  "CLAUDE.md"
)

BASENAME=$(basename "$REL_PATH")
for cfg in "${CONFIG_FILES[@]}"; do
  if [[ "$BASENAME" == "$cfg" ]]; then
    # Output JSON for "ask" decision
    cat <<ASKJSON
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "ask",
    "permissionDecisionReason": "Modifying config file: $BASENAME — please review carefully."
  }
}
ASKJSON
    exit 0
  fi
done

# --- Directory allowlist for new file creation ---
# Only check for Write (new file creation), not Edit (existing file)
if [[ "$TOOL_NAME" == "Write" ]]; then
  ALLOWED=false

  ALLOWED_PREFIXES=(
    "backend/app/"
    "backend/tests/"
    "backend/alembic/"
    "frontend-next/src/"
    ".claude/"
    "docs/"
  )

  # Always allow writes to user-level .claude directory (plans, memory, etc.)
  if [[ "$FILE_PATH" == /home/jkcho/.claude/* ]]; then
    ALLOWED=true
  fi

  for prefix in "${ALLOWED_PREFIXES[@]}"; do
    if [[ "$REL_PATH" == ${prefix}* ]]; then
      ALLOWED=true
      break
    fi
  done

  # Allow overwriting existing files anywhere
  if [[ "$ALLOWED" == "false" && ! -f "$FILE_PATH" ]]; then
    echo "⚠️ BLOCKED: Creating file outside allowed directories." >&2
    echo "  File: $REL_PATH" >&2
    echo "  Allowed: backend/app/, backend/tests/, backend/alembic/, frontend-next/src/, .claude/, docs/" >&2
    echo "" >&2
    echo "If this file is needed, ask the user to confirm." >&2
    exit 2
  fi
fi

exit 0
