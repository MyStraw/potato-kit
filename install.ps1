# potato-kit 설치 (Windows PowerShell)
# 실행: powershell -ExecutionPolicy Bypass -File .\install.ps1

$ErrorActionPreference = "Continue"
$KitDir = Split-Path -Parent $MyInvocation.MyCommand.Path
# Claude Code 설정 디렉토리. CLAUDE_CONFIG_DIR 이 설정돼 있으면 그쪽을 따른다.
$ClaudeDir = if ($env:CLAUDE_CONFIG_DIR) { $env:CLAUDE_CONFIG_DIR } else { Join-Path $HOME ".claude" }
$EnvName   = "potato"

function Say  ($m) { Write-Host "`n▶ $m" -ForegroundColor Cyan }
function OK   ($m) { Write-Host "  [OK] $m"   -ForegroundColor Green }
function Warn ($m) { Write-Host "  [!]  $m"   -ForegroundColor Yellow }
function Fail ($m) { Write-Host "  [X]  $m"   -ForegroundColor Red }

Write-Host "`n[potato] potato-kit 설치를 시작합니다"
Write-Host "         킷 위치: $KitDir"

# ---------------------------------------------------------------- 1. 사전 확인
Say "1/5 사전 확인"

if (-not (Get-Command claude -ErrorAction SilentlyContinue)) {
    Fail "Claude Code가 없습니다."
    Write-Host "     https://claude.com/product/claude-code 에서 설치 후 다시 실행하세요."
    exit 1
}
OK "Claude Code 확인됨"

if (-not (Get-Command conda -ErrorAction SilentlyContinue)) {
    Fail "이 터미널에서 conda 를 찾을 수 없습니다."
    Write-Host ""
    Write-Host "  [A] conda 를 아직 설치하지 않았다면" -ForegroundColor Cyan
    Write-Host "      winget install Anaconda.Miniconda3"
    Write-Host "      또는 https://docs.conda.io/en/latest/miniconda.html"
    Write-Host ""
    Write-Host "  [B] 설치는 했는데 PowerShell/VS Code 에서 안 잡히는 경우 (가장 흔함)" -ForegroundColor Cyan
    Write-Host "      1) 관리자 PowerShell 에서 한 번:"
    Write-Host "         Set-ExecutionPolicy -Scope CurrentUser RemoteSigned"
    Write-Host "         ^ 이걸 빼먹으면 아래를 해도 계속 안 잡힙니다"
    Write-Host "      2) Anaconda Prompt 를 열고:"
    Write-Host "         conda init powershell"
    Write-Host "      3) 터미널을 완전히 닫았다 다시 열기 (VS Code 는 VS Code 자체를 재시작)"
    Write-Host ""
    Write-Host "  [C] 급하면 그냥 'Anaconda Prompt' 에서 이 스크립트를 실행하세요." -ForegroundColor Cyan
    Write-Host "      기능은 동일합니다."
    exit 1
}
OK "conda 확인됨 ($(conda --version 2>$null))"

# ---------------------------------------------------------------- 2. 환경 생성
Say "2/5 conda 환경 준비"

$envList = conda env list 2>$null | Out-String
if ($envList -match "(?m)^$EnvName\s") {
    OK "'$EnvName' 환경이 이미 있습니다"
} else {
    conda create -n $EnvName python=3.11 -y *>$null
    if ($LASTEXITCODE -eq 0) { OK "'$EnvName' 환경 생성 완료" }
    else { Fail "환경 생성 실패"; exit 1 }
}

# ---------------------------------------------------------------- 3. 패키지
Say "3/5 공통 패키지 설치 (몇 분 걸립니다)"

$CorePkgs = "pandas numpy scipy scikit-learn matplotlib seaborn jupyterlab ipykernel python-dotenv openpyxl"
$McpPkgs  = "paper-search-mcp jupyter-mcp-server"

conda run -n $EnvName pip install -q --upgrade pip *>$null

conda run -n $EnvName pip install -q $CorePkgs.Split(" ") *>$null
if ($LASTEXITCODE -eq 0) { OK "분석 라이브러리 설치 완료" }
else { Warn "일부 분석 라이브러리 설치 실패 - 나중에 개별 설치하세요" }

conda run -n $EnvName pip install -q $McpPkgs.Split(" ") *>$null
if ($LASTEXITCODE -eq 0) { OK "MCP 서버 패키지 설치 완료" }
else { Warn "MCP 패키지 설치 실패 - Claude에게 '설치 실패했어'라고 말하면 도와줍니다" }

# ---------------------------------------------------------------- 4. MCP 등록
Say "4/5 공통 코어 MCP 등록 (유저 스코프)"

claude mcp remove paper-search *>$null

claude mcp add -s user paper-search -- conda run --no-capture-output -n $EnvName python -m paper_search_mcp.server *>$null
if ($LASTEXITCODE -eq 0) {
    OK "paper-search 등록 완료 (논문 검색: arXiv, PubMed 등)"
} else {
    Warn "paper-search 등록 실패 - 아래 명령을 직접 실행해보세요:"
    Write-Host "     claude mcp add -s user paper-search -- conda run --no-capture-output -n $EnvName python -m paper_search_mcp.server"
}

Write-Host ""
Write-Host "  jupyter MCP는 주피터 서버가 떠 있어야 연결됩니다."
Write-Host "  분석을 시작할 때 '.\start-jupyter.ps1' 를 먼저 실행하세요."

# ---------------------------------------------------------------- 5. 자산 복사
Say "5/5 스킬·에이전트·팩 설치"

Write-Host "  설치 위치: $ClaudeDir"
if ($env:CLAUDE_CONFIG_DIR) { Write-Host "  (CLAUDE_CONFIG_DIR 환경변수를 따름)" }

foreach ($d in @("skills", "agents", "packs")) {
    $dest = Join-Path $ClaudeDir $d
    New-Item -ItemType Directory -Force -Path $dest *>$null
    $src = Join-Path $KitDir ".claude\$d"
    if (Test-Path $src) {
        Copy-Item -Path "$src\*" -Destination $dest -Recurse -Force -ErrorAction SilentlyContinue
        OK "$d -> $dest\"
    }
}

Copy-Item -Path (Join-Path $KitDir "CLAUDE.md") `
          -Destination (Join-Path $ClaudeDir "potato-kit-rules.md") -Force -ErrorAction SilentlyContinue
OK "운영 규칙 -> $ClaudeDir\potato-kit-rules.md"

# 상태줄 스크립트 (화면 아래 계정·모델·컨텍스트·사용량 표시)
$SlPath = Join-Path $ClaudeDir "potato-statusline.ps1"
Copy-Item -Path (Join-Path $KitDir ".claude\statusline\potato-statusline.ps1") `
          -Destination $SlPath -Force -ErrorAction SilentlyContinue
if (Test-Path $SlPath) { OK "상태줄 스크립트 -> $SlPath" }

# settings.json:
#  - 기본 모델을 sonnet 으로 (Pro 구독은 Opus 를 쓸 수 없고, Sonnet 이 한도도 오래간다)
#  - 상태줄(statusLine) 등록
# 이미 설정된 키는 건드리지 않는다.
$SettingsPath = Join-Path $ClaudeDir "settings.json"
try {
    # -AsHashtable 은 PowerShell 6+ 전용이라 쓰지 않는다 (Windows 기본은 5.1)
    $cfg = $null
    if ((Test-Path $SettingsPath) -and ((Get-Item $SettingsPath).Length -gt 0)) {
        $cfg = Get-Content $SettingsPath -Raw -Encoding UTF8 | ConvertFrom-Json
    }
    if ($null -eq $cfg) { $cfg = New-Object PSObject }
    $changed = $false

    if ($cfg.PSObject.Properties.Name -contains "model") {
        OK "기본 모델 = 기존 설정 유지 ($($cfg.model))"
    } else {
        $cfg | Add-Member -NotePropertyName model -NotePropertyValue "sonnet" -Force
        $changed = $true
        OK "기본 모델 = sonnet (Pro 구독에 맞춤)"
    }

    if ($cfg.PSObject.Properties.Name -contains "statusLine") {
        OK "상태줄 = 기존 설정 유지 (바꾸려면 /potato-statusline)"
    } elseif (Test-Path $SlPath) {
        # Git Bash 가 있으면 상태줄 명령이 Git Bash 로 실행되므로 경로는 슬래시로 쓴다
        $slFwd = $SlPath -replace '\\', '/'
        $sl = New-Object PSObject
        $sl | Add-Member -NotePropertyName type -NotePropertyValue "command"
        $sl | Add-Member -NotePropertyName command `
              -NotePropertyValue "powershell -NoProfile -ExecutionPolicy Bypass -File `"$slFwd`""
        $cfg | Add-Member -NotePropertyName statusLine -NotePropertyValue $sl -Force
        $changed = $true
        OK "상태줄 등록 완료 (재시작하면 화면 아래에 나타납니다)"
    }

    if ($changed) {
        $json = $cfg | ConvertTo-Json -Depth 20
        # BOM 없는 UTF-8 로 쓴다 (Set-Content -Encoding UTF8 은 5.1 에서 BOM 을 붙여
        # JSON 파서가 못 읽을 수 있다)
        [System.IO.File]::WriteAllText($SettingsPath, $json, (New-Object System.Text.UTF8Encoding $false))
    }
} catch {
    Warn "settings.json 자동 설정 실패 - Claude Code 에서 '/model sonnet' 을 직접 실행하세요"
}

# ---------------------------------------------------------------- 끝
Write-Host @"

────────────────────────────────────────────────────────────
[potato]  설치 완료

  다음 단계
  ─────────
  1. Claude Code를 껐다 켜세요 (MCP는 시작할 때 연결됩니다)
  2. 확인:            claude mcp list
  3. 전공 팩 켜기:     /potato-add-pack list
  4. 사용법 읽기:      GUIDE.md  <- 페르소나별 사용 시나리오

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
"@ -ForegroundColor White
