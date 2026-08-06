<div align="center">

# 🥔 potato-kit

**Claude Code를 연구용 작업대로 바꿔주는 설치형 킷**

논문 찾기 · 데이터 수집 · 분석 · **방법론 감사** · 보고서까지<br>
연구 한 사이클을 슬래시 명령 몇 개로 돌린다

<br>

![Platform](https://img.shields.io/badge/Windows%20·%20macOS%20·%20Linux-지원-2ea44f?style=flat-square)
![Claude](https://img.shields.io/badge/Claude%20Code-지원-8A63D2?style=flat-square)
![Codex](https://img.shields.io/badge/Codex%20CLI-지원-10A37F?style=flat-square)
![Skills](https://img.shields.io/badge/스킬-12종-blue?style=flat-square)
![Packs](https://img.shields.io/badge/전공팩-7종-orange?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-lightgrey?style=flat-square)

<br>

[**설치**](#-설치-5분) · [**전공 팩**](#-전공-팩-끼우기) · [**첫 실행**](#-첫-실행--나는-어디서-시작하나) · [**스킬**](#-스킬-12종) · [**사용법 가이드**](./GUIDE.md) · [**완주 예제**](./projects/_example/)

</div>

---

## 이게 뭔가요

Claude Code는 강력하지만 **범용 도구**입니다. 연구자가 쓰려면 매번 같은 걸 설명해야 하죠 —
"데이터 누수 조심해", "결과는 재현 가능한 스크립트로 남겨줘", "논문 좀 찾아줘"…

potato-kit은 그 반복을 없앱니다. 한 번 설치하면:

<table>
<tr>
<td width="50%" valign="top">

**🔬 연구 절차가 내장됩니다**

문헌조사 → 데이터 발굴 → 탐색 → 실험 → **감사** → 보고
여섯 단계가 슬래시 명령으로 들어 있습니다

</td>
<td width="50%" valign="top">

**🧪 전공별로 갈아 끼웁니다**

의료·금융·해양·문헌정보·산업공학…
`/add-pack` 한 줄로 그 분야 데이터베이스가 붙습니다

</td>
</tr>
<tr>
<td width="50%" valign="top">

**🛡️ 틀린 결과를 잡아냅니다**

데이터 누수, 검증 설계 오류, 통계 오용을
전담 에이전트가 분야별 체크리스트로 감사합니다

</td>
<td width="50%" valign="top">

**💸 Pro 구독이면 충분합니다**

모든 모델이 Sonnet으로 고정돼 있어
한도가 오래갑니다. Windows에서도 그대로 동작합니다

</td>
</tr>
</table>

---

## 🚀 설치 (5분)

<details open>
<summary><b>Windows</b> (PowerShell)</summary>

```powershell
git clone https://github.com/MyStraw/potato-kit.git
cd potato-kit
powershell -ExecutionPolicy Bypass -File .\install.ps1
```
</details>

<details>
<summary><b>macOS / Linux</b></summary>

```bash
git clone https://github.com/MyStraw/potato-kit.git
cd potato-kit
bash install.sh
```
</details>

<details>
<summary><b>Codex CLI 를 쓴다면</b> (ChatGPT 구독)</summary>

```bash
bash install-codex.sh                                          # macOS/Linux
powershell -ExecutionPolicy Bypass -File .\install-codex.ps1    # Windows
```

Codex 는 구조가 달라 **일부만 그대로 옮겨집니다.** 아래 표를 먼저 보세요.

| | Claude Code | Codex CLI |
| :-- | :-: | :-- |
| 운영 규칙 | `CLAUDE.md` ✅ | `AGENTS.md` ✅ 자동 생성 |
| MCP 서버 | ✅ | ✅ `codex mcp add` |
| 슬래시 명령 (`/research` 등) | ✅ 12종 | ❌ → **말로 요청**하면 AGENTS.md 가 해당 스킬 파일로 라우팅 |
| 서브에이전트 4종 | ✅ 자동 위임 | ❌ → 역할 파일을 읽고 직접 수행 |

절차 자체는 같습니다. Codex 도 파일을 읽을 수 있으므로,
`"이 데이터 EDA 해줘"` 라고 하면 AGENTS.md 가 `.claude/skills/eda/SKILL.md` 를
읽으라고 지시하고 같은 절차를 따릅니다.

> 💡 **감사는 새 Codex 세션에서 돌리세요.** 서브에이전트가 없어 같은 대화에서
> 자기 코드를 감사하게 되는데, 그러면 확증 편향이 생깁니다.

</details>

### 준비물

| 필요한 것 | 확인 | 없으면 |
| :-- | :-- | :-- |
| **Claude Code** | `claude --version` | [설치 안내](https://claude.com/product/claude-code) |
| **Claude 구독** | `claude` → `/login` | Pro면 충분합니다 |
| **Python** (Anaconda/Miniconda) | `conda --version` | 설치 스크립트가 안내합니다 |
| Node.js *(선택)* | `node --version` | 일부 MCP에만 필요 |

### 설치 스크립트가 하는 일

```
1. conda 확인 → 없으면 Miniconda 설치 안내
2. potato 라는 conda 환경 생성 (Python 3.11)
3. 분석 라이브러리 + MCP 서버 패키지 설치
4. 공통 코어 MCP 2종을 Claude Code에 등록
5. 스킬·에이전트·팩을 설정 디렉토리로 복사
6. 기본 모델을 Sonnet으로 지정 (이미 지정돼 있으면 건드리지 않음)
```

> 💡 **유저 스코프로 설치되므로 어느 폴더에서든 동작합니다.**
> 킷 폴더 안에서만 쓸 수 있는 게 아닙니다.

### 확인

```bash
claude mcp list     # paper-search 가 보이면 성공
```

그다음 Claude Code를 **껐다 켜고** `/add-pack list` 를 쳐보세요.

---

## 🎯 첫 실행 — 나는 어디서 시작하나

설치했는데 뭘 쳐야 할지 모르겠다면, **`/research` 하나만 기억하세요.**
상황을 물어보고 거기에 맞는 경로로 데려갑니다.

```
cd ~/내연구폴더
claude
```
```
/research
```

<div align="center">

**`/research`가 가장 먼저 묻는 것 — "어떤 상황인가요?"**

</div>

<table>
<tr>
<th width="6%">유형</th><th width="30%">이런 상황이면</th><th width="64%">이렇게 흘러갑니다</th>
</tr>

<tr>
<td align="center"><b>A</b></td>
<td>

**논문이 먼저 있다**

"교수님이 이 논문 읽고 우리 데이터에 적용해보래"<br>
*(랩 연구 · 아이디어 확장)*

</td>
<td>

```
/lit-review  선행·후속 지형 파악
     ↓
/reproduce   저자 코드 재현 → 원 논문 수치와 대조
     ↓
데이터 차이 분석  내 데이터 vs 논문 데이터
     ↓
/experiment  원 방법 vs 내 아이디어 (ablation)
     ↓
/report
```
**핵심**: 재현 수치가 안 맞으면 원인부터 규명합니다.<br>
안 그러면 "내 아이디어가 좋아서 오른 건지" 알 수 없어요.

</td>
</tr>

<tr>
<td align="center"><b>B</b></td>
<td>

**데이터가 이미 있다**

"이 데이터로 뭘 예측/분류하고 싶다"<br>
*(해커톤 · 캐글 · 데이콘 · 과제)*

</td>
<td>

```
/eda         성격 파악 + HTML 리포트
     ↓        └ "이 데이터로 풀 수 있는 문제 3가지" 제안
문제 확정     무엇을 예측할지 고른다
     ↓
/experiment  베이스라인 → 모델 비교 → 감사
     ↓        └ 누수·검증오류 나오면 여기서 멈춤
/report  (경진대회면 /submit 도)
```
**핵심**: 감사를 건너뛰지 마세요.<br>
누수 하나로 리더보드 1등이 실격됩니다.

</td>
</tr>

<tr>
<td align="center"><b>C</b></td>
<td>

**주제만 있다**

"청년 정주여건 개선하래…<br>데이터도 문제도 내가 정해야 해"<br>
*(지자체 과제 · RISE · 자유주제)*

</td>
<td>

```
문제 쪼개기   데이터로 답할 질문 3~5개로
     ↓
/find-data   소스 탐색 → 실현가능성 확인 → 수집 스크립트
     ↓        └ 못 구하면 질문을 바꿉니다. 정상이에요
/eda         받은 게 쓸만한지
     ↓
/experiment  또는 기술통계 (예측 모델이 필요 없을 때도 많음)
     ↓
/report
```
**핵심**: 수집을 **스크립트로** 남깁니다.<br>
보고서의 "데이터 출처" 절이 저절로 채워져요.

</td>
</tr>

<tr>
<td align="center"><b>D</b></td>
<td>

**결정을 내려야 한다**

"근무표를 짜야 해"<br>"창구 몇 개면 될까"<br>
*(산업공학 · 운영 개선)*

</td>
<td>

```
정식화       결정변수·목적함수·제약을 말로 먼저
     ↓
용량 회계     애초에 가능한 문제인가 (30초 산수)
     ↓
/optimize    작은 예제 → 실제 규모
     ↓
민감도 분석   입력이 흔들리면 답이 얼마나 바뀌나
     ↓
/report
```
**핵심**: 최적화의 실패는 푸는 단계가 아니라<br>**세우는 단계**에서 일어납니다.

</td>
</tr>
</table>

### 반자동입니다 — 매 단계 물어봅니다

`/research`는 알아서 끝까지 달리지 않습니다. 각 단계가 끝나면 이렇게 멈춥니다:

```
## [2/5] 데이터 수집 완료

한 일   : KOSIS·국토부에서 3개 데이터셋 수집
결과    : 실거래가 184,332건, 연령별 인구 4,120행
막힌 것 : 청년 전월세 부담률은 직접 제공하는 통계가 없음
          → 실거래가 + 소득으로 계산해야 함

다음은 [3/5] 탐색(/eda)입니다.
  1. 계속 진행    2. 방향을 바꾸고 싶다    3. 여기서 멈춘다
```

**"막힌 것"을 반드시 보고합니다.** 숨기고 넘어가면 다음 단계에서 더 크게 터지니까요.

> 💡 스킬을 직접 부르는 것도 당연히 됩니다.
> 뭘 할지 이미 안다면 `/eda data/train.csv` 처럼 바로 쓰세요.
> `/research`는 **길잡이**일 뿐 필수가 아닙니다.

### 세션이 끊겼다면

```
/research 이어서
```
`plan.md`의 진행 기록을 읽고 다음 단계부터 재개합니다.

---

## 📚 기본으로 붙는 것

`paper-search` 하나로 **20개 이상 학술 플랫폼**을 검색합니다.

<div align="center">

`arXiv` · `PubMed` · `PMC` · `Europe PMC` · `OpenAlex` · `Crossref` · `Semantic Scholar`<br>
`bioRxiv` · `medRxiv` · `DOAJ` · `CORE` · `SSRN` · `Zenodo` · `DBLP` · `HAL` · …

</div>

여기에 `jupyter` MCP가 붙어 노트북에서 코드를 실행합니다.
(`bash start-jupyter.sh` / `.ps1` 로 주피터를 먼저 띄우세요)

---

## 🧩 전공 팩 끼우기

```
/add-pack list          # 목록 보기
/add-pack medical       # 켜기
/add-pack remove ocean  # 끄기
/add-pack new 재료공학   # 목록에 없으면 새로 만들기
```

| 팩 | 무엇이 붙나 | 누구에게 |
| :-- | :-- | :-- |
| 🏥 **`medical`** | PubMed · 임상시험 · 유전자변이 · OpenFDA · ClinVar | 의료 · 약학 · 바이오 |
| 💊 **`medical-plus`** | 화합물(PubChem) · 생물활성(ChEMBL) · 단백질(UniProt) | 약물 설계 · 화학정보학 |
| 📈 **`finance`** | 주가 · 재무제표 · 거시경제 시계열 | 금융 · 시계열 |
| 📖 **`libsci`** | 서지 메타데이터 · 인용 네트워크 | 문헌정보 · 계량서지학 |
| 🌊 **`ocean`** | 조위 · 해류 · 부이 관측 · 기상 · 수문 | 해양 · 환경 |
| ⚙️ **`industrial`** | OR-Tools · SimPy · NetworkX | 산업공학 · 물류 |
| 🇰🇷 **`korea`** | KOSIS · 공공데이터포털 · 실거래가 · ECOS · KHOA | 지역 · 정책 과제 |

> 팩마다 **그 분야의 방법론 함정 체크리스트**가 함께 들어옵니다.
> 예를 들어 `finance`를 켜면 룩어헤드 편향·생존 편향·거래비용 누락을 감사합니다.

<details>
<summary>목록에 없는 전공이라면</summary>

`.claude/packs/` 에 파일 하나만 추가하면 됩니다.
형식은 [`packs/README.md`](./.claude/packs/README.md)에 있고,
Claude에게 `"재료공학 팩 만들어줘"` 라고 시켜도 됩니다 —
그 분야 공개 DB를 조사해서 팩 파일을 만들어줍니다.

</details>

---

## ⚡ 스킬 12종

| 스킬 | 하는 일 |
| :-- | :-- |
| **`/research`** | **연구 한 사이클 반자동 진행** — 뭘 할지 모르면 여기서 시작 |
| **`/start`** | 현재 폴더를 연구 프로젝트로 초기화 |
| `/lit-review <주제>` | 논문·근거 조사 → 정리 노트 |
| `/find-data <주제>` | 공개 데이터 발굴 → **수집 스크립트** → `data/` 적재 |
| `/eda <파일>` | 탐색적 분석 + HTML 리포트 |
| `/experiment` | 전처리 → 모델 비교 → **방법론 감사** → 결과 종합 |
| `/reproduce <논문>` | 논문 + 저자 코드 재현 → 내 데이터에 적용 |
| `/optimize` | 최적화·시뮬레이션 정식화 → 해 구하기 → 민감도 분석 |
| `/report` | 결과를 마크다운 보고서로 *(PDF·PPTX는 물어본 뒤)* |
| `/slides` | 발표용 PPTX *(요청했을 때만)* |
| `/submit` | 경진대회 제출 파일 + 개선 루프 |
| `/add-pack` | 전공 팩 켜기 / 끄기 / 만들기 |

기본 흐름은 이렇습니다:

```
          ┌─────────────── /research (반자동 · 매 단계 확인) ───────────────┐
          │                                                              │
/start ──→ /lit-review ─→ /find-data ─→ /eda ─→ /experiment ─→ /report
  ↑         논문부터        데이터부터            ↓
프로젝트                                   감사가 여기서 돈다
 초기화                                    (methods-reviewer)
```

**`/start` 부터 시작하세요.** 스킬은 어디서든 동작하지만 **운영 규칙은 폴더에
`CLAUDE.md` 가 있어야 적용됩니다.** `/start` 가 그걸 놓아줍니다.

각 스킬은 **혼자서도, 이어서도** 동작합니다.

---

## 🛡️ 이 킷의 핵심 — 감사 에이전트

성능을 올리는 것보다 **틀린 결과를 내지 않는 것**이 먼저입니다.
`methods-reviewer`는 결과를 의심하는 것이 임무입니다.

<table>
<tr><th>공통</th><td>데이터 누수 · 교차검증 설계 · 다중비교 · 지표 적합성</td></tr>
<tr><th>🏥 의료</th><td>표본 선택 편향 · 결측 메커니즘 · 불멸 시간 편향 · 임상적 유의성</td></tr>
<tr><th>📈 시계열</th><td>룩어헤드 편향 · 생존 편향 · 워크포워드 검증 · 거래비용</td></tr>
<tr><th>🌊 공간</th><td>공간 자기상관 · 계절성 · 센서 교체 불연속</td></tr>
<tr><th>📖 서지</th><td>DB 커버리지 편향 · 인용 지연 · 저자명 명확화</td></tr>
<tr><th>⚙️ 최적화</th><td>모델링 타당성 · 제약 누락 · 해의 취약성 · 시뮬레이션 검증</td></tr>
</table>

> **실화**: 이 킷을 만들면서 시운전으로 돌린 실험이 이 에이전트에게 **fail 판정**을
> 받았습니다. 감사 에이전트가 직접 재현 스크립트를 짜서 돌린 결과,
> `GroupKFold`가 층화를 하지 않는다는 걸 잡아내 **누수를 1.5배 과대평가했다**는
> 사실이 드러났습니다. 그 과정이 [`projects/_example/`](./projects/_example/)에 남아 있습니다.

---

## 📂 프로젝트 시작하기

**어느 폴더에서든** Claude Code를 열고:

```
/start 내 연구 주제
```

폴더 구조·`CLAUDE.md`·`plan.md`를 만들어주고, 프로젝트 성격(해커톤/논문/기관)과
데이터 반출 제한을 물어본 뒤 그에 맞는 규칙을 넣어줍니다.

> ⚠️ **`/start` 를 건너뛰면 운영 규칙이 적용되지 않습니다.** 스킬 자체는 동작하지만,
> 데이터 보호·산출물 규칙 같은 상시 규칙은 폴더의 `CLAUDE.md` 에서 나옵니다.

킷 안에서 시작하고 싶다면 템플릿을 복사해도 됩니다:
```bash
cp -r projects/_template projects/my-project
```

`projects/<이름>/CLAUDE.md`에 프로젝트 성격을 적어두면 **그 폴더에서만** 규칙이 바뀝니다:

<table>
<tr><td width="33%"><b>🏃 해커톤</b><br>속도 우선<br>검증은 제출 직전 한 번</td>
<td width="33%"><b>🎓 논문·랩</b><br>엄밀성 우선<br>단계마다 감사</td>
<td width="33%"><b>🏛️ 기관 과제</b><br>설명 가능성 우선<br>비전공자도 읽히게</td></tr>
</table>

---

## 🗂 구조

```
potato-kit/
├── README.md                 지금 이 문서
├── GUIDE.md                  ★ 페르소나별 사용법 — 먼저 읽으세요
├── CLAUDE.md                 연구 운영 규칙 (프로젝트에 상속)
├── install.sh / install.ps1  설치
├── start-jupyter.sh / .ps1   주피터 + MCP 연결
├── .claude/
│   ├── agents/    literature-scout · data-analyst · methods-reviewer · report-writer
│   ├── skills/    슬래시 명령 12종
│   └── packs/     전공 팩 7종 (+ 새 팩 만드는 법)
└── projects/
    ├── _template/ 새 프로젝트 템플릿
    └── _example/  완주 예제 (Titanic 워크플로 한 바퀴)
```

---

## 🆘 자주 막히는 곳

<details>
<summary><b>/add-pack 이 안 먹혀요</b></summary>

Claude Code를 껐다 켜세요. 스킬은 시작할 때 읽힙니다.
</details>

<details>
<summary><b>claude mcp list 에 아무것도 없어요</b></summary>

설치 스크립트를 다시 돌리고, `-s user` 스코프로 등록됐는지 확인하세요.
`CLAUDE_CONFIG_DIR` 환경변수를 쓰고 있다면 스크립트가 그쪽에 설치합니다
(실행 중 어디에 설치하는지 출력합니다).
</details>

<details>
<summary><b>jupyter MCP가 연결이 안 돼요</b></summary>

주피터 서버를 먼저 띄워야 합니다:
`bash start-jupyter.sh` (Windows: `.\start-jupyter.ps1`)
</details>

<details>
<summary><b>그림에서 한글이 깨져요</b></summary>

matplotlib 폰트를 지정하세요. 스킬에 코드가 들어 있습니다.
Windows는 `Malgun Gothic`, macOS는 `AppleGothic`, Linux는 `NanumGothic`.
**그림 안에 이모지는 쓰지 마세요** — 한글 폰트에 이모지 글리프가 없어 두부(□)로 깨집니다.
</details>

<details>
<summary><b>사용량 한도가 빨리 닳아요</b></summary>

- 큰 파일을 통째로 읽지 말고 pandas로 요약만 보세요
- 병렬 서브에이전트를 줄이세요 (`/experiment`에 "순차로 돌려줘")
- 주제가 바뀌면 `/clear` 로 새 세션을 여세요
- 한도가 임박하면: **결과 생성 > 정리 > 탐색** 순으로

자세한 건 [`CLAUDE.md`](./CLAUDE.md)의 "사용량 아끼기" 절에 있습니다.
</details>

<details>
<summary><b>Codex 에서 스킬이 안 먹혀요</b></summary>

Codex 에는 슬래시 명령이 없습니다. `"이 데이터 EDA 해줘"` 처럼 **말로** 요청하면
`~/.codex/AGENTS.md` 가 해당 스킬 파일을 읽으라고 라우팅합니다.
AGENTS.md 가 없다면 `bash install-codex.sh` 를 돌리세요.
</details>

<details>
<summary><b>macOS에서 LightGBM이 안 돌아가요</b></summary>

`conda install -c conda-forge llvm-openmp`
macOS에는 OpenMP 런타임이 기본 탑재돼 있지 않습니다. Windows·Linux는 무관합니다.
</details>

---

## 🤝 기여

버그를 만나거나 팩을 새로 만들었다면 이슈나 PR로 보내주세요.
특히 **Windows에서 겪은 문제**가 가장 도움이 됩니다.

새 전공 팩은 [`.claude/packs/README.md`](./.claude/packs/README.md) 형식만 맞추면 됩니다.

---

<div align="center">

**감자 세 마리를 위해 만들었습니다** 🥔🥔🥔

[사용법 가이드 →](./GUIDE.md)

</div>
