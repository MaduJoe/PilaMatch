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
SESSION="pilamatch"
BASE_BRANCH="main"
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PARENT_DIR="$(dirname "$PROJECT_ROOT")"
TODOS_DIR="${PROJECT_ROOT}/scripts/worktree-todos"

declare -a NAMES=("BACKEND" "FRONTEND" "DATA" "INFRA")
declare -a DIRS=(
    "${PARENT_DIR}/wt-backend"
    "${PARENT_DIR}/wt-frontend"
    "${PARENT_DIR}/wt-data"
    "${PARENT_DIR}/wt-infra"
)
declare -a BRANCHES=("feat/backend" "feat/frontend" "feat/data" "feat/infra")
declare -a TODO_FILES=(
    "${TODOS_DIR}/backend.md"
    "${TODOS_DIR}/frontend.md"
    "${TODOS_DIR}/data.md"
    "${TODOS_DIR}/infra.md"
)
declare -a PROMPTS=(
    "WORKTREE_TODO.md 를 읽고 모든 Task를 순서대로 구현해. 각 Task 완료 후 반드시 테스트 실행하고 git commit 해. 수정 범위를 벗어나는 파일은 절대 수정하지 마."
    "WORKTREE_TODO.md 를 읽고 모든 Task를 순서대로 구현해. 각 Task 완료 후 npm run build 확인하고 git commit 해. 수정 범위를 벗어나는 파일은 절대 수정하지 마."
    "WORKTREE_TODO.md 를 읽고 모든 Task를 순서대로 구현해. 모델 변경 후 반드시 Alembic 마이그레이션 생성하고, 테스트 실행 후 git commit 해. 수정 범위를 벗어나는 파일은 절대 수정하지 마."
    "WORKTREE_TODO.md 를 읽고 모든 Task를 순서대로 구현해. Docker/CI 변경 후 문법 검증하고 git commit 해. 수정 범위를 벗어나는 파일은 절대 수정하지 마."
)

# ─── Usage ────────────────────────────────────────────────────────────────────
usage() {
    echo -e "${BOLD}Usage:${NC} $0 [OPTIONS]"
    echo ""
    echo "  Creates 4 worktrees, copies TODO files, and launches Claude Code in each."
    echo ""
    echo -e "${BOLD}Options:${NC}"
    echo "  --auto         Launch Claude with auto-execute prompts (non-interactive)"
    echo "  --interactive  Launch Claude interactively (default, TODO file copied)"
    echo "  --dry-run      Show what would be done without executing"
    echo "  --help         Show this help"
    echo ""
    echo -e "${BOLD}Examples:${NC}"
    echo "  $0                  # Interactive: Claude opens, you send the prompt"
    echo "  $0 --auto           # Auto: Claude starts working immediately"
    echo ""
}

MODE="interactive"
DRY_RUN=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --auto)       MODE="auto"; shift ;;
        --interactive) MODE="interactive"; shift ;;
        --dry-run)    DRY_RUN=true; shift ;;
        --help|-h)    usage; exit 0 ;;
        *)            err "Unknown option: $1"; usage; exit 1 ;;
    esac
done

# ─── Prereq checks ───────────────────────────────────────────────────────────
cd "$PROJECT_ROOT"

if ! git rev-parse --is-inside-work-tree &>/dev/null; then
    err "Not a git repository: $PROJECT_ROOT"
    exit 1
fi

if ! command -v tmux &>/dev/null; then
    err "tmux not installed. Install: sudo apt install tmux"
    exit 1
fi

if ! command -v claude &>/dev/null; then
    err "claude CLI not found. Install from: https://claude.ai/code"
    exit 1
fi

for f in "${TODO_FILES[@]}"; do
    if [[ ! -f "$f" ]]; then
        err "TODO file not found: $f"
        err "Run from project root with scripts/worktree-todos/*.md present."
        exit 1
    fi
done

# ─── Display plan ─────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║  PilaMatch — 4-Worktree Parallel Development Launch        ║${NC}"
echo -e "${BOLD}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${BOLD}Plan:${NC}"
for i in 0 1 2 3; do
    echo -e "  ${CYAN}${NAMES[$i]}${NC} → ${DIRS[$i]}"
    echo -e "    Branch: ${BRANCHES[$i]}"
    echo -e "    TODO:   ${TODO_FILES[$i]}"
done

echo ""
echo -e "  Mode: ${BOLD}${MODE}${NC}"
echo ""

if [[ "$DRY_RUN" == true ]]; then
    warn "Dry-run mode. Exiting."
    exit 0
fi

# ─── Create worktrees (idempotent) ───────────────────────────────────────────
info "Creating worktrees from ${BOLD}${BASE_BRANCH}${NC}..."

for i in 0 1 2 3; do
    dir="${DIRS[$i]}"
    branch="${BRANCHES[$i]}"
    name="${NAMES[$i]}"

    if [[ -d "$dir" ]]; then
        ok "${name} worktree already exists"
    else
        if git show-ref --verify --quiet "refs/heads/${branch}"; then
            git worktree add "$dir" "$branch"
        else
            git worktree add -b "$branch" "$dir" "$BASE_BRANCH"
        fi
        ok "${name} worktree created → ${dir}"
    fi
done

echo ""

# ─── Copy TODO files into worktrees ──────────────────────────────────────────
info "Copying TODO files into worktrees..."

for i in 0 1 2 3; do
    cp "${TODO_FILES[$i]}" "${DIRS[$i]}/WORKTREE_TODO.md"
    ok "${NAMES[$i]}: WORKTREE_TODO.md copied"
done

echo ""

# ─── Kill existing session if any ────────────────────────────────────────────
if tmux has-session -t "$SESSION" 2>/dev/null; then
    warn "Existing tmux session '${SESSION}' found."
    read -r -p "Kill and recreate? [y/N] " confirm
    if [[ "${confirm,,}" == "y" ]]; then
        tmux kill-session -t "$SESSION"
        ok "Old session killed"
    else
        info "Attaching to existing session..."
        exec tmux attach -t "$SESSION"
    fi
fi

# ─── Create tmux 2x2 session ─────────────────────────────────────────────────
info "Creating tmux session '${SESSION}'..."

tmux new-session -d -s "$SESSION" -c "${DIRS[0]}" -x "$(tput cols)" -y "$(tput lines)"
tmux split-window -h -t "${SESSION}:0" -c "${DIRS[1]}"
tmux split-window -v -t "${SESSION}:0.0" -c "${DIRS[2]}"
tmux split-window -v -t "${SESSION}:0.1" -c "${DIRS[3]}"
tmux select-layout -t "${SESSION}:0" tiled

# ─── Configure tmux ──────────────────────────────────────────────────────────
tmux set-option -t "$SESSION" prefix C-a
tmux bind-key -T prefix C-a send-prefix
tmux set-option -t "$SESSION" mouse on
tmux set-option -t "$SESSION" pane-border-status top
tmux set-option -t "$SESSION" pane-border-format \
    " #{pane_index}: #{pane_title} "
tmux set-option -t "$SESSION" pane-active-border-style "fg=green,bold"
tmux set-option -t "$SESSION" pane-border-style "fg=colour240"
tmux set-option -t "$SESSION" status-style "bg=colour235,fg=white"
tmux set-option -t "$SESSION" status-left \
    "#[fg=black,bg=green,bold] PilaMatch #[default] "
tmux set-option -t "$SESSION" status-right \
    "#[fg=yellow]%H:%M #[fg=cyan]%Y-%m-%d "
tmux set-option -t "$SESSION" status-left-length 30

# ─── Launch Claude in each pane ───────────────────────────────────────────────
PANE_ORDER=(0 1 2 3)

for idx in 0 1 2 3; do
    pane="${PANE_ORDER[$idx]}"
    name="${NAMES[$idx]}"
    prompt="${PROMPTS[$idx]}"

    # Set pane title
    tmux select-pane -t "${SESSION}:0.${pane}" -T "${name}"

    if [[ "$MODE" == "auto" ]]; then
        # Auto mode: launch claude with the prompt directly
        # Escape single quotes in prompt
        escaped_prompt="${prompt//\'/\'\\\'\'}"
        tmux send-keys -t "${SESSION}:0.${pane}" \
            "claude '${escaped_prompt}'" Enter
    else
        # Interactive mode: show banner, then launch claude
        tmux send-keys -t "${SESSION}:0.${pane}" "clear" Enter
        tmux send-keys -t "${SESSION}:0.${pane}" \
            "echo ''" Enter
        tmux send-keys -t "${SESSION}:0.${pane}" \
            "echo '  [$name] WORKTREE_TODO.md ready.'" Enter
        tmux send-keys -t "${SESSION}:0.${pane}" \
            "echo '  Send this prompt to Claude:'" Enter
        tmux send-keys -t "${SESSION}:0.${pane}" \
            "echo '  → Read WORKTREE_TODO.md and implement all tasks.'" Enter
        tmux send-keys -t "${SESSION}:0.${pane}" \
            "echo ''" Enter
        tmux send-keys -t "${SESSION}:0.${pane}" "claude" Enter
    fi
done

# Select first pane
tmux select-pane -t "${SESSION}:0.0"

# ─── Attach ──────────────────────────────────────────────────────────────────
echo ""
ok "All 4 worktrees ready with Claude Code."
echo ""
echo -e "  ${BOLD}Tmux Controls:${NC}"
echo -e "  ${CYAN}Ctrl-a + ←↑→↓${NC}  Move between panes"
echo -e "  ${CYAN}Ctrl-a + z${NC}      Zoom/unzoom pane (focus on one Claude)"
echo -e "  ${CYAN}Ctrl-a + d${NC}      Detach (Claude keeps running)"
echo -e "  ${CYAN}Ctrl-a + [${NC}      Scroll mode (q to exit)"
echo ""
echo -e "  ${BOLD}After work is done:${NC}"
echo -e "  ${DIM}./scripts/worktree-status.sh${NC}   Check progress"
echo -e "  ${DIM}./scripts/worktree-cleanup.sh${NC}  Merge all branches"
echo ""

exec tmux attach -t "$SESSION"
