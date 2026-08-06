"""
모델 비교 v2 — 감사 지적사항 반영본
실행: conda run --no-capture-output -n potato python train_compare_v2.py

v1 대비 수정 (methods-reviewer 감사 반영)
  major 1: GroupKFold → StratifiedGroupKFold (층화 유지, 시드로 변동 측정 가능)
  major 2: 단일 시드 순위 금지 → 5시드 반복, 시드 간 변동 함께 보고
  minor 5: Age 결측 지시자 추가 (결측 자체가 정보)
  minor 6: 하이퍼파라미터 출처 명시 (아래 주석 참조)
  minor 8: std 를 유의성 판정에 쓰지 않음. 시드 간 변동으로 판단

하이퍼파라미터 출처: 튜닝하지 않은 관례적 기본값이다. 따라서 이 비교는
"모델 계열의 우열"이 아니라 "임의의 한 점끼리의 비교"임을 결론에 명시한다.
"""
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedGroupKFold, StratifiedKFold, cross_validate
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

warnings.filterwarnings("ignore")
SEEDS = [0, 1, 2, 3, 42]
ROOT = Path(__file__).parent
train = pd.read_csv(ROOT / "data/train.csv")


def make_features(df):
    d = df.copy()
    d["Title"] = (d.Name.str.extract(r",\s*([^\.]+)\.", expand=False).str.strip()
                  .replace(["Mlle", "Ms"], "Miss").replace("Mme", "Mrs"))
    d["Title"] = d.Title.where(d.Title.isin(["Mr", "Miss", "Mrs", "Master"]), "Rare")
    d["FamilySize"] = d.SibSp + d.Parch + 1
    d["IsAlone"] = (d.FamilySize == 1).astype(int)
    d["HasCabin"] = d.Cabin.notna().astype(int)
    return d


data = make_features(train)
y = data.Survived.values
groups = data.Ticket.values
NUM = ["Age", "Fare", "FamilySize", "SibSp", "Parch"]
CAT = ["Sex", "Pclass", "Embarked", "Title"]
BIN = ["IsAlone", "HasCabin"]
X = data[NUM + CAT + BIN]

pre = ColumnTransformer([
    # add_indicator=True : Age 결측 여부 자체가 신호 (감사 minor 5)
    ("num", Pipeline([("imp", SimpleImputer(strategy="median", add_indicator=True)),
                      ("sc", StandardScaler())]), NUM),
    ("cat", Pipeline([("imp", SimpleImputer(strategy="most_frequent")),
                      ("oh", OneHotEncoder(handle_unknown="ignore"))]), CAT),
    ("bin", "passthrough", BIN),
])

MODELS = {
    "Baseline(최빈값)": lambda s: DummyClassifier(strategy="most_frequent"),
    "LogisticRegression": lambda s: LogisticRegression(max_iter=2000, random_state=s),
    "RandomForest": lambda s: RandomForestClassifier(
        n_estimators=300, max_depth=6, min_samples_leaf=4, random_state=s, n_jobs=-1),
    "HistGradientBoosting": lambda s: HistGradientBoostingClassifier(
        max_depth=6, learning_rate=0.05, max_iter=300, random_state=s),
}


def run(scheme):
    """scheme: 'plain' = StratifiedKFold, 'group' = StratifiedGroupKFold"""
    out = {name: [] for name in MODELS}
    dummy_fold_std = []
    for s in SEEDS:
        cv = (StratifiedKFold(5, shuffle=True, random_state=s) if scheme == "plain"
              else StratifiedGroupKFold(5, shuffle=True, random_state=s))
        g = None if scheme == "plain" else groups
        for name, mk in MODELS.items():
            pipe = Pipeline([("pre", pre), ("model", mk(s))])
            # scoring 을 리스트로 주면 키가 test_accuracy, 문자열이면 test_score 다
            r = cross_validate(pipe, X, y, cv=cv, scoring=["accuracy"], groups=g, n_jobs=1)
            out[name].append(r["test_accuracy"].mean())
            if name.startswith("Baseline"):
                dummy_fold_std.append(r["test_accuracy"].std())
    return out, float(np.mean(dummy_fold_std))


print("실행 중 (5시드 × 2분할 × 4모델)...\n")
plain, dstd_plain = run("plain")
group, dstd_group = run("group")

rows = []
for name in MODELS:
    p, g = np.array(plain[name]), np.array(group[name])
    rows.append({
        "모델": name,
        "일반분할": p.mean(), "일반_시드변동": p.std(),
        "그룹분할": g.mean(), "그룹_시드변동": g.std(),
        "누수기여": p.mean() - g.mean(),
    })
df = pd.DataFrame(rows)

print("=" * 82)
print("모델 비교 — 5시드 평균 ± 시드 간 변동 (accuracy)")
print("=" * 82)
print(f"{'모델':24s} {'StratifiedKFold':>20s} {'StratifiedGroupKFold':>22s} {'누수기여':>10s}")
for _, r in df.iterrows():
    sig = " *" if abs(r["누수기여"]) > 2 * max(r["일반_시드변동"], r["그룹_시드변동"]) else "  "
    print(f"{r['모델']:24s} {r['일반분할']:.4f} ± {r['일반_시드변동']:.4f}   "
          f"{r['그룹분할']:.4f} ± {r['그룹_시드변동']:.4f}   {r['누수기여']:+.4f}{sig}")
print("\n  * = 누수 기여가 시드 변동의 2배를 넘음 (실질적이라고 볼 수 있는 수준)")

print()
print("=" * 82)
print("층화 건전성 점검 — Dummy 분류기의 폴드 간 표준편차")
print("=" * 82)
print(f"  StratifiedKFold      {dstd_plain:.4f}")
print(f"  StratifiedGroupKFold {dstd_group:.4f}")
print(f"  → 비율 {dstd_group/max(dstd_plain,1e-9):.1f}배. "
      f"{'층화 유지됨 (v1 의 GroupKFold 는 15배였다)' if dstd_group < dstd_plain*5 else '층화가 깨져 있다'}")

# 단일 시드(42)만 봤을 때의 순위 — v1 의 함정 재현
print()
print("=" * 82)
print("단일 시드의 위험 — 시드 42 하나만 볼 때 vs 5시드 평균 (StratifiedKFold)")
print("=" * 82)
real = {k: v for k, v in plain.items() if not k.startswith("Baseline")}
s42 = {k: v[SEEDS.index(42)] for k, v in real.items()}
avg = {k: np.mean(v) for k, v in real.items()}
print(f"  시드 42 순위 : {' > '.join(sorted(s42, key=s42.get, reverse=True))}")
print(f"  5시드 평균   : {' > '.join(sorted(avg, key=avg.get, reverse=True))}")
spread = max(avg.values()) - min(avg.values())
maxstd = max(np.std(v) for v in real.values())
print(f"  → 모델 간 격차 {spread:.4f} vs 시드 변동 최대 {maxstd:.4f}"
      f" → {'구분되지 않음' if spread < maxstd else '구분 가능'}")

df.to_csv(ROOT / "reports/cv_v2_summary.csv", index=False)
print(f"\n저장 → reports/cv_v2_summary.csv")
