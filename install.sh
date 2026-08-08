#!/usr/bin/env bash
# potato-kit 설치 (macOS / Linux)
set -uo pipefail

KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Claude Code 설정 디렉토리. CLAUDE_CONFIG_DIR 이 설정돼 있으면 그쪽을 따른다.
# (하드코딩하면 커스텀 설정 디렉토리를 쓰는 사람에게 엉뚱한 곳에 설치된다)
CLAUDE_DIR="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
ENV_NAME="potato"

say()  { printf "\n\033[1;36m▶ %s\033[0m\n" "$1"; }
ok()   { printf "  \033[32m✓\033[0m %s\n" "$1"; }
warn() { printf "  \033[33m!\033[0m %s\n" "$1"; }
fail() { printf "  \033[31m✗\033[0m %s\n" "$1"; }

echo "🥔 potato-kit 설치를 시작합니다"
echo "   킷 위치: $KIT_DIR"

# ---------------------------------------------------------------- 1. 사전 확인
say "1/5 사전 확인"

if ! command -v claude >/dev/null 2>&1; then
  fail "Claude Code가 없습니다."
  echo "     https://claude.com/product/claude-code 에서 설치 후 다시 실행하세요."
  exit 1
fi
ok "Claude Code: $(claude --version 2>/dev/null | head -1)"

if ! command -v conda >/dev/null 2>&1; then
  fail "conda가 없습니다."
  echo ""
  echo "  Miniconda를 설치하세요:"
  echo "    macOS (Apple Silicon):"
  echo "      curl -o mc.sh https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-arm64.sh"
  echo "      bash mc.sh -b -p \$HOME/miniconda3 && \$HOME/miniconda3/bin/conda init zsh"
  echo "    macOS (Intel): MacOSX-x86_64.sh"
  echo "    Linux:         Linux-x86_64.sh"
  echo ""
  echo "  설치 후 터미널을 새로 열고 이 스크립트를 다시 실행하세요."
  exit 1
fi
ok "conda: $(conda --version)"

# ---------------------------------------------------------------- 2. 환경 생성
say "2/5 conda 환경 준비"

if conda env list | grep -qE "^${ENV_NAME}\s"; then
  ok "'$ENV_NAME' 환경이 이미 있습니다"
else
  conda create -n "$ENV_NAME" python=3.11 -y >/dev/null 2>&1 \
    && ok "'$ENV_NAME' 환경 생성 완료" \
    || { fail "환경 생성 실패"; exit 1; }
fi

# ---------------------------------------------------------------- 3. 패키지
say "3/5 공통 패키지 설치 (몇 분 걸립니다)"

CORE_PKGS="pandas numpy scipy scikit-learn matplotlib seaborn jupyterlab ipykernel python-dotenv openpyxl"
MCP_PKGS="paper-search-mcp jupyter-mcp-server"

conda run -n "$ENV_NAME" pip install -q --upgrade pip >/dev/null 2>&1
conda run -n "$ENV_NAME" pip install -q $CORE_PKGS >/dev/null 2>&1 \
  && ok "분석 라이브러리 설치 완료" \
  || warn "일부 분석 라이브러리 설치 실패 — 나중에 개별 설치하세요"

conda run -n "$ENV_NAME" pip install -q $MCP_PKGS >/dev/null 2>&1 \
  && ok "MCP 서버 패키지 설치 완료" \
  || warn "MCP 패키지 설치 실패 — Claude에게 '설치 실패했어'라고 말하면 도와줍니다"

# ---------------------------------------------------------------- 4. MCP 등록
say "4/5 공통 코어 MCP 등록 (유저 스코프)"

# 기존 등록이 있으면 지우고 다시 (멱등성)
claude mcp remove paper-search >/dev/null 2>&1 || true

if claude mcp add -s user paper-search -- \
     conda run --no-capture-output -n "$ENV_NAME" python -m paper_search_mcp.server >/dev/null 2>&1; then
  ok "paper-search 등록 완료 (논문 검색: arXiv, PubMed 등)"
else
  warn "paper-search 등록 실패 — 아래 명령을 직접 실행해보세요:"
  echo "     claude mcp add -s user paper-search -- conda run --no-capture-output -n $ENV_NAME python -m paper_search_mcp.server"
fi

echo ""
echo "  jupyter MCP는 주피터 서버가 떠 있어야 연결됩니다."
echo "  분석을 시작할 때 './start-jupyter.sh' 를 먼저 실행하세요."

# ---------------------------------------------------------------- 5. 자산 복사
say "5/5 스킬·에이전트·팩 설치"

echo "  설치 위치: $CLAUDE_DIR"
[ -n "${CLAUDE_CONFIG_DIR:-}" ] && echo "  (CLAUDE_CONFIG_DIR 환경변수를 따름)"

mkdir -p "$CLAUDE_DIR"/{skills,agents,packs}

copy_dir() {  # $1=src subdir, $2=label
  if [ -d "$KIT_DIR/.claude/$1" ]; then
    cp -R "$KIT_DIR/.claude/$1/." "$CLAUDE_DIR/$1/" 2>/dev/null \
      && ok "$2 → $CLAUDE_DIR/$1/" \
      || warn "$2 복사 실패"
  fi
}

copy_dir skills "스킬 14종"
copy_dir agents "서브에이전트 4종"
copy_dir packs  "전공 팩 7종"

# 운영 규칙은 덮어쓰지 않고 별도 파일로 둔다
cp "$KIT_DIR/CLAUDE.md" "$CLAUDE_DIR/potato-kit-rules.md" 2>/dev/null \
  && ok "운영 규칙 → $CLAUDE_DIR/potato-kit-rules.md"

# 상태줄 스크립트 (화면 아래 계정·모델·컨텍스트·사용량 표시)
cp "$KIT_DIR/.claude/statusline/potato-statusline.py" "$CLAUDE_DIR/potato-statusline.py" 2>/dev/null \
  && ok "상태줄 스크립트 → $CLAUDE_DIR/potato-statusline.py"

# settings.json:
#  - 기본 모델을 sonnet 으로 (Pro 구독은 Opus 를 쓸 수 없고, Sonnet 이 한도도 오래간다)
#  - 상태줄(statusLine) 등록
# 이미 설정된 키는 건드리지 않는다.
SETTINGS="$CLAUDE_DIR/settings.json"
SETTINGS_RESULT="$(python3 - "$SETTINGS" "$CLAUDE_DIR/potato-statusline.py" 2>/dev/null <<'PY'
import json, os, sys
p, sl_script = sys.argv[1], sys.argv[2]
try:
    cfg = json.load(open(p, encoding="utf-8")) if os.path.exists(p) and os.path.getsize(p) else {}
    assert isinstance(cfg, dict)
except Exception:
    print("INVALID"); raise SystemExit(0)
changed = False
if "model" in cfg:
    print("MODEL_KEEP:" + str(cfg["model"]))
else:
    cfg["model"] = "sonnet"; changed = True
    print("MODEL_SET")
if "statusLine" in cfg:
    print("SL_KEEP")
else:
    cfg["statusLine"] = {"type": "command", "command": 'python3 "%s"' % sl_script}
    changed = True
    print("SL_SET")
if changed:
    os.makedirs(os.path.dirname(p), exist_ok=True)
    json.dump(cfg, open(p, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
PY
)"
case "$SETTINGS_RESULT" in
  INVALID|"") warn "settings.json 을 읽을 수 없습니다 — Claude Code 에서 '/model sonnet' 을 직접 실행하세요" ;;
  *)
    case "$SETTINGS_RESULT" in *MODEL_SET*) ok "기본 모델 = sonnet (Pro 구독에 맞춤)" ;;
      *) ok "기본 모델 = 기존 설정 유지 ($(printf '%s' "$SETTINGS_RESULT" | sed -n 's/^MODEL_KEEP://p'))" ;; esac
    case "$SETTINGS_RESULT" in *SL_SET*) ok "상태줄 등록 완료 (재시작하면 화면 아래에 나타납니다)" ;;
      *) ok "상태줄 = 기존 설정 유지 (바꾸려면 /potato-statusline)" ;; esac
    ;;
esac

# ---------------------------------------------------------------- 끝
cat <<EOF

────────────────────────────────────────────────────────────
🥔  설치 완료

  다음 단계
  ─────────
  1. Claude Code를 껐다 켜세요 (MCP는 시작할 때 연결됩니다)
  2. 확인:            claude mcp list
  3. 전공 팩 켜기:     /potato-add-pack list
  4. 사용법 읽기:      GUIDE.md  ← 페르소나별 사용 시나리오

  스킬은 유저 스코프로 설치되어 **어느 폴더에서든** 동작합니다.

  전공 팩 예시
  ─────────
    /potato-add-pack medical      의료·약학  (PubMed, 임상시험, OpenFDA)
    /potato-add-pack finance      금융·시계열
    /potato-add-pack libsci       문헌정보·계량서지
    /potato-add-pack ocean        해양·환경
    /potato-add-pack industrial   산업공학·최적화
    /potato-add-pack korea        한국 공공데이터
    /potato-add-pack new <분야>    목록에 없는 전공이면 새로 만들기
────────────────────────────────────────────────────────────
EOF
