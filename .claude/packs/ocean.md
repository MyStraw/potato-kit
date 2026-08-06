---
name: ocean
title: 해양·환경·기상
domain: 조위·해류·부이 관측, 기상, 대기질, 수문
---

# ocean 팩

## 무엇이 붙나

조위·해류·부이 관측값, 기상·대기질, 하천 유량을 Claude가 직접 조회할 수 있게 된다.
대부분 **API 키 없이** 바로 쓸 수 있다.

## MCP 서버

### NOAA Marine ✅패키지 확인됨 (npm v0.3.0)
- **출처**: `@cyanheads/noaa-marine-mcp-server` (npm)
  / github.com/cyanheads/noaa-marine-mcp-server
- **필요**: **API 키 불필요**
- **설치**:
  ```bash
  claude mcp add -s user noaa-marine -- npx -y @cyanheads/noaa-marine-mcp-server
  ```
- **규모**: 조위·수위 관측소 3,450+ / 해류 관측소 4,430+ / NDBC 부이 1,354+
- **제공 도구** (7종): 관측소 검색, 조석 예측, 실측 수위, 조류 예측·프로파일,
  실시간 부이 상태
- **측정 항목**: 수온, 전기전도도, 염분, 용존산소, 클로로필, 탁도, pH, 산화환원전위
  (수심별)
- **주의**: 미국 중심이다. 국내 해역은 아래 KHOA를 쓴다

### Open-Meteo (기상·대기질) ⚠️미검증
- **출처**: github.com/isdaniel/mcp_weather_server
- **필요**: **API 키 불필요**
- **제공**: 현재·과거 기상, 대기질, 시간대. 전 세계 커버리지
- **주의**: 비상업적 사용은 무료. 대량 요청은 제한이 있다

### USGS Water ⚠️미검증
- **출처**: github.com/mansurjisan/ocean-mcp
- **필요**: API 키 불필요
- **제공**: 하천 유량, 홍수 단계, 첨두 유량 이벤트, 관측소 정보 (미국)

## 파이썬 패키지

```bash
conda run -n potato pip install xarray netCDF4 cftime
conda run -n potato pip install geopandas shapely folium
conda run -n potato pip install statsmodels
```

- **`xarray`** — 다차원 격자 자료(NetCDF)의 표준 도구. 해양·기상 자료는 대부분
  NetCDF다. 이건 사실상 필수
- `netCDF4`, `cftime` — NetCDF 입출력, 기후 달력 처리
- `geopandas`, `shapely` — 공간 자료 처리
- `folium` — 지도 시각화 (HTML로 저장되어 보고서에 넣기 좋다)

위성·재분석 자료를 다루면 추가:
```bash
conda run -n potato pip install copernicusmarine cdsapi
```
- `copernicusmarine` — 코페르니쿠스 해양 서비스 (전 지구 해양 재분석·예보)
- `cdsapi` — ERA5 등 기후 재분석 자료

## 감사 체크리스트

`methods-reviewer`의 **해양·환경·공간** 절이 활성화된다.

- [ ] **공간 자기상관** — 인접 관측소를 무작위로 train/test에 나눴는가?
      가까운 관측소끼리는 값이 비슷해서 성능이 과대평가된다.
      → 공간 블록 분할이 필요하다
- [ ] **시간 자기상관** — 시계열 검증 규칙이 여기도 적용된다. 셔플 금지
- [ ] **계절성** — 계절 성분을 제거하지 않고 추세를 논하고 있지 않은가?
- [ ] **센서 교체·보정 시점** — 계단형 불연속이 있는가?
      이걸 실제 환경 변화로 해석하면 안 된다
- [ ] **이상치의 정체** — 극값이 실제 현상(폭풍, 홍수, 적조)인가 센서 오류인가?
      **전자를 제거하면 정작 중요한 사건을 버리는 것이다.** 환경 데이터에서
      이상치 제거는 특히 조심해야 한다
- [ ] **해상도 불일치** — 서로 다른 시공간 해상도 자료를 보간해 합쳤는가?
      보간이 만들어낸 상관을 실제 상관으로 해석하고 있지 않은가?
- [ ] **결측 구간의 성격** — 장비 고장인가, 악천후로 관측 불가였는가?
      후자면 결측 자체가 정보다 (MNAR)

## 데이터 소스 메모 — 국내

| 소스 | 접근 | 비고 |
| --- | --- | --- |
| **국립해양조사원 KHOA** | khoa.go.kr / 오픈API | **국내 조위·수온·염분·해류.** 키 무료 |
| 해양수산부 해양환경정보 | meis.go.kr | 해양환경 측정망 |
| 기상청 기상자료개방포털 | data.kma.go.kr | 기상·해양기상 부이. 키 무료 |
| 한국수자원공사 WAMIS | wamis.go.kr | 수문·댐·하천 |
| 환경부 물환경정보시스템 | water.nier.go.kr | 수질 측정망 |
| 공공데이터포털 | data.go.kr | 위 기관들의 API가 여기에도 등록돼 있다 |

**국내 연구라면 KHOA와 기상청이 주력이다.** NOAA는 방법론 참고나 비교 연구용으로.
국내 소스는 MCP가 없으므로 `korea` 팩과 `/find-data`로 수집 스크립트를 만든다.

## 산업공학과 함께 쓸 때

해양 데이터를 받아서 **운영을 개선**하는 문제(항만 운영, 선박 스케줄링,
양식장 관리, 해상 물류)라면 `industrial` 팩도 함께 켠다.
관측 → 예측까지가 이 팩이고, 예측 → 결정이 그쪽이다.

```
/add-pack industrial
```
