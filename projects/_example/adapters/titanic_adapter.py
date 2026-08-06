"""
어댑터 — 우리 데이터(Titanic)를 pytabkit 이 기대하는 형태로 바꾼다.

/reproduce 스킬 원칙: **저자 코드를 수정하지 않는다.**
external/pytabkit 은 손대지 않고, 여기서 우리 데이터를 저자 API 에 맞춘다.

pytabkit 의 sklearn 인터페이스는 X(DataFrame), y(array) 를 받으며
범주형은 dtype 이 category 이면 알아서 처리한다.
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent

NUM = ["Age", "Fare", "FamilySize", "SibSp", "Parch"]
CAT = ["Sex", "Pclass", "Embarked", "Title"]
BIN = ["IsAlone", "HasCabin"]


def _features(df):
    d = df.copy()
    d["Title"] = (d.Name.str.extract(r",\s*([^\.]+)\.", expand=False).str.strip()
                  .replace(["Mlle", "Ms"], "Miss").replace("Mme", "Mrs"))
    d["Title"] = d.Title.where(d.Title.isin(["Mr", "Miss", "Mrs", "Master"]), "Rare")
    d["FamilySize"] = d.SibSp + d.Parch + 1
    d["IsAlone"] = (d.FamilySize == 1).astype(int)
    d["HasCabin"] = d.Cabin.notna().astype(int)
    return d


def load():
    """returns X(DataFrame), y(ndarray), groups(ndarray)"""
    raw = pd.read_csv(ROOT / "data/train.csv")
    d = _features(raw)
    X = d[NUM + CAT + BIN].copy()
    for c in CAT:
        X[c] = X[c].astype("category")      # pytabkit 은 category dtype 을 인식한다
    return X, d.Survived.values, d.Ticket.values


if __name__ == "__main__":
    X, y, g = load()
    print("어댑터 출력")
    print(f"  X {X.shape}, y {y.shape}, 그룹(Ticket) 고유 {len(np.unique(g))}")
    print(f"  범주형 {CAT} → dtype: {[str(X[c].dtype) for c in CAT]}")
    print(f"  결측: {dict(X.isna().sum()[X.isna().sum() > 0])}")
