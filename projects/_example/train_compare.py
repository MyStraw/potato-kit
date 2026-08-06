"""
모델 비교 — Titanic (potato-kit 시운전)
실행: conda run --no-capture-output -n potato python train_compare.py

설계 원칙 (CLAUDE.md 준수)
  - 모든 전처리는 Pipeline 안에서 → 폴드 내부에서만 fit (누수 방지)
  - 시드 고정 (42)
  - 동일 폴드·동일 전처리로 공정 비교
  - EDA에서 발견한 Ticket 누수 위험을 GroupKFold로 별도 검증
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
from sklearn.model_selection import GroupKFold, StratifiedKFold, cross_validate
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

warnings.filterwarnings("ignore")
SEED = 42
ROOT = Path(__file__).parent
train = pd.read_csv(ROOT / "data/train.csv")


def make_features(df):
    """타깃을 쓰지 않는 파생 변수만 여기서. 타깃 기반 인코딩은 파이프라인 안에서."""
    d = df.copy()
    d["Title"] = (d.Name.str.extract(r",\s*([^\.]+)\.", expand=False).str.strip()
                  .replace(["Mlle", "Ms"], "Miss").replace("Mme", "Mrs"))
    common = ["Mr", "Miss", "Mrs", "Master"]
    d["Title"] = d.Title.where(d.Title.isin(common), "Rare")
    d["FamilySize"] = d.SibSp + d.Parch + 1
    d["IsAlone"] = (d.FamilySize == 1).astype(int)
    d["HasCabin"] = d.Cabin.notna().astype(int)
    return d


data = make_features(train)
y = data.Survived.values
groups = data.Ticket.values          # 누수 검증용 그룹
NUM = ["Age", "Fare", "FamilySize", "SibSp", "Parch"]
CAT = ["Sex", "Pclass", "Embarked", "Title"]
BIN = ["IsAlone", "HasCabin"]
X = data[NUM + CAT + BIN]

pre = ColumnTransformer([
    ("num", Pipeline([("imp", SimpleImputer(strategy="median")),
                      ("sc", StandardScaler())]), NUM),
    ("cat", Pipeline([("imp", SimpleImputer(strategy="most_frequent")),
                      ("oh", OneHotEncoder(handle_unknown="ignore"))]), CAT),
    ("bin", "passthrough", BIN),
])

MODELS = {
    "Baseline (최빈값)": DummyClassifier(strategy="most_frequent"),
    "LogisticRegression": LogisticRegression(max_iter=2000, random_state=SEED),
    "RandomForest": RandomForestClassifier(
        n_estimators=300, max_depth=6, min_samples_leaf=4,
        random_state=SEED, n_jobs=-1),
    "HistGradientBoosting": HistGradientBoostingClassifier(
        max_depth=6, learning_rate=0.05, max_iter=300, random_state=SEED),
}

SCORING = ["accuracy", "roc_auc"]


def evaluate(cv, cv_groups=None):
    rows = []
    for name, model in MODELS.items():
        pipe = Pipeline([("pre", pre), ("model", model)])
        r = cross_validate(pipe, X, y, cv=cv, scoring=SCORING,
                           groups=cv_groups, n_jobs=1)
        rows.append({
            "모델": name,
            "Accuracy": r["test_accuracy"].mean(),
            "Acc_std": r["test_accuracy"].std(),
            "ROC-AUC": r["test_roc_auc"].mean(),
            "AUC_std": r["test_roc_auc"].std(),
        })
    return pd.DataFrame(rows)


print("=" * 74)
print("A) StratifiedKFold(5, shuffle=True, seed=42) — 표준 검증")
print("=" * 74)
skf = evaluate(StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED))
for _, r in skf.iterrows():
    print(f"  {r['모델']:24s} acc {r['Accuracy']:.4f} ± {r['Acc_std']:.4f}"
          f"   auc {r['ROC-AUC']:.4f} ± {r['AUC_std']:.4f}")

print()
print("=" * 74)
print("B) GroupKFold(5, groups=Ticket) — 같은 일행이 폴드를 넘지 않게")
print("=" * 74)
gkf = evaluate(GroupKFold(n_splits=5), cv_groups=groups)
for _, r in gkf.iterrows():
    print(f"  {r['모델']:24s} acc {r['Accuracy']:.4f} ± {r['Acc_std']:.4f}"
          f"   auc {r['ROC-AUC']:.4f} ± {r['AUC_std']:.4f}")

print()
print("=" * 74)
print("C) 검증 설계에 따른 차이 (A − B)")
print("=" * 74)
for (_, a), (_, b) in zip(skf.iterrows(), gkf.iterrows()):
    d_acc = a["Accuracy"] - b["Accuracy"]
    flag = "  ← 낙관적" if d_acc > max(a["Acc_std"], b["Acc_std"]) else ""
    print(f"  {a['모델']:24s} Δacc {d_acc:+.4f}   Δauc {a['ROC-AUC']-b['ROC-AUC']:+.4f}{flag}")

skf.to_csv(ROOT / "reports/cv_stratified.csv", index=False)
gkf.to_csv(ROOT / "reports/cv_group.csv", index=False)
print(f"\n결과 저장 → reports/cv_stratified.csv, reports/cv_group.csv")
