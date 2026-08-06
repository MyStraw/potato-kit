---
name: finance
title: 금융·시계열
domain: 주가, 재무제표, 거시경제 시계열, 백테스트
---

# finance 팩

## 무엇이 붙나

주가·재무제표·거시경제 지표를 Claude가 직접 조회할 수 있게 된다.
그리고 **시계열 특유의 함정을 잡는 감사 체크리스트**가 활성화된다 —
이 팩에서는 후자가 더 중요하다.

## MCP 서버

### yahoo-finance MCP ✅연결 확인됨 (2026-08-06)
- **패키지**: `yahoo-finance-mcp` (npm 1.6.2) — Node 필요
- **필요**: API 키 불필요
- **설치**:
  ```bash
  claude mcp add -s user yfinance -- npx -y yahoo-finance-mcp
  ```
- **제공**: 과거 주가, 배당·액면분할, 기업 정보, 재무제표, 옵션 데이터, 시장 뉴스
- **주의**: Yahoo Finance 비공식 API 기반이라 간헐적으로 막힐 수 있다.
  중요한 연구는 데이터를 받아서 로컬에 저장해두고 쓰자

### FRED MCP ⚠️미검증
- npm `fred-mcp` 는 없지만 `fred-mcp-server` 는 실재한다(2026-08-07 확인).
  이 킷에서 연결까지는 확인하지 않았다. FRED API 키가 필요하다.
- 확실한 길: **`pandas-datareader` 로 대체한다.** FRED 를 정식 지원한다:
  ```python
  import pandas_datareader as pdr
  gdp = pdr.get_data_fred("GDP", start="2010-01-01")
  ```
- FRED API 키(무료): https://fred.stlouisfed.org/docs/api/api_key.html

### OpenBB ⚠️미검증
- **출처**: github.com/OpenBB-finance/OpenBB — MCP 서버는 PyPI `openbb-mcp-server`
- **필요**: 소스별로 키가 다름 (무료 소스만 써도 된다)
- **설치**: `conda run -n potato pip install openbb-mcp-server` (⚠️미검증 —
  실패하면 Claude에게 대안을 찾아달라고 한다)
- **제공**: 100개 이상 데이터 소스를 하나의 인터페이스로 통합
- **언제 쓰나**: yfinance만으로 부족할 때. 데이터 소스를 파라미터 하나로 바꿀 수 있다

### 설치 요약 — 검증된 것 하나면 시작할 수 있다

```bash
claude mcp add -s user yfinance -- npx -y yahoo-finance-mcp   # ✅ 연결 확인됨
```

설치가 실패해도 아래 파이썬 패키지로 대부분 대체된다. 오히려 연구용으로는
직접 받아서 저장하는 쪽이 재현성이 좋다.

## 파이썬 패키지

```bash
conda run -n potato pip install yfinance pandas-datareader statsmodels arch pmdarima
```

- `yfinance` — 주가 데이터 (MCP 없이 직접)
- `pandas-datareader` — FRED 포함 여러 소스
- `statsmodels` — ARIMA, VAR, 단위근 검정, 공적분
- `arch` — GARCH 계열 변동성 모형
- `pmdarima` — auto ARIMA

시계열 딥러닝이 필요하면 추가:
```bash
conda run -n potato pip install darts sktime
```

## 감사 체크리스트 — 이 팩의 핵심

`methods-reviewer`의 **시계열·금융** 절이 활성화된다.
일반적인 데이터 누수보다 훨씬 잡기 어려운 것들이다.

### 함정 4종

| 함정 | 무엇인가 | 증상 |
| --- | --- | --- |
| **룩어헤드 편향** | 그 시점에 알 수 없던 정보 사용 | 백테스트만 비정상적으로 좋다 |
| **생존 편향** | 살아남은 개체만으로 검증 | 과거 성과가 체계적으로 과대평가 |
| **비현실적 평가** | 체결·리밸런싱 가정이 현실과 다름 | 실전에서 재현 안 됨 |
| **비용 무시** | 거래비용·슬리피지·세금 미반영 | 수익이 비용에 먹힘 |

### 상세 체크

- [ ] 재무제표를 **발표일**이 아니라 회계기준일로 붙이지 않았는가
- [ ] 지수 편입 종목을 "현재 기준"으로 과거에 소급 적용하지 않았는가
- [ ] 정규화·표준화를 **전체 기간** 통계로 하지 않았는가 (미래가 과거로 샌다)
- [ ] 상장폐지·청산된 종목이 데이터에서 빠지지 않았는가
- [ ] 랜덤 셔플 K-fold를 쓰지 않았는가 (→ 워크포워드/확장윈도우여야 한다)
- [ ] 학습·검증 구간 사이에 퍼징(purging)·엠바고를 뒀는가
- [ ] 정상성 검정 없이 원계열을 회귀에 넣지 않았는가 (허구적 회귀)
- [ ] 레짐이 바뀐 구간을 하나로 묶어 학습하지 않았는가
- [ ] 수백 개 전략을 백테스트하고 최고를 골랐는가 (→ 다중검정. 그 성과는 우연일 수 있다)

### 관점: 정확도가 아니라 의사결정 품질

**예측 정확도를 극대화하는 것이 목표가 아닌 경우가 많다.**
방향 정확도가 조금 낮아도 손실을 덜 보는 모델이 실제로는 더 낫다.

평가지표를 정할 때 스스로 물어보자:
- 이 지표는 "맞히는 것"을 재는가, "결정의 결과"를 재는가?
- 틀렸을 때의 비용이 방향에 따라 다른가? (상승 오판 vs 하락 오판)
- 거래비용을 반영하고도 유의한 차이인가?

Claude에게 "이 문제에서 정확도 대신 봐야 할 지표가 뭔지" 물어보면 짚어준다.

## 데이터 소스 메모

| 소스 | 접근 |
| --- | --- |
| 한국은행 ECOS (금리·환율·통화) | ecos.bok.or.kr — API 키 무료 |
| KRX 정보데이터시스템 (국내 주식) | data.krx.co.kr |
| 금융감독원 DART (공시·재무제표) | opendart.fss.or.kr — API 키 무료 |
| 통계청 KOSIS (거시지표) | kosis.kr |
| FRED (미국 거시) | fred.stlouisfed.org — API 키 무료 |
| Yahoo Finance | `yfinance` 패키지 |

국내 데이터가 필요하면 `korea` 팩도 함께 켜자.
