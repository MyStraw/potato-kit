---
name: medical
title: 의료·약학·바이오
domain: 임상 데이터, 의약품, 유전체, 생의학 문헌
---

# medical 팩

## 무엇이 붙나

PubMed 문헌, ClinicalTrials.gov 임상시험, 유전자 변이, FDA 의약품 정보를
Claude가 직접 조회할 수 있게 된다. 웹 검색으로 뒤지는 것보다 정확하고,
유전자·질환·변이 이름 같은 전문 용어로 정밀 검색이 된다.

## MCP 서버

### biomcp ✅검증됨
- **출처**: `biomcp-python` (PyPI) / github.com/genomoncology/biomcp
- **필요**: API 키 불필요 (일부 고급 기능은 선택적 키)
- **설치**:
  ```bash
  conda run -n potato pip install biomcp-python
  claude mcp add -s user biomcp -- conda run --no-capture-output -n potato python -m biomcp run
  ```
- **제공 도구** (21종): 내부적으로 40개 이상의 상위 소스를 조회한다
  - `article_searcher` / `article_getter` — **PubMed·PubTator3** + 프리프린트.
    PMID·DOI로 초록·본문 조회
  - `trial_searcher` / `trial_getter` / `trial_protocol_getter` /
    `trial_outcomes_getter` / `trial_locations_getter` — ClinicalTrials.gov.
    질환·중재·상(phase)별 필터 검색
  - `variant_searcher` / `variant_getter` — MyVariant.info 유전자 변이
  - 그 외 연동 소스: Europe PMC, MyGene.info, UniProt, ClinVar, **OpenFDA**,
    MyDisease.info, Reactome 등

## 파이썬 패키지

```bash
conda run -n potato pip install lifelines scikit-survival tableone
```

- `lifelines` — 생존분석 (Kaplan-Meier, Cox 회귀)
- `scikit-survival` — 생존분석 머신러닝
- `tableone` — 임상 논문의 Table 1(기저특성표) 자동 생성

## 감사 체크리스트

`methods-reviewer`의 **의료·보건** 절이 활성화된다. 핵심은:

- 표본 선택 편향 (코호트 정의가 결과에 유리하게 되어 있지 않은가)
- 결측 메커니즘 (임상 결측은 무작위가 아니다. "검사를 안 했다"도 정보다)
- 불멸 시간 편향 (immortal time bias)
- 임상적 유의성 vs 통계적 유의성
- 기저 유병률 (희귀 사건에 accuracy를 쓰면 안 된다)
- 시점 정합성 (예측 시점에 알 수 있는 변수만 썼는가)

## 데이터 보호 (이 팩에서 특히 중요)

의료 데이터는 대부분 **외부 전송 제한**이 걸려 있다.

- MIMIC 계열 — PhysioNet 자격 인증 + DUA. 원본 레코드를 외부 API로 보내면 위반
- 병원 EMR — IRB 승인 조건에 반출 금지가 들어 있는 것이 보통
- 국민건강보험공단·심평원 표본 데이터 — 반출 및 재식별 금지 조항

**규칙**: 원본은 로컬 코드 안에서만 처리하고, 모델에는 스키마와 집계 통계만
보여준다. 이건 `CLAUDE.md`의 데이터 보호 절에 이미 들어 있다.

## 데이터 소스 메모

MCP 없이 접근하는 것들:

| 소스 | 접근 |
| --- | --- |
| MIMIC-III / IV | PhysioNet 자격 인증 후 다운로드. 로컬 처리 |
| 국민건강보험 표본코호트 | 공단 신청 |
| 건강보험심사평가원 공공데이터 | opendata.hira.or.kr |
| 질병관리청 KNHANES(국민건강영양조사) | knhanes.kdca.go.kr |
| 식약처 의약품 정보 | nedrug.mfds.go.kr (공공데이터포털에도 API 있음) |

## 심화가 필요하면

화합물 구조·생물활성·단백질까지 다루려면 `medical-plus` 팩을 함께 켠다.

```
/add-pack medical-plus
```
