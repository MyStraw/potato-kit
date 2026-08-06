"""
논문 재현 + 우리 데이터 적용 — /reproduce 스킬 시운전

대상 : "Better by Default: Strong Pre-Tuned MLPs and Boosted Trees on Tabular Data"
       (Holzmüller et al., NeurIPS 2024) · github.com/dholzmueller/pytabkit (Apache-2.0)
주장 : 저자들이 사전 튜닝한 기본 하이퍼파라미터(TD = tuned defaults)가
       **튜닝 없이도** 라이브러리 기본값을 이긴다.

우리가 검증하는 것
  원 논문 벤치마크 전체 재현은 규모상 불가능하므로(수십 개 데이터셋 × GPU),
  **주장이 우리 데이터에서도 성립하는지**를 동일 프로토콜로 확인한다.
  → results.md 의 라이브러리 기본값 결과와 직접 비교 가능하다.

프로토콜 (results.md v2 와 동일하게 맞춤 — 이게 공정 비교의 조건이다)
  5시드(0,1,2,3,42) × StratifiedKFold(5, shuffle) · accuracy
  비교군: 우리가 이미 잰 LR 0.8289 / RF 0.8285 / HistGB 0.8301

실행: conda run --no-capture-output -n repro-pytabkit python reproduce_pytabkit.py
"""
import sys
import time
import warnings
from pathlib import Path

import numpy as np
from sklearn.model_selection import StratifiedKFold

warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).parent))
from adapters.titanic_adapter import load  # noqa: E402

SEEDS = [0, 1, 2, 3, 42]

# results.md v2 에서 가져온 라이브러리 기본값 결과 (동일 프로토콜)
BASELINE = {
    "LogisticRegression (sklearn 기본)": (0.8289, 0.0025),
    "RandomForest (관례적 기본)":         (0.8285, 0.0024),
    "HistGradientBoosting (관례적 기본)": (0.8301, 0.0040),
}

print("=" * 78)
print("재현 대상: pytabkit (Better by Default, NeurIPS 2024)")
print("=" * 78)

try:
    import pytabkit
    from pytabkit import LGBM_TD_Classifier, RealMLP_TD_Classifier
    print(f"  ✓ pytabkit import 성공")
except Exception as e:
    print(f"  ✗ import 실패: {type(e).__name__} {e}")
    sys.exit(1)

X, y, _ = load()
print(f"  데이터: {X.shape[0]}행 × {X.shape[1]}열 (Titanic, 우리 데이터)")

MODELS = {
    "LGBM_TD (저자 튜닝 기본값)": lambda s: LGBM_TD_Classifier(n_threads=4, random_state=s),
    "RealMLP_TD (저자 튜닝 기본값)": lambda s: RealMLP_TD_Classifier(
        device="cpu", n_threads=4, random_state=s, verbosity=0),
}

def impute_fold(Xtr, Xva):
    """폴드 내부 대치 — pytabkit 은 연속형 결측을 거부한다(저자 벤치마크엔 결측이 없었다).

    저자 코드를 고치지 않고 어댑터 층에서 해결한다.
    **반드시 학습 폴드 통계로만 대치한다** — 검증 폴드를 보고 대치하면 누수다.
    """
    a, b = Xtr.copy(), Xva.copy()
    for c in a.columns:
        if str(a[c].dtype) == "category":
            if a[c].isna().any() or b[c].isna().any():
                fill = a[c].mode()
                if len(fill):
                    a[c] = a[c].fillna(fill[0]); b[c] = b[c].fillna(fill[0])
        elif a[c].isna().any() or b[c].isna().any():
            med = a[c].median()                 # 학습 폴드 중앙값만 사용
            a[c] = a[c].fillna(med); b[c] = b[c].fillna(med)
    return a, b


results = {}
for name, mk in MODELS.items():
    scores, t0 = [], time.time()
    for s in SEEDS:
        cv = StratifiedKFold(5, shuffle=True, random_state=s)
        fold = []
        for tr, va in cv.split(X, y):
            try:
                Xtr, Xva = impute_fold(X.iloc[tr], X.iloc[va])
                m = mk(s)
                m.fit(Xtr, y[tr])
                fold.append((m.predict(Xva) == y[va]).mean())
            except Exception as e:
                print(f"  ✗ {name} 실패: {type(e).__name__} {str(e)[:110]}")
                fold = None
                break
        if fold is None:
            break
        scores.append(np.mean(fold))
    if scores:
        results[name] = (float(np.mean(scores)), float(np.std(scores)), time.time() - t0)
        print(f"  {name:32s} {results[name][0]:.4f} ± {results[name][1]:.4f}"
              f"  ({results[name][2]:.0f}초)")

if not results:
    print("\n  재현 실패 — 모든 모델이 오류. 여기서 멈춘다.")
    sys.exit(1)

print()
print("=" * 78)
print("주장 검증 — 저자 튜닝 기본값 vs 라이브러리 기본값 (동일 프로토콜)")
print("=" * 78)
print(f"  {'모델':34s} {'정확도':>18s}  {'출처':>10s}")
for n, (m, sd) in BASELINE.items():
    print(f"  {n:34s} {m:.4f} ± {sd:.4f}  {'results.md':>10s}")
print("  " + "-" * 66)
for n, (m, sd, _) in results.items():
    print(f"  {n:34s} {m:.4f} ± {sd:.4f}  {'이번 실행':>10s}")

best_lib = max(v[0] for v in BASELINE.values())
best_td = max(v[0] for v in results.values())
max_sd = max(max(v[1] for v in BASELINE.values()), max(v[1] for v in results.values()))
diff = best_td - best_lib

print()
print(f"  최고 라이브러리 기본값 : {best_lib:.4f}")
print(f"  최고 저자 튜닝 기본값  : {best_td:.4f}")
print(f"  차이 {diff:+.4f}  vs  시드 변동 최대 {max_sd:.4f}")
print()
if abs(diff) < 2 * max_sd:  # 시드 변동의 2배를 판정 기준으로
    print("  판정: **이 데이터에서는 주장을 확인할 수 없다** — 차이가 시드 변동의 2배 안이다.")
    print("        원 논문 주장을 반박하는 것이 아니다. 891행짜리 단일 데이터셋에서는")
    print("        구분할 검정력이 없다는 뜻이다 (논문은 수십 개 데이터셋 벤치마크).")
else:
    who = "저자 튜닝 기본값" if diff > 0 else "라이브러리 기본값"
    print(f"  판정: 이 데이터에서는 **{who}**이 우세하다 ({abs(diff):.4f}, 시드변동의 "
          f"{abs(diff)/max_sd:.1f}배).")
    print("        단일 데이터셋 결과이므로 일반화하지 말 것.")
