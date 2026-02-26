#!/usr/bin/env bash
set -euo pipefail

# ─── Colors ───────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'
CYAN='\033[0;36m'; BOLD='\033[1m'; DIM='\033[2m'; NC='\033[0m'

info()  { echo -e "${BLUE}[INFO]${NC} $*"; }
ok()    { echo -e "${GREEN}[OK]${NC}   $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
err()   { echo -e "${RED}[ERR]${NC}  $*" >&2; }

# ─── Config ───────────────────────────────────────────────────────────────────
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PARENT_DIR="$(dirname "$PROJECT_ROOT")"
BASE_BRANCH="main"

declare -a NAMES=("BACKEND" "FRONTEND" "DATA" "INFRA")
declare -a DIRS=(
    "${PARENT_DIR}/wt-backend"
    "${PARENT_DIR}/wt-frontend"
    "${PARENT_DIR}/wt-data"
    "${PARENT_DIR}/wt-infra"
)
declare -a BRANCHES=("feat/backend" "feat/frontend" "feat/data" "feat/infra")

# ─── Prereq check ────────────────────────────────────────────────────────────
cd "$PROJECT_ROOT"

if ! git rev-parse --is-inside-work-tree &>/dev/null; then
    err "Not a git repository: $PROJECT_ROOT"
    exit 1
fi

# Check if any worktrees exist
any_exists=false
for dir in "${DIRS[@]}"; do
    if [[ -d "$dir" ]]; then
        any_exists=true
        break
    fi
done

if [[ "$any_exists" == false ]]; then
    err "No worktrees found. Run worktree-tmux.sh first."
    exit 1
fi

# ─── Gather data ─────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}PilaMatch Worktree Status${NC}"
echo -e "${DIM}$(date '+%Y-%m-%d %H:%M:%S')${NC}"
echo ""

# Table header
printf "┌───────────┬───────────────────┬──────────┬───────────┬──────────┐\n"
printf "│ %-9s │ %-17s │ %-8s │ %-9s │ %-8s │\n" \
    "Worktree" "Branch" "Commits" "Status" "Changed"
printf "├───────────┼───────────────────┼──────────┼───────────┼──────────┤\n"

# Track changed files per worktree for conflict detection
declare -A ALL_CHANGED_FILES  # file -> list of worktree names

for i in 0 1 2 3; do
    name="${NAMES[$i]}"
    dir="${DIRS[$i]}"
    branch="${BRANCHES[$i]}"

    if [[ ! -d "$dir" ]]; then
        printf "│ %-9s │ %-17s │ %8s │ %-9s │ %8s │\n" \
            "$name" "$branch" "-" "MISSING" "-"
        continue
    fi

    # Count commits ahead of main
    commits=$(git -C "$dir" rev-list --count "${BASE_BRANCH}..HEAD" 2>/dev/null || echo "0")

    # Check dirty status
    dirty_count=$(git -C "$dir" status --porcelain 2>/dev/null | wc -l)
    if [[ "$dirty_count" -gt 0 ]]; then
        status="${dirty_count} dirty"
    else
        status="clean"
    fi

    # Count changed files vs main
    changed=$(git -C "$dir" diff --name-only "${BASE_BRANCH}..HEAD" 2>/dev/null | wc -l)

    # Color the status
    if [[ "$status" == "clean" ]]; then
        status_display="${GREEN}clean${NC}    "
    else
        status_display="${YELLOW}${status}${NC}"
        # Pad to fit column
        pad_len=$((9 - ${#status}))
        status_display="${YELLOW}${status}${NC}$(printf '%*s' "$pad_len" '')"
    fi

    printf "│ %-9s │ %-17s │ %8s │ " "$name" "$branch" "$commits"
    echo -en "$status_display"
    printf " │ %8s │\n" "$changed"

    # Collect changed files for conflict detection
    while IFS= read -r file; do
        [[ -z "$file" ]] && continue
        if [[ -n "${ALL_CHANGED_FILES[$file]:-}" ]]; then
            ALL_CHANGED_FILES[$file]="${ALL_CHANGED_FILES[$file]}, $name"
        else
            ALL_CHANGED_FILES[$file]="$name"
        fi
    done < <(git -C "$dir" diff --name-only "${BASE_BRANCH}..HEAD" 2>/dev/null)

    # Also include uncommitted changes
    while IFS= read -r line; do
        file="${line:3}"
        [[ -z "$file" ]] && continue
        if [[ -n "${ALL_CHANGED_FILES[$file]:-}" ]]; then
            ALL_CHANGED_FILES[$file]="${ALL_CHANGED_FILES[$file]}, $name"
        else
            ALL_CHANGED_FILES[$file]="$name"
        fi
    done < <(git -C "$dir" status --porcelain 2>/dev/null)
done

printf "└───────────┴───────────────────┴──────────┴───────────┴──────────┘\n"

# ─── Detailed diff stats per worktree ─────────────────────────────────────────
echo ""
echo -e "${BOLD}Detailed Changes${NC}"
echo ""

for i in 0 1 2 3; do
    name="${NAMES[$i]}"
    dir="${DIRS[$i]}"
    branch="${BRANCHES[$i]}"

    if [[ ! -d "$dir" ]]; then
        continue
    fi

    committed_changes=$(git -C "$dir" diff --stat "${BASE_BRANCH}..HEAD" 2>/dev/null)
    uncommitted_changes=$(git -C "$dir" diff --stat 2>/dev/null)
    staged_changes=$(git -C "$dir" diff --cached --stat 2>/dev/null)

    if [[ -z "$committed_changes" && -z "$uncommitted_changes" && -z "$staged_changes" ]]; then
        continue
    fi

    echo -e "  ${CYAN}${BOLD}${name}${NC} (${branch}):"

    if [[ -n "$committed_changes" ]]; then
        echo -e "    ${DIM}Committed:${NC}"
        echo "$committed_changes" | sed 's/^/      /'
    fi

    if [[ -n "$staged_changes" ]]; then
        echo -e "    ${DIM}Staged:${NC}"
        echo "$staged_changes" | sed 's/^/      /'
    fi

    if [[ -n "$uncommitted_changes" ]]; then
        echo -e "    ${DIM}Unstaged:${NC}"
        echo "$uncommitted_changes" | sed 's/^/      /'
    fi

    echo ""
done

# ─── Conflict detection ──────────────────────────────────────────────────────
echo -e "${BOLD}Conflict Analysis${NC}"
echo ""

conflict_found=false
for file in "${!ALL_CHANGED_FILES[@]}"; do
    worktrees="${ALL_CHANGED_FILES[$file]}"
    # Check if the file appears in more than one worktree (contains a comma)
    if [[ "$worktrees" == *","* ]]; then
        if [[ "$conflict_found" == false ]]; then
            echo -e "  ${RED}${BOLD}!! Potential Conflicts Detected:${NC}"
            conflict_found=true
        fi
        echo -e "  ${RED}!!${NC} ${file} → ${YELLOW}${worktrees}${NC}"
    fi
done

if [[ "$conflict_found" == false ]]; then
    echo -e "  ${GREEN}No potential conflicts detected across worktrees.${NC}"
fi

echo ""
