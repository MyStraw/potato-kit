#!/usr/bin/env python3
"""potato-kit 상태줄 (macOS / Linux).

Claude Code 가 settings.json 의 statusLine 설정으로 이 스크립트를 호출하고,
stdin 으로 세션 정보 JSON 을 준다. 여기서 출력한 줄들이 화면 아래
상태줄이 된다. 출력 형식을 바꾸고 싶으면 이 파일을 고치면 된다.

표시 (세 줄):
  🥔 계정 | 폴더 (브랜치)
  모델 | 컨텍스트 %
  사용량 5h·7d % | +줄/-줄
"""
import json, os, sys

RESET, DIM, BOLD = "\033[0m", "\033[2m", "\033[1m"
SEP = f" {DIM}|{RESET} "


def usage_color(pct):
    """사용률 색: 50% 미만 초록, 80% 미만 노랑, 그 이상 빨강."""
    if pct is None:
        return DIM
    return "\033[32m" if pct < 50 else ("\033[33m" if pct < 80 else "\033[31m")


try:
    d = json.load(sys.stdin)
except Exception:
    print("🥔")
    sys.exit(0)

line1, line2, line3 = [], [], []

# 1) 로그인 계정 — .claude.json 의 oauthAccount 에서 (없으면 조용히 생략)
try:
    cfg_dir = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.expanduser("~/.claude")
    for p in (os.path.join(cfg_dir, ".claude.json"), os.path.expanduser("~/.claude.json")):
        if os.path.isfile(p):
            email = (json.load(open(p, encoding="utf-8")).get("oauthAccount") or {}).get("emailAddress")
            if email:
                line1.append(f"{DIM}{email}{RESET}")
                break
except Exception:
    pass

# 2) 폴더 이름 + git 브랜치 (.git/HEAD 를 직접 읽는다 — git 실행보다 빠르다)
cwd = (d.get("workspace") or {}).get("current_dir") or d.get("cwd") or ""
name = os.path.basename(cwd.rstrip(os.sep)) or cwd
branch = ""
try:
    p = cwd
    for _ in range(6):  # 상위로 최대 6단계까지 저장소 루트를 찾는다
        head = os.path.join(p, ".git", "HEAD")
        if os.path.isfile(head):
            ref = open(head, encoding="utf-8").read().strip()
            branch = ref.rsplit("/", 1)[-1] if ref.startswith("ref:") else ref[:8]
            break
        parent = os.path.dirname(p)
        if parent == p:
            break
        p = parent
except Exception:
    pass
line1.append(f"📁 {name}" + (f" {DIM}({branch}){RESET}" if branch else ""))

# 3) 모델
model = (d.get("model") or {}).get("display_name") or "?"
line2.append(f"{BOLD}{model}{RESET}")

# 4) 컨텍스트 사용률 (첫 응답 전에는 null 이라 생략된다)
pct = (d.get("context_window") or {}).get("used_percentage")
if pct is not None:
    line2.append(f"컨텍스트 {usage_color(pct)}{round(pct)}%{RESET}")

# 5) 구독 사용량 — Pro/Max 구독일 때만 온다 (5시간 / 7일 한도)
rl = d.get("rate_limits") or {}
parts = []
for key, label in (("five_hour", "5h"), ("seven_day", "7d")):
    u = (rl.get(key) or {}).get("used_percentage")
    if u is not None:
        parts.append(f"{label} {usage_color(u)}{round(u)}%{RESET}")
if parts:
    line3.append("사용량 " + " · ".join(parts))

# 6) 이 세션에서 고친 코드 줄 수
cost = d.get("cost") or {}
la, lr = cost.get("total_lines_added") or 0, cost.get("total_lines_removed") or 0
if la or lr:
    line3.append(f"\033[32m+{la}{RESET}/\033[31m-{lr}{RESET}")

print("🥔 " + SEP.join(line1))
if line2:
    print(SEP.join(line2))
if line3:
    print(SEP.join(line3))
