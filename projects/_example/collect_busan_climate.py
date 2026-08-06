"""
공개 데이터 수집 — 부산 폭염·한파 일수 (RISE 정주여건 대리지표)
실행: conda run --no-capture-output -n potato python collect_busan_climate.py

/find-data 스킬 절차
  1. 질문 → 데이터 요구사항 번역
  2. 소스 탐색 (팩의 데이터 소스 메모 우선)
  3. 실현 가능성 확인 ← 스크립트 다 짜기 전에 1건만 받아본다
  4. 수집 스크립트
  5. 정제
  6. sources.md 기록

질문: "부산 청년 정주여건" 중 기후 쾌적성 갈래
      → 연도별 폭염일수(최고기온 33도 이상)·한파일수(최저 -12도 이하) 추이
소스: Open-Meteo Archive API (API 키 불필요, 비상업 무료)
      국내 공식 통계는 기상청 API 키가 필요하므로 키 없이 되는 이 소스로 먼저 확인
"""
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).parent
RAW = ROOT / "data/raw"; RAW.mkdir(parents=True, exist_ok=True)

BUSAN = {"latitude": 35.1796, "longitude": 129.0756}   # 부산시청
BASE = "https://archive-api.open-meteo.com/v1/archive"


def fetch(start, end):
    q = urllib.parse.urlencode({
        **BUSAN, "start_date": start, "end_date": end,
        "daily": "temperature_2m_max,temperature_2m_min",
        "timezone": "Asia/Seoul",
    })
    with urllib.request.urlopen(f"{BASE}?{q}", timeout=60) as r:
        return json.loads(r.read().decode())


# ── 3. 실현 가능성 확인 — 스크립트를 다 짜기 전에 1건만 ──────────
print("=== 실현 가능성 확인 (1일치) ===")
try:
    probe = fetch("2025-08-01", "2025-08-01")
    d = probe["daily"]
    print(f"  ✓ 응답 정상 — {d['time'][0]}: "
          f"최고 {d['temperature_2m_max'][0]}°C / 최저 {d['temperature_2m_min'][0]}°C")
    print(f"  단위: {probe['daily_units']['temperature_2m_max']}, "
          f"시간대: {probe['timezone']}")
except Exception as e:
    print(f"  ✗ 실패: {type(e).__name__} {e}")
    print("  → 여기서 멈춘다. 스크립트를 더 짜기 전에 소스를 바꾸거나 키를 받아야 한다.")
    sys.exit(1)

# ── 4. 수집 ────────────────────────────────────────────────────
print("\n=== 수집 (2015~2025, 연 단위로 나눠서) ===")
frames = []
for yr in range(2015, 2026):
    try:
        d = fetch(f"{yr}-01-01", f"{yr}-12-31")["daily"]
        frames.append(pd.DataFrame({
            "date": pd.to_datetime(d["time"]),
            "tmax": d["temperature_2m_max"],
            "tmin": d["temperature_2m_min"],
        }))
        print(f"  {yr}: {len(d['time'])}일")
        time.sleep(0.3)          # 호출 간격 준수
    except Exception as e:
        print(f"  {yr}: 실패 ({type(e).__name__}) — 건너뜀")

if not frames:
    print("  수집된 데이터 없음"); sys.exit(1)

raw = pd.concat(frames, ignore_index=True)
raw.to_csv(RAW / "busan_daily_temp.csv", index=False)
print(f"  → data/raw/busan_daily_temp.csv ({len(raw)}행)")

# ── 5. 정제·파생 ───────────────────────────────────────────────
raw["year"] = raw.date.dt.year
agg = raw.groupby("year").agg(
    폭염일수=("tmax", lambda s: int((s >= 33).sum())),
    열대야일수=("tmin", lambda s: int((s >= 25).sum())),
    한파일수=("tmin", lambda s: int((s <= -12).sum())),
    연평균최고=("tmax", "mean"),
).round(2).reset_index()

proc = ROOT / "data/processed"; proc.mkdir(parents=True, exist_ok=True)
agg.to_csv(proc / "busan_climate_yearly.csv", index=False, encoding="utf-8-sig")

print("\n=== 연도별 집계 ===")
print(agg.to_string(index=False))

full = agg[agg.year < 2026]
if len(full) >= 5:
    first, last = full.head(3)["열대야일수"].mean(), full.tail(3)["열대야일수"].mean()
    print(f"\n  열대야: 초기 3년 평균 {first:.1f}일 → 최근 3년 평균 {last:.1f}일 "
          f"({last-first:+.1f}일)")
    print("  ⓘ 관측 기간이 11년뿐이라 추세 검정을 하기엔 짧다. 기술통계로만 읽을 것.")

print(f"\n  → data/processed/busan_climate_yearly.csv")
