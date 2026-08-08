#!/usr/bin/env bash
# potato-kit → Codex CLI 설치 (macOS / Linux)
#
# Claude Code 와 Codex 는 구조가 다르다:
#   Claude Code : CLAUDE.md + 슬래시 스킬 + 서브에이전트  (전부 지원)
#   Codex       : AGENTS.md + MCP                        (슬래시 스킬·서브에이전트 없음)
#
# 그래서 이 스크립트는 스킬 파일을 그대로 두고, AGENTS.md 가 "언제 어느 파일을
# 읽어야 하는지" 알려주는 라우터가 되게 만든다. Codex 는 파일을 읽을 수 있으므로
# 절차 자체는 동일하게 따를 수 있다.
set -uo pipefail

KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CODEX_DIR="${CODEX_HOME:-$HOME/.codex}"
ENV_NAME="potato"

say()  { printf "\n\033[1;36m▶ %s\033[0m\n" "$1"; }
ok()   { printf "  \033[32m✓\033[0m %s\n" "$1"; }
warn() { printf "  \033[33m!\033[0m %s\n" "$1"; }
fail() { printf "  \033[31m✗\033[0m %s\n" "$1"; }

echo "🥔 potato-kit → Codex CLI 설치"
echo "   킷 위치: $KIT_DIR"

# ---------------------------------------------------------------- 1. 사전 확인
say "1/4 사전 확인"
mkdir -p "$CODEX_DIR"      # codex 는 CODEX_HOME 이 없으면 설정 로드에 실패한다
if ! command -v codex >/dev/null 2>&1; then
  fail "Codex CLI 가 없습니다."
  echo "     npm i -g @openai/codex  또는  brew install codex"
  exit 1
fi
ok "Codex: $(codex --version 2>/dev/null | head -1)"

if ! command -v conda >/dev/null 2>&1; then
  fail "conda 가 없습니다. Miniconda 를 먼저 설치하세요."
  exit 1
fi
ok "conda: $(conda --version)"

# ---------------------------------------------------------------- 2. 환경·패키지
say "2/4 conda 환경 · 패키지"
if conda env list | grep -qE "^${ENV_NAME}\s"; then
  ok "'$ENV_NAME' 환경이 이미 있습니다"
else
  conda create -n "$ENV_NAME" python=3.11 -y >/dev/null 2>&1 \
    && ok "'$ENV_NAME' 환경 생성" || { fail "환경 생성 실패"; exit 1; }
fi
conda run -n "$ENV_NAME" pip install -q --upgrade pip >/dev/null 2>&1
conda run -n "$ENV_NAME" pip install -q \
  pandas numpy scipy scikit-learn matplotlib seaborn jupyterlab ipykernel \
  python-dotenv openpyxl paper-search-mcp jupyter-mcp-server >/dev/null 2>&1 \
  && ok "패키지 설치 완료" || warn "일부 패키지 설치 실패"

# ---------------------------------------------------------------- 3. MCP 등록
say "3/4 MCP 등록 (codex mcp add)"
codex mcp remove paper-search >/dev/null 2>&1 || true
if codex mcp add paper-search -- \
     conda run --no-capture-output -n "$ENV_NAME" python -m paper_search_mcp.server >/dev/null 2>&1; then
  ok "paper-search 등록 (arXiv·PubMed·OpenAlex 등 20+ 플랫폼)"
else
  warn "paper-search 등록 실패 — 직접 실행해보세요:"
  echo "     codex mcp add paper-search -- conda run --no-capture-output -n $ENV_NAME python -m paper_search_mcp.server"
fi
echo "  jupyter MCP 는 주피터 서버가 떠 있어야 합니다 → ./start-jupyter.sh"

# ---------------------------------------------------------------- 4. AGENTS.md
say "4/4 AGENTS.md 생성"
OUT="$CODEX_DIR/AGENTS.md"
KIT_MARK="<!-- potato-kit -->"

if [ -f "$OUT" ] && ! grep -q "$KIT_MARK" "$OUT" 2>/dev/null; then
  cp "$OUT" "$OUT.bak.$(date +%s)"
  warn "기존 AGENTS.md 를 백업했습니다 ($OUT.bak.*)"
  KEEP="$(cat "$OUT")"
else
  KEEP=""
fi

{
  [ -n "$KEEP" ] && { printf '%s\n\n---\n\n' "$KEEP"; }
  printf '%s\n' "$KIT_MARK"
  cat <<EOF
# potato-kit — 연구 작업 지침 (Codex)

> 이 블록은 potato-kit 이 자동 생성했다. 킷을 갱신하려면
> \`bash $KIT_DIR/install-codex.sh\` 를 다시 돌린다.
> 킷 위치: \`$KIT_DIR\`

EOF
  # 운영 규칙 전문
  awk 'NR==1 && /^# /{next} {print}' "$KIT_DIR/CLAUDE.md"

  cat <<EOF

---

## 연구 절차 파일 (요청에 따라 읽고 그대로 따른다)

Codex 에는 슬래시 스킬이 없다. 대신 **아래 파일을 직접 읽고 절차를 따른다.**
사용자가 해당 작업을 요청하면 먼저 파일을 읽고 시작한다.

| 사용자가 이렇게 말하면 | 읽을 파일 |
| --- | --- |
| "연구 시작", "처음부터 끝까지", 뭘 할지 모를 때 | \`$KIT_DIR/.claude/skills/potato-research/SKILL.md\` |
| "이 폴더 세팅", "프로젝트 만들어줘" | \`$KIT_DIR/.claude/skills/potato-start/SKILL.md\` |
| "논문 찾아줘", "선행연구" | \`$KIT_DIR/.claude/skills/potato-lit-review/SKILL.md\` |
| "이 논문 같이 읽어줘", "논문 정독하고 싶어" | \`$KIT_DIR/.claude/skills/potato-study-paper/SKILL.md\` |
| "데이터 어디서 구하지", "데이터 찾아줘" | \`$KIT_DIR/.claude/skills/potato-find-data/SKILL.md\` |
| "이 데이터 봐줘", "EDA" | \`$KIT_DIR/.claude/skills/potato-eda/SKILL.md\` |
| "모델 만들어줘", "실험 돌려줘" | \`$KIT_DIR/.claude/skills/potato-experiment/SKILL.md\` |
| "이 논문 재현해줘" | \`$KIT_DIR/.claude/skills/potato-reproduce/SKILL.md\` |
| "최적화", "스케줄 짜줘" | \`$KIT_DIR/.claude/skills/potato-optimize/SKILL.md\` |
| "보고서 써줘", "결과 정리" | \`$KIT_DIR/.claude/skills/potato-report/SKILL.md\` |
| "발표자료", "PPT" | \`$KIT_DIR/.claude/skills/potato-slides/SKILL.md\` |
| "제출 파일", 경진대회 | \`$KIT_DIR/.claude/skills/potato-submit/SKILL.md\` |
| "팩 켜줘", "무슨 팩 있어" | \`$KIT_DIR/.claude/skills/potato-add-pack/SKILL.md\` |

**주의**: 스킬 문서에 \`claude mcp add\` 가 나오면 \`codex mcp add\` 로 바꿔 실행한다.
문법은 같다 (\`codex mcp add <이름> -- <명령>\`).

## 역할 지침 (Codex 에는 서브에이전트가 없다)

Claude Code 판에는 전용 서브에이전트 4종이 있지만 Codex 에는 없다.
대신 **해당 역할이 필요한 시점에 아래 파일을 읽고 그 관점으로 직접 수행한다.**

| 역할 | 언제 | 파일 |
| --- | --- | --- |
| **방법론 감사** ★ | 모델링 후, 제출·발표 전, 결과가 너무 좋을 때 | \`$KIT_DIR/.claude/agents/methods-reviewer.md\` |
| 문헌 조사 | 논문·근거를 찾을 때 | \`$KIT_DIR/.claude/agents/literature-scout.md\` |
| 데이터 분석 | EDA·모델링 코드를 쓸 때 | \`$KIT_DIR/.claude/agents/data-analyst.md\` |
| 보고서 작성 | 결과를 문서로 옮길 때 | \`$KIT_DIR/.claude/agents/report-writer.md\` |

**감사는 별도 세션으로 도는 게 좋다.** 같은 대화에서 자기 코드를 감사하면
확증 편향이 생긴다. 가능하면 새 Codex 세션을 열어
"이 폴더의 실험을 methods-reviewer.md 관점으로 감사해줘"라고 시킨다.

## 전공 팩

\`$KIT_DIR/.claude/packs/\` 에 분야별 정의가 있다. 팩을 켜면 MCP 서버가 붙고
**그 분야의 방법론 함정 체크리스트가 활성화된다.**

medical · medical-plus · finance · libsci · ocean · industrial · korea

팩 문서의 설치 명령에서 \`claude mcp add\` → \`codex mcp add\` 로 바꿔 실행한다.
EOF
} > "$OUT.tmp" && mv "$OUT.tmp" "$OUT"

ok "AGENTS.md → $OUT ($(wc -c < "$OUT" | tr -d ' ') bytes)"

cat <<EOF

────────────────────────────────────────────────────────────
🥔  Codex 설치 완료

  확인
    codex mcp list

  시작
    cd ~/내연구폴더
    codex
    > 연구 시작할게. 무엇부터 하면 될지 물어봐줘

  ⚠️  Claude Code 판과의 차이
    · 슬래시 명령(/potato-research 등)이 없다 → 말로 요청하면 AGENTS.md 가 라우팅한다
    · 서브에이전트가 없다 → 역할 파일을 읽고 직접 수행한다
    · 감사는 새 세션에서 돌리는 것을 권한다 (확증 편향 방지)

  프로젝트 폴더에도 규칙을 두려면
    cp $KIT_DIR/CLAUDE.md ./AGENTS.md
────────────────────────────────────────────────────────────
EOF
