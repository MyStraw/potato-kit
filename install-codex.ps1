# potato-kit → Codex CLI 설치 (Windows PowerShell)
# 실행: powershell -ExecutionPolicy Bypass -File .\install-codex.ps1
#
# Claude Code 와 Codex 는 구조가 다르다:
#   Claude Code : CLAUDE.md + 슬래시 스킬 + 서브에이전트  (전부 지원)
#   Codex       : AGENTS.md + MCP                        (슬래시 스킬·서브에이전트 없음)
# 이 스크립트는 AGENTS.md 가 "언제 어느 스킬 파일을 읽을지" 알려주는 라우터가 되게 한다.

$ErrorActionPreference = "Continue"
$KitDir   = Split-Path -Parent $MyInvocation.MyCommand.Path
$CodexDir = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $HOME ".codex" }
$EnvName  = "potato"

function Say  ($m) { Write-Host "`n▶ $m" -ForegroundColor Cyan }
function OK   ($m) { Write-Host "  [OK] $m" -ForegroundColor Green }
function Warn ($m) { Write-Host "  [!]  $m" -ForegroundColor Yellow }
function Fail ($m) { Write-Host "  [X]  $m" -ForegroundColor Red }

Write-Host "`n[potato] potato-kit -> Codex CLI 설치"
Write-Host "         킷 위치: $KitDir"

# ---------------------------------------------------------------- 1. 사전 확인
Say "1/4 사전 확인"
New-Item -ItemType Directory -Force -Path $CodexDir *>$null   # 없으면 codex 가 설정 로드에 실패

if (-not (Get-Command codex -ErrorAction SilentlyContinue)) {
    Fail "Codex CLI 가 없습니다."
    Write-Host "     npm i -g @openai/codex"
    exit 1
}
OK "Codex 확인됨"

if (-not (Get-Command conda -ErrorAction SilentlyContinue)) {
    Fail "conda 가 없습니다. Miniconda 를 먼저 설치하세요."
    Write-Host "     winget install Anaconda.Miniconda3"
    exit 1
}
OK "conda 확인됨"

# ---------------------------------------------------------------- 2. 환경·패키지
Say "2/4 conda 환경 · 패키지"
$envList = conda env list 2>$null | Out-String
if ($envList -match "(?m)^$EnvName\s") {
    OK "'$EnvName' 환경이 이미 있습니다"
} else {
    conda create -n $EnvName python=3.11 -y *>$null
    if ($LASTEXITCODE -eq 0) { OK "'$EnvName' 환경 생성" } else { Fail "환경 생성 실패"; exit 1 }
}
$pkgs = "pandas numpy scipy scikit-learn matplotlib seaborn jupyterlab ipykernel python-dotenv openpyxl paper-search-mcp jupyter-mcp-server"
conda run -n $EnvName pip install -q --upgrade pip *>$null
conda run -n $EnvName pip install -q $pkgs.Split(" ") *>$null
if ($LASTEXITCODE -eq 0) { OK "패키지 설치 완료" } else { Warn "일부 패키지 설치 실패" }

# ---------------------------------------------------------------- 3. MCP 등록
Say "3/4 MCP 등록 (codex mcp add)"
codex mcp remove paper-search *>$null
codex mcp add paper-search -- conda run --no-capture-output -n $EnvName python -m paper_search_mcp.server *>$null
if ($LASTEXITCODE -eq 0) {
    OK "paper-search 등록 (arXiv·PubMed·OpenAlex 등 20+ 플랫폼)"
} else {
    Warn "paper-search 등록 실패 - 직접 실행해보세요:"
    Write-Host "     codex mcp add paper-search -- conda run --no-capture-output -n $EnvName python -m paper_search_mcp.server"
}
Write-Host "  jupyter MCP 는 주피터 서버가 떠 있어야 합니다 -> .\start-jupyter.ps1"

# ---------------------------------------------------------------- 4. AGENTS.md
Say "4/4 AGENTS.md 생성"
$Out     = Join-Path $CodexDir "AGENTS.md"
$KitMark = "<!-- potato-kit -->"
$Keep    = ""

if ((Test-Path $Out) -and -not (Select-String -Path $Out -SimpleMatch $KitMark -Quiet)) {
    Copy-Item $Out "$Out.bak.$([int][double]::Parse((Get-Date -UFormat %s)))"
    Warn "기존 AGENTS.md 를 백업했습니다"
    $Keep = (Get-Content $Out -Raw) + "`n`n---`n`n"
}

# 운영 규칙 전문 (첫 줄 H1 제거)
$rules = Get-Content (Join-Path $KitDir "CLAUDE.md")
if ($rules[0] -match '^# ') { $rules = $rules[1..($rules.Count - 1)] }
$rulesText = $rules -join "`n"

$header = @"
$KitMark
# potato-kit — 연구 작업 지침 (Codex)

> 이 블록은 potato-kit 이 자동 생성했다. 킷을 갱신하려면
> ``powershell -ExecutionPolicy Bypass -File $KitDir\install-codex.ps1`` 를 다시 돌린다.
> 킷 위치: ``$KitDir``

"@

$footer = @"

---

## 연구 절차 파일 (요청에 따라 읽고 그대로 따른다)

Codex 에는 슬래시 스킬이 없다. 대신 **아래 파일을 직접 읽고 절차를 따른다.**
사용자가 해당 작업을 요청하면 먼저 파일을 읽고 시작한다.

| 사용자가 이렇게 말하면 | 읽을 파일 |
| --- | --- |
| "연구 시작", "처음부터 끝까지", 뭘 할지 모를 때 | ``$KitDir\.claude\skills\research\SKILL.md`` |
| "이 폴더 세팅", "프로젝트 만들어줘" | ``$KitDir\.claude\skills\start\SKILL.md`` |
| "논문 찾아줘", "선행연구" | ``$KitDir\.claude\skills\lit-review\SKILL.md`` |
| "데이터 어디서 구하지", "데이터 찾아줘" | ``$KitDir\.claude\skills\find-data\SKILL.md`` |
| "이 데이터 봐줘", "EDA" | ``$KitDir\.claude\skills\eda\SKILL.md`` |
| "모델 만들어줘", "실험 돌려줘" | ``$KitDir\.claude\skills\experiment\SKILL.md`` |
| "이 논문 재현해줘" | ``$KitDir\.claude\skills\reproduce\SKILL.md`` |
| "최적화", "스케줄 짜줘" | ``$KitDir\.claude\skills\optimize\SKILL.md`` |
| "보고서 써줘", "결과 정리" | ``$KitDir\.claude\skills\report\SKILL.md`` |
| "발표자료", "PPT" | ``$KitDir\.claude\skills\slides\SKILL.md`` |
| "제출 파일", 경진대회 | ``$KitDir\.claude\skills\submit\SKILL.md`` |
| "팩 켜줘", "무슨 팩 있어" | ``$KitDir\.claude\skills\add-pack\SKILL.md`` |

**주의**: 스킬 문서에 ``claude mcp add`` 가 나오면 ``codex mcp add`` 로 바꿔 실행한다.
문법은 같다 (``codex mcp add <이름> -- <명령>``).

## 역할 지침 (Codex 에는 서브에이전트가 없다)

Claude Code 판에는 전용 서브에이전트 4종이 있지만 Codex 에는 없다.
대신 **해당 역할이 필요한 시점에 아래 파일을 읽고 그 관점으로 직접 수행한다.**

| 역할 | 언제 | 파일 |
| --- | --- | --- |
| **방법론 감사** ★ | 모델링 후, 제출·발표 전, 결과가 너무 좋을 때 | ``$KitDir\.claude\agents\methods-reviewer.md`` |
| 문헌 조사 | 논문·근거를 찾을 때 | ``$KitDir\.claude\agents\literature-scout.md`` |
| 데이터 분석 | EDA·모델링 코드를 쓸 때 | ``$KitDir\.claude\agents\data-analyst.md`` |
| 보고서 작성 | 결과를 문서로 옮길 때 | ``$KitDir\.claude\agents\report-writer.md`` |

**감사는 별도 세션으로 도는 게 좋다.** 같은 대화에서 자기 코드를 감사하면
확증 편향이 생긴다. 가능하면 새 Codex 세션을 열어
"이 폴더의 실험을 methods-reviewer.md 관점으로 감사해줘"라고 시킨다.

## 전공 팩

``$KitDir\.claude\packs\`` 에 분야별 정의가 있다. 팩을 켜면 MCP 서버가 붙고
**그 분야의 방법론 함정 체크리스트가 활성화된다.**

medical · medical-plus · finance · libsci · ocean · industrial · korea

팩 문서의 설치 명령에서 ``claude mcp add`` -> ``codex mcp add`` 로 바꿔 실행한다.
"@

($Keep + $header + $rulesText + $footer) | Set-Content $Out -Encoding UTF8
OK "AGENTS.md -> $Out"

Write-Host @"

────────────────────────────────────────────────────────────
[potato]  Codex 설치 완료

  확인
    codex mcp list

  시작
    cd ~\내연구폴더
    codex
    > 연구 시작할게. 무엇부터 하면 될지 물어봐줘

  [!] Claude Code 판과의 차이
    · 슬래시 명령(/research 등)이 없다 -> 말로 요청하면 AGENTS.md 가 라우팅한다
    · 서브에이전트가 없다 -> 역할 파일을 읽고 직접 수행한다
    · 감사는 새 세션에서 돌리는 것을 권한다 (확증 편향 방지)

  프로젝트 폴더에도 규칙을 두려면
    Copy-Item $KitDir\CLAUDE.md .\AGENTS.md
────────────────────────────────────────────────────────────
"@ -ForegroundColor White
