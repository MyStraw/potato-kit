# 주피터 서버를 띄우고 jupyter MCP를 연결한다 (Windows)
# 실행: powershell -ExecutionPolicy Bypass -File .\start-jupyter.ps1

param([int]$Port = 8888)

$EnvName = "potato"
$Token   = -join ((1..32) | ForEach-Object { "{0:x}" -f (Get-Random -Max 16) })

Write-Host "[potato] 주피터 서버를 시작합니다 (포트 $Port)" -ForegroundColor Cyan

$job = Start-Job -ScriptBlock {
    param($EnvName, $Port, $Token)
    conda run --no-capture-output -n $EnvName `
        jupyter lab --no-browser --port=$Port `
        --IdentityProvider.token=$Token `
        --ServerApp.disable_check_xsrf=True
} -ArgumentList $EnvName, $Port, $Token

Start-Sleep -Seconds 5

if ($job.State -eq "Failed") {
    Write-Host "[X] 주피터 시작 실패" -ForegroundColor Red
    Write-Host "    conda run -n $EnvName pip install jupyterlab 로 설치를 확인하세요."
    exit 1
}

claude mcp remove jupyter *>$null

claude mcp add -s user jupyter `
    -e "JUPYTER_URL=http://127.0.0.1:$Port" `
    -e "JUPYTER_TOKEN=$Token" `
    -e "ALLOW_IMG_OUTPUT=true" `
    -- conda run --no-capture-output -n $EnvName jupyter-mcp-server *>$null

if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] jupyter MCP 등록 완료" -ForegroundColor Green
} else {
    Write-Host "[!] jupyter MCP 등록 실패 - Claude에게 알려주면 도와줍니다" -ForegroundColor Yellow
}

Write-Host @"

  주피터:  http://127.0.0.1:$Port/lab?token=$Token
  중지:    Stop-Job -Id $($job.Id)  또는 이 창 닫기

  [!] Claude Code를 껐다 켜야 MCP가 연결됩니다.

"@

Receive-Job -Job $job -Wait
