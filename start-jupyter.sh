#!/usr/bin/env bash
# 주피터 서버를 띄우고 jupyter MCP를 연결한다 (macOS / Linux)
set -uo pipefail

ENV_NAME="potato"
PORT="${1:-8888}"
TOKEN="$(python3 -c 'import secrets; print(secrets.token_hex(16))' 2>/dev/null || echo "potatokit$RANDOM")"

echo "🥔 주피터 서버를 시작합니다 (포트 $PORT)"

conda run --no-capture-output -n "$ENV_NAME" \
  jupyter lab --no-browser --port="$PORT" \
  --IdentityProvider.token="$TOKEN" \
  --ServerApp.disable_check_xsrf=True &

JUPYTER_PID=$!
sleep 4

if ! kill -0 "$JUPYTER_PID" 2>/dev/null; then
  echo "✗ 주피터 시작 실패. 'conda run -n $ENV_NAME pip install jupyterlab' 로 설치를 확인하세요."
  exit 1
fi

claude mcp remove jupyter >/dev/null 2>&1 || true
claude mcp add -s user jupyter \
  -e "JUPYTER_URL=http://127.0.0.1:$PORT" \
  -e "JUPYTER_TOKEN=$TOKEN" \
  -e "ALLOW_IMG_OUTPUT=true" \
  -- conda run --no-capture-output -n "$ENV_NAME" jupyter-mcp-server >/dev/null 2>&1 \
  && echo "✓ jupyter MCP 등록 완료" \
  || echo "! jupyter MCP 등록 실패 — Claude에게 알려주면 도와줍니다"

cat <<EOF

  주피터:  http://127.0.0.1:$PORT/lab?token=$TOKEN
  중지:    Ctrl+C

  ⚠️  Claude Code를 껐다 켜야 MCP가 연결됩니다.

EOF

wait "$JUPYTER_PID"
