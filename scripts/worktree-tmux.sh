#!/usr/bin/env bash
set -euo pipefail

# ─── Colors ───────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'
CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

info()  { echo -e "${BLUE}[INFO]${NC} $*"; }
ok()    { echo -e "${GREEN}[OK]${NC}   $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
err()   { echo -e "${RED}[ERR]${NC}  $*" >&2; }

# ─── Config ───────────────────────────────────────────────────────────────────
SESSION="pilamatch"
BASE_BRANCH="main"
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PARENT_DIR="$(dirname "$PROJECT_ROOT")"

declare -A WT_NAMES=( [0]="BACKEND" [1]="FRONTEND" [2]="DATA" [3]="INFRA" )
declare -A WT_DIRS=(
    [0]="${PARENT_DIR}/wt-backend"
    [1]="${PARENT_DIR}/wt-frontend"
    [2]="${PARENT_DIR}/wt-data"
    [3]="${PARENT_DIR}/wt-infra"
)
declare -A WT_BRANCHES=(
    [0]="feat/backend"
    [1]="feat/frontend"
    [2]="feat/data"
    [3]="feat/infra"
)
declare -A WT_SCOPES=(
    [0]="API + Services (backend/app/api/, services/, schemas/)"
    [1]="Next.js UI (frontend-next/src/)"
    [2]="Models + Payment (backend/app/models/, alembic/, payment)"
    [3]="DevOps + Tests (docker, CI/CD, tests/, docs/)"
)
declare -A WT_COLORS=( [0]="green" [1]="cyan" [2]="yellow" [3]="magenta" )

WITH_CLAUDE=false
if [[ "${1:-}" == "--with-claude" ]]; then
    WITH_CLAUDE=true
fi

# ─── Prereq checks ───────────────────────────────────────────────────────────
cd "$PROJECT_ROOT"

if ! git rev-parse --is-inside-work-tree &>/dev/null; then
    err "Not a git repository: $PROJECT_ROOT"
    exit 1
fi

if ! command -v tmux &>/dev/null; then
    err "tmux is not installed. Install with: sudo apt install tmux"
    exit 1
fi

if [[ "$WITH_CLAUDE" == true ]] && ! command -v claude &>/dev/null; then
    err "claude CLI not found. Install from: https://claude.ai/code"
    exit 1
fi

# ─── Create worktrees (idempotent) ───────────────────────────────────────────
info "Creating worktrees from ${BOLD}${BASE_BRANCH}${NC}..."

for i in 0 1 2 3; do
    dir="${WT_DIRS[$i]}"
    branch="${WT_BRANCHES[$i]}"
    name="${WT_NAMES[$i]}"

    if [[ -d "$dir" ]]; then
        ok "${name} worktree already exists at ${dir}"
    else
        # Create branch if it already exists (e.g. from a previous partial run)
        if git show-ref --verify --quiet "refs/heads/${branch}"; then
            git worktree add "$dir" "$branch"
        else
            git worktree add -b "$branch" "$dir" "$BASE_BRANCH"
        fi
        ok "${name} worktree created → ${dir} (${branch})"
    fi
done

echo ""
info "Worktree summary:"
git worktree list
echo ""

# ─── Create tmux session (idempotent) ────────────────────────────────────────
if tmux has-session -t "$SESSION" 2>/dev/null; then
    warn "tmux session '${SESSION}' already exists. Attaching..."
    exec tmux attach -t "$SESSION"
fi

info "Creating tmux session '${SESSION}' with 2x2 layout..."

# Create session with first pane (BACKEND)
tmux new-session -d -s "$SESSION" -c "${WT_DIRS[0]}" -x "$(tput cols)" -y "$(tput lines)"

# Split into 2x2 grid
tmux split-window -h -t "${SESSION}:0" -c "${WT_DIRS[1]}"   # Right pane (FRONTEND)
tmux split-window -v -t "${SESSION}:0.0" -c "${WT_DIRS[2]}" # Bottom-left (DATA)
tmux split-window -v -t "${SESSION}:0.1" -c "${WT_DIRS[3]}" # Bottom-right (INFRA)

# Apply tiled layout for even sizing
tmux select-layout -t "${SESSION}:0" tiled

# ─── Configure tmux ──────────────────────────────────────────────────────────
# Prefix: Ctrl-a (more ergonomic than Ctrl-b)
tmux set-option -t "$SESSION" prefix C-a
tmux bind-key -T prefix C-a send-prefix

# Mouse support
tmux set-option -t "$SESSION" mouse on

# Pane border styling
tmux set-option -t "$SESSION" pane-border-status top
tmux set-option -t "$SESSION" pane-border-format \
    " #{pane_index}: #{pane_title} (#{pane_current_path}) "
tmux set-option -t "$SESSION" pane-active-border-style "fg=green,bold"
tmux set-option -t "$SESSION" pane-border-style "fg=colour240"

# Status bar
tmux set-option -t "$SESSION" status-style "bg=colour235,fg=white"
tmux set-option -t "$SESSION" status-left \
    "#[fg=black,bg=green,bold] PilaMatch #[default] "
tmux set-option -t "$SESSION" status-right \
    "#[fg=yellow]%H:%M #[fg=cyan]%Y-%m-%d "
tmux set-option -t "$SESSION" status-left-length 30

# ─── Set pane titles and display banners ─────────────────────────────────────
# Pane mapping after tiled layout: 0=top-left, 1=top-right, 2=bottom-left, 3=bottom-right
PANE_ORDER=(0 1 2 3)

for idx in 0 1 2 3; do
    pane="${PANE_ORDER[$idx]}"
    name="${WT_NAMES[$idx]}"
    branch="${WT_BRANCHES[$idx]}"
    scope="${WT_SCOPES[$idx]}"
    color="${WT_COLORS[$idx]}"

    # Set pane title
    tmux select-pane -t "${SESSION}:0.${pane}" -T "${name}"

    # Display role banner
    tmux send-keys -t "${SESSION}:0.${pane}" "clear" Enter
    tmux send-keys -t "${SESSION}:0.${pane}" \
        "echo -e '\\n  ╔══════════════════════════════════════╗'" Enter
    tmux send-keys -t "${SESSION}:0.${pane}" \
        "echo -e '  ║  ${name} Worktree'" Enter
    tmux send-keys -t "${SESSION}:0.${pane}" \
        "echo -e '  ║  Branch: ${branch}'" Enter
    tmux send-keys -t "${SESSION}:0.${pane}" \
        "echo -e '  ║  Scope:  ${scope}'" Enter
    tmux send-keys -t "${SESSION}:0.${pane}" \
        "echo -e '  ╚══════════════════════════════════════╝\\n'" Enter

    # Launch claude if requested
    if [[ "$WITH_CLAUDE" == true ]]; then
        tmux send-keys -t "${SESSION}:0.${pane}" "claude" Enter
    fi
done

# Select first pane
tmux select-pane -t "${SESSION}:0.0"

# ─── Attach ──────────────────────────────────────────────────────────────────
ok "All worktrees ready. Attaching to tmux session..."
echo ""
echo -e "  ${BOLD}Quick Reference:${NC}"
echo -e "  ${CYAN}Ctrl-a + ←↑→↓${NC}  Move between panes"
echo -e "  ${CYAN}Ctrl-a + z${NC}      Zoom/unzoom pane"
echo -e "  ${CYAN}Ctrl-a + d${NC}      Detach session"
echo -e "  ${CYAN}Ctrl-a + [${NC}      Scroll mode (q to exit)"
echo ""

exec tmux attach -t "$SESSION"
