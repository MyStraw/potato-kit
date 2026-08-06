"""
제출 파일 생성 — /submit 스킬 시운전
실행: conda run --no-capture-output -n potato python predict.py

스킬 절차
  1. sample_submission 형식 확인   ← 없으면 대회 규격을 직접 확인
  2. 예측 생성
  3. 자동 검증 (행수·컬럼명·결측·범위·ID 일치)
  4. submissions.md 에 이력 기록
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

SEED = 42
ROOT = Path(__file__).parent
train = pd.read_csv(ROOT / "data/train.csv")
test = pd.read_csv(ROOT / "data/test.csv")


def make_features(df):
    d = df.copy()
    d["Title"] = (d.Name.str.extract(r",\s*([^\.]+)\.", expand=False).str.strip()
                  .replace(["Mlle", "Ms"], "Miss").replace("Mme", "Mrs"))
    d["Title"] = d.Title.where(d.Title.isin(["Mr", "Miss", "Mrs", "Master"]), "Rare")
    d["FamilySize"] = d.SibSp + d.Parch + 1
    d["IsAlone"] = (d.FamilySize == 1).astype(int)
    d["HasCabin"] = d.Cabin.notna().astype(int)
    return d


NUM = ["Age", "Fare", "FamilySize", "SibSp", "Parch"]
CAT = ["Sex", "Pclass", "Embarked", "Title"]
BIN = ["IsAlone", "HasCabin"]

tr, te = make_features(train), make_features(test)
X, y = tr[NUM + CAT + BIN], tr.Survived.values
X_test = te[NUM + CAT + BIN]

pre = ColumnTransformer([
    ("num", Pipeline([("imp", SimpleImputer(strategy="median", add_indicator=True)),
                      ("sc", StandardScaler())]), NUM),
    ("cat", Pipeline([("imp", SimpleImputer(strategy="most_frequent")),
                      ("oh", OneHotEncoder(handle_unknown="ignore"))]), CAT),
    ("bin", "passthrough", BIN),
])

# results.md 결론: 세 모델이 구분되지 않으므로 가장 단순하고 안정적인 것을 쓴다
# (LogReg 는 그룹 분할에서도 성능 하락이 가장 작았다: +0.0013)
pipe = Pipeline([("pre", pre), ("model", LogisticRegression(max_iter=2000, random_state=SEED))])
pipe.fit(X, y)
pred = pipe.predict(X_test).astype(int)

# ── 1. 제출 형식 확인 ──────────────────────────────────────────
sample_path = ROOT / "data/sample_submission.csv"
if sample_path.exists():
    sample = pd.read_csv(sample_path)
    cols, ids = list(sample.columns), sample.iloc[:, 0].values
else:
    # 이 미러에는 sample 이 없다. Kaggle Titanic 공식 규격을 따른다.
    cols, ids = ["PassengerId", "Survived"], te.PassengerId.values
    print("  ⓘ sample_submission.csv 없음 → 대회 공식 규격(PassengerId, Survived) 사용")

sub = pd.DataFrame({cols[0]: te.PassengerId.values, cols[1]: pred})

# ── 2. 자동 검증 ───────────────────────────────────────────────
checks = [
    ("행 수 일치", len(sub) == len(te), f"{len(sub)} vs {len(te)}"),
    ("컬럼명 정확", list(sub.columns) == cols, f"{list(sub.columns)}"),
    ("결측 없음", sub.isna().sum().sum() == 0, f"{int(sub.isna().sum().sum())}건"),
    ("예측값 범위", set(sub[cols[1]].unique()) <= {0, 1}, f"{sorted(sub[cols[1]].unique())}"),
    ("ID 일치(순서 포함)", np.array_equal(sub[cols[0]].values, ids), "—"),
    ("ID 중복 없음", sub[cols[0]].duplicated().sum() == 0, "—"),
]
print("=== 제출 파일 검증 ===")
fail = 0
for name, ok, detail in checks:
    print(f"  {'✓' if ok else '✗'} {name:20s} {detail}")
    fail += (not ok)
if fail:
    print(f"\n  ✗ {fail}건 실패 — 제출하면 거부되거나 0점 처리된다")
    sys.exit(1)

out_dir = ROOT / "submissions"; out_dir.mkdir(exist_ok=True)
n = len(list(out_dir.glob("sub_*.csv"))) + 1
out = out_dir / f"sub_{n:02d}.csv"
sub.to_csv(out, index=False, encoding="utf-8-sig")

print(f"\n=== 제출 파일 ===")
print(f"  {out}  ({len(sub)}행)")
print(f"  예측 분포: 사망 {(pred==0).sum()} / 생존 {(pred==1).sum()} "
      f"(생존율 {pred.mean():.1%})")
print(f"  학습 데이터 생존율 {y.mean():.1%} — "
      f"{'유사' if abs(pred.mean()-y.mean()) < 0.08 else '⚠ 크게 다름. 확인 필요'}")
