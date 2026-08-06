---
name: libsci
title: 문헌정보·계량서지
domain: 서지 메타데이터, 인용 네트워크, 계량서지학
---

# libsci 팩

## 무엇이 붙나

`paper-search`가 **논문의 내용**을 찾는 도구라면, 이 팩은 **논문들 사이의 관계**를
보는 도구다. 인용 네트워크, 저자 협업 구조, 주제 클러스터의 시간적 변화 —
계량서지학(bibliometrics)의 본체가 여기 있다.

## 먼저 알아둘 것 — 공통 코어가 이미 상당 부분 커버한다

시운전에서 확인한 사실: 공통 코어의 **`paper-search` MCP가 20개 이상의 플랫폼을
이미 지원한다.** 아래 별도 MCP를 굳이 깔지 않아도 되는 경우가 많다.

`paper-search`가 지원하는 플랫폼 (대부분 검색·조회·다운로드 3종 도구,
`core`·`europepmc`·`pmc`·`google_scholar`·`unpaywall` 은 검색만):

```
arxiv · pubmed · pmc · europepmc · openalex · crossref · semantic
biorxiv · medrxiv · doaj · core · hal · ssrn · zenodo · dblp
iacr · openaire · citeseerx · base · google_scholar · unpaywall
```

즉 **OpenAlex·Crossref·Semantic Scholar·PubMed·Europe PMC는 이미 쓸 수 있다.**
이 팩의 값어치는 별도 MCP보다 **아래의 감사 체크리스트와 `pyalex` 대량 수집**에 있다.

> 💡 CORE·DOAJ·Unpaywall은 API 키를 넣으면 요청 제한이 풀린다(전부 무료).
> 키 없이도 동작하되 rate limit이 걸린다.

## 추가 MCP 서버 (선택)

> ⚠️ 아래는 미검증이다. `/potato-add-pack libsci`가 설치 전에 확인한다.
> **대부분의 경우 필요 없다** — 위 `paper-search`로 먼저 해보고, 부족할 때만 검토하자.

### OpenAlex MCP ⚠️미검증
- **출처**: OpenAlex 계열 MCP 서버 (여러 구현체 존재)
- **필요**: API 키 불필요 (이메일을 넣으면 우선 처리 풀로 간다)
- **규모**: 2억 편 이상의 학술 저작물. Microsoft Academic Graph의 후계
- **제공**: 논문·저자·기관·저널·개념(concept) 메타데이터, 인용 관계

### Crossref MCP ⚠️미검증
- **출처**: Crossref REST API 기반 MCP
- **필요**: API 키 불필요
- **제공**: DOI 등록 메타데이터 (제목, 저자, 저널, 발행일, 참고문헌)

### Semantic Scholar MCP ⚠️미검증
- **출처**: Semantic Scholar Academic Graph API 기반
- **필요**: 키 없이도 되나 요청 제한이 있다 (무료 키 신청 가능)
- **제공**: 인용 맥락(citation context), 영향력 있는 인용 구분, TLDR 요약

## 파이썬 패키지 (MCP 없이도 충분하다)

```bash
conda run -n potato pip install pyalex habanero networkx python-igraph
conda run -n potato pip install bibtexparser rispy
```

- **`pyalex`** — OpenAlex 공식 파이썬 클라이언트. 이게 사실상 주력이다.
  키 없이 대량 수집이 되고 페이지네이션도 처리해준다
- `habanero` — Crossref 클라이언트
- `networkx` / `python-igraph` — 인용·협업 네트워크 분석
- `bibtexparser` / `rispy` — BibTeX·RIS 파일 파싱 (EndNote·Zotero 내보내기)

시각화·토픽모델링이 필요하면:
```bash
conda run -n potato pip install bertopic pyvis
```
- `bertopic` — 임베딩 기반 토픽 모델링 (LDA보다 최근 방법)
- `pyvis` — 인터랙티브 네트워크 시각화 (HTML로 저장)

## 전형적인 작업 흐름

```
1. 수집    pyalex 로 주제·기간별 논문 메타데이터 수집 → data/
2. 정제    저자명 명확화, 중복 제거, 결측 보정
3. 분석    - 연도별 발표량 추이
           - 인용 네트워크 (누가 누구를 인용하나)
           - 저자 협업 네트워크 (공저 관계)
           - 키워드 동시출현 (co-word analysis)
           - 토픽 모델링 (주제 클러스터의 시간적 변화)
4. 해석    연구 공백, 신흥 주제, 학제 간 연결이 끊긴 지점
5. 보고    /potato-report
```

## 감사 체크리스트

`methods-reviewer`의 **문헌정보·계량서지** 절이 활성화된다.

- [ ] **DB 커버리지 편향** — Scopus/WoS/OpenAlex는 수록 범위가 다르다.
      비영어권·인문사회 학술지는 체계적으로 과소 수록된다.
      한 DB만 쓰고 "이 분야 전체"라고 말하지 않았는가?
- [ ] **인용 지연** — 최근 논문은 인용이 쌓일 시간이 없다.
      연도 보정 없이 "최근 논문은 영향력이 낮다"고 결론 내리지 않았는가?
- [ ] **저자명 명확화** — 동명이인(특히 한국·중국 이름)과 이형 표기를 처리했는가?
      OpenAlex의 저자 ID를 쓰면 상당 부분 해결되지만 완벽하지 않다
- [ ] **자기인용** — 인용 지표에서 자기인용을 분리했는가?
- [ ] **분야 정규화** — 분야마다 인용 문화가 다르다 (의학 >> 수학).
      분야 간 비교에 정규화(FWCI 등)를 적용했는가?
- [ ] **저널 vs 논문 지표 혼동** — 임팩트 팩터는 저널 지표다.
      개별 논문의 질을 저널 IF로 대리하지 않았는가?
- [ ] **표본 편향** — 검색어 하나로 뽑은 집합을 "이 분야"로 취급하지 않았는가?
      동의어·상위어·하위어를 함께 시도했는가?

## 데이터 소스 메모

| 소스 | 접근 | 비고 |
| --- | --- | --- |
| OpenAlex | api.openalex.org — 무료, 무제한에 가까움 | **1순위 추천** |
| Crossref | api.crossref.org — 무료 | DOI 메타데이터 |
| Semantic Scholar | api.semanticscholar.org — 무료 키 | 인용 맥락 |
| PubMed | E-utilities API — 무료 | 생의학 (medical 팩의 biomcp가 더 편하다) |
| arXiv | export.arxiv.org/api — 무료 | 프리프린트 |
| **RISS** | riss.kr | 국내 학위논문·학술지. API 없음 → 웹 |
| **KCI** | kci.go.kr | 한국학술지인용색인. **OpenAPI 제공** |
| **DBpia / KISS** | 기관 구독 필요 | |
| Scopus / Web of Science | 기관 구독 + API 키 | 커버리지 좋으나 유료 |

**국내 문헌 연구라면 KCI OpenAPI를 꼭 확인하자.** 한국 학술지 인용 데이터는
OpenAlex나 Scopus에 제대로 안 잡히는 경우가 많다.

## 금융·시계열과 함께 쓸 때

문헌정보학 전공이면서 금융 랩에 있다면 `finance` 팩도 같이 켜는 게 자연스럽다.
두 팩이 만나는 지점이 실제로 흥미로운 연구 주제가 된다 — 예를 들어
뉴스·공시 텍스트의 서지적 특성과 시장 반응의 관계 같은 것.

이때 **시계열 함정 체크리스트가 텍스트 데이터에도 적용된다는 점**을 잊지 말자.
뉴스 발행 시각과 시장 반영 시각을 혼동하면 그게 곧 룩어헤드 편향이다.
