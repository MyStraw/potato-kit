# potato-kit -> Codex installer (Windows PowerShell 5.1+)
# Run: powershell -ExecutionPolicy Bypass -File .\install-codex.ps1
[CmdletBinding()]
param(
    [string]$CodexHome = $(if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $HOME ".codex" }),
    [string]$SkillsHome = $(Join-Path $HOME ".agents\skills"),
    [switch]$SkipEnvironment,
    [switch]$SkipMcp
)

$ErrorActionPreference = "Stop"
$KitDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$EnvName = "potato"
$env:CODEX_HOME = $CodexHome

function Say  ($m) { Write-Host "`n> $m" -ForegroundColor Cyan }
function OK   ($m) { Write-Host "  [OK] $m" -ForegroundColor Green }
function Warn ($m) { Write-Host "  [!]  $m" -ForegroundColor Yellow }
function Fail ($m) { Write-Host "  [X]  $m" -ForegroundColor Red }

Write-Host "`n[potato] potato-kit -> native Codex install"
Write-Host "         kit: $KitDir"

# ---------------------------------------------------------------- 1. Prerequisites
Say "1/5 prerequisites"
New-Item -ItemType Directory -Force -Path $CodexHome | Out-Null

if (-not (Get-Command codex -ErrorAction SilentlyContinue)) {
    Fail "Codex CLI is not installed."
    Write-Host "     npm i -g @openai/codex"
    exit 1
}
OK "Codex: $(codex --version)"

if (-not $SkipEnvironment) {
    if (-not (Get-Command conda -ErrorAction SilentlyContinue)) {
        Fail "conda is not installed. Install Miniconda first."
        exit 1
    }
    OK "conda: $(conda --version)"
} elseif (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Fail "-SkipEnvironment validation requires the python command."
    exit 1
}

# ---------------------------------------------------------------- 2. Environment and packages
Say "2/5 conda environment and packages"
if ($SkipEnvironment) {
    Warn "skipping environment and package installation"
} else {
    $envList = conda env list 2>$null | Out-String
    if ($envList -match "(?m)^$EnvName\s") {
        OK "'$EnvName' environment already exists"
    } else {
        conda create -n $EnvName python=3.11 -y
        if ($LASTEXITCODE -ne 0) { Fail "environment creation failed"; exit 1 }
        OK "created '$EnvName' environment"
    }

    $pkgs = @(
        "pandas", "numpy", "scipy", "scikit-learn", "matplotlib", "seaborn",
        "jupyterlab", "ipykernel", "python-dotenv", "openpyxl",
        "paper-search-mcp", "jupyter-mcp-server"
    )
    conda run -n $EnvName python -m pip install -q --upgrade pip
    if ($LASTEXITCODE -ne 0) { Fail "pip upgrade failed"; exit 1 }
    conda run -n $EnvName python -m pip install -q $pkgs
    if ($LASTEXITCODE -ne 0) { Fail "package installation failed"; exit 1 }
    OK "installed analysis and MCP packages"
}

# ---------------------------------------------------------------- 3. MCP registration
Say "3/5 MCP registration"
if ($SkipMcp) {
    Warn "skipping MCP registration"
} else {
    $previousErrorPreference = $ErrorActionPreference
    $ErrorActionPreference = "SilentlyContinue"
    codex mcp get paper-search --json *>$null
    $paperSearchExists = ($LASTEXITCODE -eq 0)
    $ErrorActionPreference = $previousErrorPreference
    if ($paperSearchExists) {
        OK "preserved existing paper-search MCP configuration"
    } else {
        codex mcp add paper-search -- conda run --no-capture-output -n $EnvName python -m paper_search_mcp.server
        if ($LASTEXITCODE -ne 0) { Fail "paper-search MCP registration failed"; exit 1 }
        OK "registered paper-search MCP"
    }
}
Write-Host "  jupyter MCP requires a running server -> .\start-jupyter.ps1"

# ---------------------------------------------------------------- 4. Native Codex assets
Say "4/5 native Codex skills, agents, and guidance"
$Helper = Join-Path $KitDir "scripts\install_codex_assets.py"
$helperArgs = @(
    $Helper,
    "--kit-dir", $KitDir,
    "--codex-home", $CodexHome,
    "--skills-home", $SkillsHome
)

if ($SkipEnvironment) {
    python @helperArgs
} else {
    conda run --no-capture-output -n $EnvName python @helperArgs
}
if ($LASTEXITCODE -ne 0) { Fail "Codex asset installation failed"; exit 1 }

OK "13 skills -> $SkillsHome"
OK "4 custom agents -> $(Join-Path $CodexHome 'agents')"
OK "global guidance -> $(Join-Path $CodexHome 'AGENTS.md')"

# ---------------------------------------------------------------- 5. Verification
Say "5/5 verification"
$requiredSkills = @(
    "potato-research", "potato-start", "potato-lit-review", "potato-find-data",
    "potato-eda", "potato-experiment", "potato-reproduce", "potato-optimize",
    "potato-report", "potato-slides", "potato-submit", "potato-add-pack",
    "potato-statusline"
)
$missingSkills = $requiredSkills | Where-Object {
    -not (Test-Path (Join-Path $SkillsHome "$_\SKILL.md"))
}
$agentCount = (Get-ChildItem (Join-Path $CodexHome "agents") -Filter "*.toml" -ErrorAction SilentlyContinue | Measure-Object).Count

if ($missingSkills.Count -gt 0) {
    Fail "missing skills: $($missingSkills -join ', ')"
    exit 1
}
if ($agentCount -lt 4) {
    Fail "fewer than 4 custom agents were installed"
    exit 1
}
OK "verified 13 skills and $agentCount agents"

Write-Host @"

------------------------------------------------------------
[potato] Codex install complete

  Restart the Codex app/CLI so it loads the new skills and agents.

  Verify
    codex mcp list
    Invoke `$potato-research or ask Codex to start a research workflow.

  Status line
    Run /statusline in Codex CLI.

  Methodology audit
    Ask Codex to delegate the audit to the methods-reviewer agent.
------------------------------------------------------------
"@ -ForegroundColor White
