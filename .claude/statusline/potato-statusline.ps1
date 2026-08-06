# potato-kit 상태줄 (Windows).
#
# Claude Code 가 settings.json 의 statusLine 설정으로 이 스크립트를 호출하고,
# stdin 으로 세션 정보 JSON 을 준다. 여기서 출력한 한 줄이 화면 아래 상태줄이 된다.
# 출력 형식을 바꾸고 싶으면 이 파일을 고치면 된다.
#
# 표시: [potato] 계정 | 폴더 (브랜치) | 모델 | 컨텍스트 % | 사용량 5h·7d % | +줄/-줄

try {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    [Console]::InputEncoding  = [System.Text.Encoding]::UTF8
} catch {}

$raw = [Console]::In.ReadToEnd()
try { $d = $raw | ConvertFrom-Json } catch { Write-Output "🥔"; exit 0 }

$e = [char]27
$RESET = "$e[0m"; $DIM = "$e[2m"; $BOLD = "$e[1m"

function UsageColor($p) {
    if ($null -eq $p) { return $DIM }
    if ($p -lt 50) { return "$e[32m" } elseif ($p -lt 80) { return "$e[33m" } else { return "$e[31m" }
}

$seg = @()

# 1) 로그인 계정 — .claude.json 의 oauthAccount 에서 (없으면 조용히 생략)
try {
    $cfgDir = if ($env:CLAUDE_CONFIG_DIR) { $env:CLAUDE_CONFIG_DIR } else { Join-Path $HOME ".claude" }
    foreach ($p in @((Join-Path $cfgDir ".claude.json"), (Join-Path $HOME ".claude.json"))) {
        if (Test-Path $p) {
            $acct = (Get-Content $p -Raw -Encoding UTF8 | ConvertFrom-Json).oauthAccount
            if ($acct -and $acct.emailAddress) { $seg += "$DIM$($acct.emailAddress)$RESET"; break }
        }
    }
} catch {}

# 2) 폴더 이름 + git 브랜치 (.git/HEAD 를 직접 읽는다 — git 실행보다 빠르다)
$cwd = $d.workspace.current_dir
if (-not $cwd) { $cwd = $d.cwd }
$name = Split-Path $cwd -Leaf
$branch = ""
try {
    $p = $cwd
    for ($i = 0; $i -lt 6 -and $p; $i++) {
        $head = Join-Path $p ".git\HEAD"
        if (Test-Path $head) {
            $ref = (Get-Content $head -Raw -Encoding UTF8).Trim()
            if ($ref.StartsWith("ref:")) { $branch = $ref.Split("/")[-1] }
            else { $branch = $ref.Substring(0, 8) }
            break
        }
        $p = Split-Path $p -Parent
    }
} catch {}
$dirseg = "📁 $name"
if ($branch) { $dirseg += " $DIM($branch)$RESET" }
$seg += $dirseg

# 3) 모델
$seg += "$BOLD$($d.model.display_name)$RESET"

# 4) 컨텍스트 사용률 (첫 응답 전에는 null 이라 생략된다)
$pct = $d.context_window.used_percentage
if ($null -ne $pct) {
    $seg += ("컨텍스트 " + (UsageColor $pct) + [math]::Round($pct) + "%$RESET")
}

# 5) 구독 사용량 — Pro/Max 구독일 때만 온다 (5시간 / 7일 한도)
$parts = @()
$u5 = $d.rate_limits.five_hour.used_percentage
if ($null -ne $u5) { $parts += ("5h " + (UsageColor $u5) + [math]::Round($u5) + "%$RESET") }
$u7 = $d.rate_limits.seven_day.used_percentage
if ($null -ne $u7) { $parts += ("7d " + (UsageColor $u7) + [math]::Round($u7) + "%$RESET") }
if ($parts.Count -gt 0) { $seg += ("사용량 " + ($parts -join " · ")) }

# 6) 이 세션에서 고친 코드 줄 수
$la = $d.cost.total_lines_added
$lr = $d.cost.total_lines_removed
if ($la -or $lr) {
    if (-not $la) { $la = 0 }; if (-not $lr) { $lr = 0 }
    $seg += "$e[32m+$la$RESET/$e[31m-$lr$RESET"
}

Write-Output ("🥔 " + ($seg -join " $DIM|$RESET "))
