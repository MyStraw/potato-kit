#!/usr/bin/env bash
# potato-kit -> Codex native install (macOS / Linux)
set -euo pipefail

KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CODEX_DIR="${CODEX_HOME:-$HOME/.codex}"
SKILLS_HOME="${POTATO_CODEX_SKILLS_HOME:-$HOME/.agents/skills}"
ENV_NAME="potato"
SKIP_ENVIRONMENT=0
SKIP_MCP=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --codex-home) CODEX_DIR="$2"; shift 2 ;;
    --skills-home) SKILLS_HOME="$2"; shift 2 ;;
    --skip-environment) SKIP_ENVIRONMENT=1; shift ;;
    --skip-mcp) SKIP_MCP=1; shift ;;
    *) printf 'Unknown option: %s\n' "$1" >&2; exit 2 ;;
  esac
done

export CODEX_HOME="$CODEX_DIR"

say()  { printf "\n\033[1;36m> %s\033[0m\n" "$1"; }
ok()   { printf "  \033[32m[OK]\033[0m %s\n" "$1"; }
warn() { printf "  \033[33m[!]\033[0m %s\n" "$1"; }
fail() { printf "  \033[31m[X]\033[0m %s\n" "$1"; }

printf '\n[potato] potato-kit -> Codex native install\n'
printf '         kit: %s\n' "$KIT_DIR"

say "1/5 prerequisites"
mkdir -p "$CODEX_DIR"
if ! command -v codex >/dev/null 2>&1; then
  fail "Codex CLI is not installed"
  printf '     npm i -g @openai/codex or brew install codex\n'
  exit 1
fi
ok "Codex: $(codex --version 2>/dev/null | head -1)"

if [[ "$SKIP_ENVIRONMENT" -eq 0 ]]; then
  if ! command -v conda >/dev/null 2>&1; then
    fail "conda is not installed"
    exit 1
  fi
  ok "conda: $(conda --version)"
elif ! command -v python3 >/dev/null 2>&1; then
  fail "--skip-environment validation requires python3"
  exit 1
fi

say "2/5 conda environment and packages"
if [[ "$SKIP_ENVIRONMENT" -eq 1 ]]; then
  warn "skipping environment and package installation"
else
  if conda env list | grep -qE "^${ENV_NAME}[[:space:]]"; then
    ok "'$ENV_NAME' environment already exists"
  else
    conda create -n "$ENV_NAME" python=3.11 -y
    ok "created '$ENV_NAME' environment"
  fi
  conda run -n "$ENV_NAME" python -m pip install -q --upgrade pip
  conda run -n "$ENV_NAME" python -m pip install -q \
    pandas numpy scipy scikit-learn matplotlib seaborn jupyterlab ipykernel \
    python-dotenv openpyxl paper-search-mcp jupyter-mcp-server
  ok "installed analysis and MCP packages"
fi

say "3/5 MCP registration"
if [[ "$SKIP_MCP" -eq 1 ]]; then
  warn "skipping MCP registration"
elif codex mcp get paper-search --json >/dev/null 2>&1; then
  ok "preserved existing paper-search MCP configuration"
else
  codex mcp add paper-search -- \
    conda run --no-capture-output -n "$ENV_NAME" python -m paper_search_mcp.server
  ok "registered paper-search MCP"
fi
printf '  jupyter MCP requires a running server -> ./start-jupyter.sh\n'

say "4/5 native Codex skills, agents, and guidance"
HELPER="$KIT_DIR/scripts/install_codex_assets.py"
if [[ "$SKIP_ENVIRONMENT" -eq 1 ]]; then
  python3 "$HELPER" --kit-dir "$KIT_DIR" --codex-home "$CODEX_DIR" \
    --skills-home "$SKILLS_HOME"
else
  conda run --no-capture-output -n "$ENV_NAME" python "$HELPER" \
    --kit-dir "$KIT_DIR" --codex-home "$CODEX_DIR" --skills-home "$SKILLS_HOME"
fi
ok "13 skills -> $SKILLS_HOME"
ok "4 custom agents -> $CODEX_DIR/agents"
ok "global guidance -> $CODEX_DIR/AGENTS.md"

say "5/5 verification"
required_skills=(
  potato-research potato-start potato-lit-review potato-find-data potato-eda
  potato-experiment potato-reproduce potato-optimize potato-report potato-slides
  potato-submit potato-add-pack potato-statusline
)
for skill in "${required_skills[@]}"; do
  if [[ ! -f "$SKILLS_HOME/$skill/SKILL.md" ]]; then
    fail "missing skill: $skill"
    exit 1
  fi
done
agent_count="$(find "$CODEX_DIR/agents" -maxdepth 1 -type f -name '*.toml' | wc -l | tr -d ' ')"
if [[ "$agent_count" -lt 4 ]]; then
  fail "fewer than 4 custom agents were installed"
  exit 1
fi
ok "verified 13 skills and $agent_count agents"

cat <<'EOF'

------------------------------------------------------------
[potato] Codex install complete

  Restart the Codex app/CLI so it loads the new skills and agents.

  Verify
    codex mcp list
    Invoke $potato-research or ask "연구 시작해줘"

  Status line
    Run /statusline in Codex CLI

  Methodology audit
    Ask Codex to delegate the audit to the methods-reviewer agent.
------------------------------------------------------------
EOF
