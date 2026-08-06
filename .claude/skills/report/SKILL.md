---
name: report
description: 분석 결과를 마크다운·PDF 보고서로 정리한다. 실험이 끝난 뒤 사용한다. "보고서 써줘", "결과 정리해줘", "PDF로 만들어줘" 같은 요청에 사용.
---

# /report — 보고서 작성

```
/report                        ← md 만들고 변환 여부를 물어본다
/report 학술논문 형식으로
/report 비전공자용. 수식 빼고 그림 위주로
/report PDF 로                 ← 형식을 지정하면 묻지 않고 바로 만든다
```

> **기본은 마크다운 하나다.** PDF·PPTX 는 만들지 않고 **물어본 뒤** 만든다.
> 아래 "마크다운을 먼저 만들고, 변환은 물어본다" 절 참조.

## 시작하기 전에

1. `results.md`, `plan.md`, `sources.md`를 읽는다
2. `reports/figs/`의 그림 목록을 확인한다
3. **결과가 없으면 만들지 않는다.** "먼저 `/experiment`를 돌려야 한다"고 말한다.
   없는 수치를 지어내는 것은 최악의 실패다

## 독자를 먼저 정한다

지정되지 않았으면 물어본다. 독자에 따라 문서가 완전히 달라진다.

| 독자 | 특징 |
| --- | --- |
| 지도교수·연구자 | 방법론 상세, 한계 명시, 인용 |
| 해커톤 심사위원 | 문제의식·결과 먼저, 방법 압축, 임팩트 강조 |
| 지자체·기관 | 수식 최소화, 정책 함의 중심, 그림 위주 |
| 팀원·후임 | 재현 방법, 코드 위치, 함정 공유 |

## `report-writer` 서브에이전트에 위임

분량이 있는 문서는 서브에이전트가 쓴다. 짧은 요약은 직접 쓴다.

> **서브에이전트의 파일 저장이 거부될 수 있다.** 권한 설정에 따라 `Write` 가
> 막히는데, 서브에이전트는 승인 프롬프트에 답할 수 없어 그냥 실패한다.
> 그럴 때 에이전트는 본문을 텍스트로 반환하도록 되어 있으니,
> **상위 에이전트(너)가 그 내용을 파일로 저장한다.** 저장 후 경로를 알린다.

## 기본 구조

```
요약 (결론 3~5문장)
1. 배경과 목적
2. 데이터 (sources.md 에서)
3. 방법 (검증 설계 포함)
4. 결과 (표·그림 + 각각 아래 해석 한두 문장)
5. 해석
6. 한계          ← 생략 금지
7. 다음 단계
부록 (재현 방법, 상세 수치)
```

**6번 한계 절을 반드시 쓴다.** `results.md`에 감사 결과가 있으면 반영한다.
한계를 숨긴 보고서는 신뢰를 잃고, 심사에서 먼저 공격받는다.

## 수치를 옮길 때

- **표준편차·신뢰구간을 함께 옮긴다.** 평균만 적으면 과장이다
- 차이가 편차 안이면 "차이가 있다"고 쓰지 않는다
- 원본 `results.md`에 없는 수치를 쓰지 않는다
- 반올림 자리수를 일관되게

## 그림

한글 폰트를 지정하지 않으면 깨진다.

```python
plt.rcParams['font.family'] = {
    'Windows': 'Malgun Gothic', 'Darwin': 'AppleGothic'
}.get(platform.system(), 'NanumGothic')
plt.rcParams['axes.unicode_minus'] = False
```

축 라벨·단위·범례를 확인한다. 색만으로 구분되는 그림은 흑백 인쇄와
색각 이상에서 읽히지 않으므로 형태·패턴도 함께 쓴다.

**matplotlib 그림 안에 이모지를 쓰지 않는다.** 한글 폰트에 이모지 글리프가
없어서 `⚠`·`✓`·`→` 가 두부(□)로 깨진다. 강조는 색·굵기로, 기호는 ASCII(`*`)로.
만든 PNG 를 실제로 열어 확인한다 — 코드만 보면 못 잡는다.

## PDF 변환

```bash
# pandoc (권장) — 있으면 이게 제일 깔끔하다
pandoc reports/report.md -o reports/report.pdf \
  --pdf-engine=xelatex -V mainfont="맑은 고딕"
```

**한글 PDF는 폰트를 지정하지 않으면 깨진다.** 위 `-V mainfont` 옵션을 빠뜨리지 않는다.
Windows는 `"맑은 고딕"`, macOS는 `"AppleGothic"` 또는 `"NanumGothic"`.

### pandoc 이 없을 때 — 설치를 강요하지 않는다

pandoc + LaTeX 설치는 무겁다(Windows MiKTeX 수백 MB, macOS BasicTeX).
**보고서 한 편 때문에 그걸 깔게 하지 말자.** 대신 단일 HTML 파일을 만든다 —
그림을 base64 로 인라인하면 파일 하나로 배포되고, 브라우저에서
`Ctrl/Cmd + P → PDF로 저장` 하면 PDF가 나온다.

```python
# conda run -n potato pip install markdown
import markdown, pathlib, base64, re
p = pathlib.Path("reports/report.md")
md = p.read_text(encoding="utf-8")

def inline(m):                       # 상대경로 그림 → base64 인라인
    f = p.parent / m.group(2)
    return (f'![{m.group(1)}](data:image/png;base64,'
            f'{base64.b64encode(f.read_bytes()).decode()})') if f.exists() else m.group(0)

md = re.sub(r'!\[([^\]]*)\]\((figs/[^)]+)\)', inline, md)
html = markdown.markdown(md, extensions=["tables", "fenced_code"])
p.with_suffix(".html").write_text(
    '<!doctype html><meta charset="utf-8">'
    "<style>body{font-family:-apple-system,'Malgun Gothic',sans-serif;"
    "max-width:900px;margin:2rem auto;line-height:1.75}"
    "table{border-collapse:collapse}td,th{border:1px solid #ddd;padding:6px 11px}"
    "img{max-width:100%}@media print{body{max-width:none}}</style>" + html,
    encoding="utf-8")
```

**어느 쪽으로 했는지 사용자에게 밝힌다.** "PDF 만들었습니다"라고 하고 실제로는
HTML만 만들면 안 된다. pandoc 이 없어서 HTML 로 했다고 말하고, PDF 가 꼭
필요하면 브라우저 인쇄를 안내한다.

## 저장 위치

`reports/report-<주제>-<날짜>.md`

---

## ⭐ 마크다운을 먼저 만들고, 변환은 물어본다

**PDF·PPTX 를 자동으로 만들지 않는다.** 대부분의 경우 `.md` 하나면 충분하고,
변환은 시간과 의존성(pandoc·LaTeX·python-pptx)을 잡아먹는다.

`.md` 를 저장한 뒤 **반드시 이렇게 묻는다**:

```
보고서를 reports/report-<주제>-<날짜>.md 로 만들었습니다.

이대로 두어도 되고, 원하시면 변환해 드릴 수 있습니다.
  1. 논문 형식 PDF 로 만들까요?
  2. 발표용 PPTX 로 만들까요?
  3. 지금은 md 로 충분합니다

어느 쪽으로 할까요?
```

그리고 **대답을 받은 뒤에만** 진행한다.

- **1번(PDF)** → 아래 PDF 변환 절차. pandoc 이 없으면 HTML 폴백을 쓰고 그렇게 말한다
- **2번(PPTX)** → `/slides` 로 넘긴다. 청중과 발표 시간을 함께 물어본다
- **3번** → 여기서 끝. 더 만들지 않는다

**예외** — 사용자가 처음부터 형식을 지정한 경우
(`/report PDF로`, `/report 발표자료까지`)에는 묻지 않고 바로 만든다.
이미 답을 준 것을 다시 묻는 것도 낭비다.

## 문체

- 결론을 먼저
- "~할 것으로 사료된다" 같은 군더더기 금지. "~로 보인다"면 충분
- 확실한 것과 추정을 구분
- 상관을 인과처럼 쓰지 않는다

## 다음 단계

위의 변환 질문에서 사용자가 고른 대로 한다.
아무것도 고르지 않았으면 **여기서 끝낸다** — 묻지도 않고 PPTX 를 만들지 않는다.
