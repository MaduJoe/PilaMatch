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

# Merge order matters: backend first (API contracts), then consumers, then infra last
declare -a NAMES=("BACKEND" "FRONTEND" "DATA" "INFRA")
declare -a DIRS=(
    "${PARENT_DIR}/wt-backend"
    "${PARENT_DIR}/wt-frontend"
    "${PARENT_DIR}/wt-data"
    "${PARENT_DIR}/wt-infra"
)
declare -a BRANCHES=("feat/backend" "feat/frontend" "feat/data" "feat/infra")

DRY_RUN=false
if [[ "${1:-}" == "--dry-run" ]]; then
    DRY_RUN=true
    warn "Dry-run mode: no changes will be made"
    echo ""
fi

# ─── Prereq checks ───────────────────────────────────────────────────────────
cd "$PROJECT_ROOT"

if ! git rev-parse --is-inside-work-tree &>/dev/null; then
    err "Not a git repository: $PROJECT_ROOT"
    exit 1
fi

# Must be on main branch in the main worktree
current_branch=$(git branch --show-current)
if [[ "$current_branch" != "$BASE_BRANCH" ]]; then
    err "Must be on '${BASE_BRANCH}' branch to merge. Currently on '${current_branch}'."
    err "Run: git checkout ${BASE_BRANCH}"
    exit 1
fi

# Check for uncommitted changes in main worktree
if [[ -n "$(git status --porcelain)" ]]; then
    err "Main worktree has uncommitted changes. Commit or stash first."
    exit 1
fi

# ─── Pre-merge: check for dirty worktrees ────────────────────────────────────
echo -e "${BOLD}Pre-merge Checks${NC}"
echo ""

has_dirty=false
for i in 0 1 2 3; do
    name="${NAMES[$i]}"
    dir="${DIRS[$i]}"
    branch="${BRANCHES[$i]}"

    if [[ ! -d "$dir" ]]; then
        info "${name}: worktree not found (skipping)"
        continue
    fi

    dirty_count=$(git -C "$dir" status --porcelain 2>/dev/null | wc -l)
    commits=$(git rev-list --count "${BASE_BRANCH}..${branch}" 2>/dev/null || echo "0")

    if [[ "$dirty_count" -gt 0 ]]; then
        err "${name} (${branch}): ${dirty_count} uncommitted changes!"
        has_dirty=true
    elif [[ "$commits" -eq 0 ]]; then
        info "${name} (${branch}): no commits ahead of ${BASE_BRANCH} (will skip)"
    else
        ok "${name} (${branch}): ${commits} commits ready to merge"
    fi
done

if [[ "$has_dirty" == true ]]; then
    echo ""
    err "Aborting: some worktrees have uncommitted changes."
    err "Commit all changes in each worktree before cleanup."
    exit 1
fi

echo ""

if [[ "$DRY_RUN" == true ]]; then
    info "Dry-run complete. Rerun without --dry-run to execute."
    exit 0
fi

# ─── Confirmation ─────────────────────────────────────────────────────────────
echo -e "${YELLOW}${BOLD}This will:${NC}"
echo -e "  1. Merge each feature branch into ${BASE_BRANCH} (--no-ff)"
echo -e "  2. Remove worktrees and delete feature branches"
echo ""
read -r -p "Proceed? [y/N] " confirm
if [[ "${confirm,,}" != "y" ]]; then
    info "Cancelled."
    exit 0
fi

echo ""

# ─── Sequential merge ────────────────────────────────────────────────────────
echo -e "${BOLD}Merging branches into ${BASE_BRANCH}...${NC}"
echo ""

merged_count=0

for i in 0 1 2 3; do
    name="${NAMES[$i]}"
    dir="${DIRS[$i]}"
    branch="${BRANCHES[$i]}"

    # Skip if branch doesn't exist
    if ! git show-ref --verify --quiet "refs/heads/${branch}" 2>/dev/null; then
        info "${name}: branch '${branch}' not found, skipping"
        continue
    fi

    # Skip if no commits ahead
    commits=$(git rev-list --count "${BASE_BRANCH}..${branch}" 2>/dev/null || echo "0")
    if [[ "$commits" -eq 0 ]]; then
        info "${name}: no new commits, skipping merge"
    else
        info "Merging ${CYAN}${branch}${NC} (${commits} commits)..."

        if ! git merge --no-ff -m "merge: ${branch} into ${BASE_BRANCH}" "$branch"; then
            echo ""
            err "MERGE CONFLICT while merging ${branch}!"
            err ""
            err "Conflicted files:"
            git diff --name-only --diff-filter=U | sed 's/^/    /'
            err ""
            err "Aborting merge..."
            git merge --abort
            err ""
            err "Resolution steps:"
            err "  1. cd ${dir}"
            err "  2. Resolve conflicts with the other branches"
            err "  3. Commit the resolution"
            err "  4. Re-run this script"
            exit 1
        fi

        ok "${name}: merged successfully"
        merged_count=$((merged_count + 1))
    fi

    # Remove worktree
    if [[ -d "$dir" ]]; then
        info "Removing worktree: ${dir}"
        git worktree remove "$dir" --force 2>/dev/null || true
        ok "${name}: worktree removed"
    fi

    # Delete branch
    if git show-ref --verify --quiet "refs/heads/${branch}" 2>/dev/null; then
        git branch -d "$branch" 2>/dev/null || git branch -D "$branch" 2>/dev/null || true
        ok "${name}: branch '${branch}' deleted"
    fi

    echo ""
done

# ─── Prune worktree metadata ─────────────────────────────────────────────────
git worktree prune 2>/dev/null || true

# ─── Summary ──────────────────────────────────────────────────────────────────
echo -e "${BOLD}${GREEN}Cleanup Complete${NC}"
echo ""

echo -e "${BOLD}Remaining worktrees:${NC}"
git worktree list
echo ""

if [[ "$merged_count" -gt 0 ]]; then
    echo -e "${BOLD}Merge history:${NC}"
    git log --oneline --graph -$((merged_count + 5))
    echo ""
fi

ok "All feature branches merged into ${BASE_BRANCH}. Ready to push."
echo -e "  ${DIM}git push origin ${BASE_BRANCH}${NC}"
echo ""
