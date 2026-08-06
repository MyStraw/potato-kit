---
name: medical-plus
title: 화합물·단백질 (약물 설계 심화)
domain: 화학정보학, 생물활성, 단백질 구조
---

# medical-plus 팩

`medical` 팩의 심화판. **약물 설계·화학정보학**을 하는 경우에만 켠다.
임상 데이터 분석만 한다면 필요 없다.

## 무엇이 붙나

**단백질(타깃) → 화합물(리간드) → 생물활성 → 임상·문헌 근거**로 이어지는
약물 발견 파이프라인을 Claude가 직접 조회하며 따라갈 수 있게 된다.

## MCP 서버

### PubChem MCP ✅연결 확인됨 (2026-08-06)
- **패키지**: `pubchem-mcp-server` (PyPI 0.1.7)
- **필요**: API 키 불필요
- **규모**: 화합물 1.1억 종
- **설치**:
  ```bash
  conda run -n potato pip install pubchem-mcp-server
  claude mcp add -s user pubchem -- conda run --no-capture-output -n potato pubchem_mcp_server
  ```
  > 실행 파일 이름은 **언더스코어** `pubchem_mcp_server` 다 (패키지명은 하이픈).
- **제공**: 화합물 검색, 분자 물성, 구조 분석, 바이오어세이, 안전성·독성

### ChEMBL MCP ⚠️패키지 못 찾음
- npm `@augmented-nature/chembl-mcp-server`, PyPI `chembl-mcp-server` 둘 다 없음(확인함).
- **→ 아래 `chembl-webresource-client` 로 대체한다.** 공식 파이썬 클라이언트라
  기능상 부족하지 않다.

### UniProt MCP ⚠️패키지 못 찾음
- 공개 패키지를 찾지 못했다.
- **→ `biopython` + UniProt REST API 로 대체한다.**

> ChEMBL·UniProt 는 MCP 가 없어도 아래 파이썬 패키지로 충분히 커버된다.
> 새 MCP 가 나왔는지 확인하고 싶으면 Claude 에게
> "ChEMBL MCP 서버 지금 나온 거 있는지 찾아줘"라고 하면 된다.

설치가 안 되면 Claude에게 이렇게 말하면 된다:

```
medical-plus 팩 설치가 실패했어. PubChem/ChEMBL/UniProt 를 쓸 다른 방법 찾아줘.
정 안 되면 REST API 직접 호출하는 파이썬 헬퍼로 만들어줘.
```

REST API 직접 호출도 충분히 실용적인 대안이다. 셋 다 공개 API를 제공한다.

## 파이썬 패키지

MCP 없이도 이 라이브러리들로 상당 부분을 대체할 수 있다.

```bash
conda run -n potato pip install rdkit chembl-webresource-client biopython
```

- `rdkit` — 화학정보학 표준 라이브러리. SMILES 파싱, 분자 기술자(descriptor),
  지문(fingerprint), 유사도 검색, 구조 그리기
- `chembl-webresource-client` — ChEMBL 공식 파이썬 클라이언트
- `biopython` — 서열·구조 처리

**RDKit이 사실상 필수다.** MCP가 안 붙어도 이건 깔아두자.

## 감사 체크리스트

`medical` 팩의 항목에 더해:

- [ ] **활성 절벽(activity cliff)** — 구조가 비슷한데 활성이 크게 다른 쌍이
      train/test에 나뉘어 낙관적 성능을 만들지 않았는가?
- [ ] **스캐폴드 분할** — 무작위 분할 대신 스캐폴드 기준으로 나눴는가?
      무작위 분할은 유사 화합물이 양쪽에 들어가 성능을 과대평가한다
- [ ] **어세이 이질성** — 서로 다른 실험 조건의 활성값을 하나로 합쳤는가?
- [ ] **활성 정의 임계값** — IC50/Ki 임계값을 임의로 정하고 분류 문제로 바꿨는가?
- [ ] **음성 데이터 부재** — "활성 없음"이 기록되지 않아 양성만 있는 데이터인가?

## 데이터 소스 메모

| 소스 | 접근 |
| --- | --- |
| PubChem | pubchem.ncbi.nlm.nih.gov (PUG REST API) |
| ChEMBL | ebi.ac.uk/chembl (REST API + 파이썬 클라이언트) |
| UniProt | uniprot.org (REST API) |
| PDB (단백질 구조) | rcsb.org |
| DrugBank | go.drugbank.com (학술용 계정 필요) |
| KEGG | genome.jp/kegg (비상업 무료) |
