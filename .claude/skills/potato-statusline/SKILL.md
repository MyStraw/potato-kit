---
name: potato-statusline
description: 터미널 아래에 상태줄(로그인 계정·폴더·브랜치·모델·컨텍스트·구독 사용량)을 설치하거나 끈다. "상태줄 켜줘", "아래에 사용량 보이게 해줘", "상태줄 바꿔줘/꺼줘" 같은 요청에 사용한다.
---

# /potato-statusline — 상태줄 설치·해제

```
/potato-statusline           ← 설치 (이미 있으면 상태 보여주기)
/potato-statusline off       ← 끄기
/potato-statusline 커스텀    ← 표시 항목 바꾸기
```

## 이게 뭔가

Claude Code 화면 맨 아래에 한 줄로 세션 정보를 상시 표시한다:

```
🥔 potato@gmail.com | 📁 my-project (main) | Sonnet | 컨텍스트 34% | 사용량 5h 24% · 7d 41% | +156/-23
```

- **사용량 5h · 7d** — Pro 구독의 5시간/7일 한도를 몇 % 썼는지. **한도 관리에 제일 유용하다**
- **컨텍스트 %** — 대화가 얼마나 찼는지. 80%쯤 되면 새 세션을 여는 게 낫다
- 색: 초록(<50%) → 노랑(<80%) → 빨강(80%+)

`install.sh` / `install.ps1` 이 **자동으로 설치**하므로 보통은 이 스킬을 부를 일이
없다. 킷을 예전에 설치했거나, 껐다 다시 켜거나, 표시 항목을 바꿀 때 쓴다.

## 구조 — 두 부분

1. **스크립트**: `<설정폴더>/potato-statusline.py` (macOS/Linux) 또는 `.ps1` (Windows).
   원본은 킷의 `.claude/statusline/` 에 있다. Claude Code 가 stdin 으로 세션 정보
   JSON 을 주면 이 스크립트가 한 줄을 출력한다.
2. **settings.json 의 `statusLine` 항목**: 어떤 명령을 실행할지 지정.

`<설정폴더>` = `$CLAUDE_CONFIG_DIR` 이 있으면 그 값, 없으면 `~/.claude`.

## 설치 절차 (Claude 가 수행)

1. **기존 statusLine 확인.** `settings.json` 에 이미 `statusLine` 이 있으면
   덮어쓰지 말고 사용자에게 보여주고 물어본다 — 다른 도구의 상태줄일 수 있다.
2. **스크립트 복사.** 킷의 `.claude/statusline/` 에서 OS 에 맞는 파일을
   `<설정폴더>/` 로 복사한다. 킷 폴더를 못 찾으면
   github.com/MyStraw/potato-kit 의 `.claude/statusline/` 에서 받는다.
3. **settings.json 에 추가.** 다른 키는 절대 건드리지 않는다:

   macOS / Linux:
   ```json
   "statusLine": { "type": "command", "command": "python3 \"/Users/<계정>/.claude/potato-statusline.py\"" }
   ```

   Windows — **경로는 반드시 슬래시(`/`)로** 쓴다. Git Bash 가 설치돼 있으면
   상태줄 명령이 Git Bash 로 실행되는데, 역슬래시 경로는 거기서 깨진다:
   ```json
   "statusLine": { "type": "command", "command": "powershell -NoProfile -ExecutionPolicy Bypass -File \"C:/Users/<계정>/.claude/potato-statusline.ps1\"" }
   ```
4. **동작 확인.** 실제 stdin 형식으로 테스트한다:
   ```bash
   echo '{"cwd":"/tmp","model":{"display_name":"Sonnet"},"workspace":{"current_dir":"/tmp"},"context_window":{"used_percentage":34}}' | python3 <설정폴더>/potato-statusline.py
   ```
   `🥔` 로 시작하는 한 줄이 나오면 성공.
5. **재시작 안내.** "Claude Code 를 껐다 켜면 아래에 상태줄이 나타납니다."

## 끄기

`settings.json` 에서 `statusLine` 키만 삭제한다. 스크립트 파일은 놔둬도 된다
(다시 켤 때 재사용).

## 커스텀

표시 항목을 바꾸려면 스크립트를 직접 고친다. 각 항목이 `# 1) ~ # 6)` 주석으로
구분돼 있어서 지우거나 순서를 바꾸면 된다. 활용할 수 있는 stdin 필드:

| 필드 | 내용 |
| --- | --- |
| `model.display_name` | 모델 이름 |
| `workspace.current_dir` | 현재 폴더 |
| `context_window.used_percentage` | 컨텍스트 사용률 (첫 응답 전 null) |
| `rate_limits.five_hour/.seven_day.used_percentage` | 구독 사용량 (Pro/Max 만) |
| `cost.total_lines_added/removed` | 이 세션에서 고친 줄 수 |
| `cost.total_cost_usd` | API 환산 비용 (구독이면 참고용) |

## 문제가 생기면

| 증상 | 원인·해결 |
| --- | --- |
| 상태줄이 안 나온다 | Claude Code 재시작을 안 했다. 껐다 켜기 |
| `🥔` 만 나온다 | 스크립트가 JSON 파싱에 실패했다 — 정상 폴백. 계속 그러면 스크립트 경로 확인 |
| 한글이 깨진다 (Windows) | `.ps1` 파일이 BOM 없는 상태로 저장됐다. 킷 원본을 다시 복사 |
| 계정이 안 나온다 | `.claude.json` 에 oauthAccount 가 없다 (로그인 방식에 따라 다름). 다른 항목은 정상 표시된다 |

## Codex CLI 는?

Codex 에는 statusline 기능이 없다. 이 스킬은 Claude Code 전용이다.
