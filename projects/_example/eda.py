"""
EDA — Titanic (potato-kit 시운전)
실행: conda run --no-capture-output -n potato python eda.py
산출: reports/eda-train.html
"""
import base64, io, platform, warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

warnings.filterwarnings("ignore")

plt.rcParams["font.family"] = {
    "Windows": "Malgun Gothic", "Darwin": "AppleGothic"
}.get(platform.system(), "NanumGothic")
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["figure.dpi"] = 110

ROOT = Path(__file__).parent
TARGET = "Survived"
train = pd.read_csv(ROOT / "data/train.csv")
test = pd.read_csv(ROOT / "data/test.csv")

figs, notes = [], []


def add_fig(fig, caption):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    figs.append((base64.b64encode(buf.getvalue()).decode(), caption))


# ── 1. 기본 점검 ────────────────────────────────────────────────
n_rows, n_cols = train.shape
miss = (train.isna().mean() * 100).sort_values(ascending=False)
miss = miss[miss > 0]
dup = int(train.duplicated().sum())
const_cols = [c for c in train.columns if train[c].nunique(dropna=False) <= 1]
id_like = [c for c in train.columns if train[c].nunique() == len(train)]
tgt = train[TARGET].value_counts(normalize=True).sort_index()

# 결측 패턴
miss_pattern = train[miss.index].isna().astype(int).corr() if len(miss) > 1 else None

# ── 2. 타깃 분포 ────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(4, 3))
ax.bar(["사망(0)", "생존(1)"], tgt.values, color=["#c44", "#4a8"])
for i, v in enumerate(tgt.values):
    ax.text(i, v + 0.01, f"{v:.1%}", ha="center")
ax.set_ylim(0, 0.75); ax.set_ylabel("비율"); ax.set_title("타깃 분포")
add_fig(fig, f"타깃 불균형은 약한 편(61.6% vs 38.4%). "
             f"층화 분할(StratifiedKFold)이면 충분하고 리샘플링까지는 불필요해 보인다.")

# ── 3. 결측 ────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(5, 3))
ax.barh(miss.index[::-1], miss.values[::-1], color="#d88")
for i, v in enumerate(miss.values[::-1]):
    ax.text(v + 1, i, f"{v:.1f}%", va="center", fontsize=9)
ax.set_xlim(0, 100); ax.set_xlabel("결측률 (%)"); ax.set_title("컬럼별 결측")
add_fig(fig, "Cabin은 77% 결측이라 대치보다 '선실 정보 유무' 플래그가 낫다. "
             "Age 20%는 대치 대상이지만 단순 중앙값은 아래 Pclass별 분포를 보면 부적절하다.")

# ── 4. 범주형 vs 타깃 ──────────────────────────────────────────
cats = ["Sex", "Pclass", "Embarked", "SibSp", "Parch"]
fig, axes = plt.subplots(1, len(cats), figsize=(16, 3))
for ax, c in zip(axes, cats):
    r = train.groupby(c)[TARGET].mean()
    ax.bar(r.index.astype(str), r.values, color="#5a8fd6")
    ax.axhline(train[TARGET].mean(), ls="--", c="gray", lw=1)
    ax.set_title(c, fontsize=10); ax.set_ylim(0, 1)
    ax.set_ylabel("생존율" if c == "Sex" else "")
add_fig(fig, "Sex의 판별력이 압도적(여성 74% vs 남성 19%). Pclass도 단조 관계가 뚜렷하다. "
             "점선은 전체 평균 생존율.")

# ── 5. 수치형 분포 ─────────────────────────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(13, 3))
axes[0].hist([train[train[TARGET] == 0]["Age"].dropna(),
              train[train[TARGET] == 1]["Age"].dropna()],
             bins=25, stacked=True, color=["#c44", "#4a8"], label=["사망", "생존"])
axes[0].legend(fontsize=8); axes[0].set_title("Age 분포"); axes[0].set_xlabel("Age")

axes[1].hist(train["Fare"], bins=40, color="#5a8fd6")
axes[1].set_yscale("log"); axes[1].set_title("Fare 분포 (y=log)"); axes[1].set_xlabel("Fare")

train.boxplot(column="Age", by="Pclass", ax=axes[2])
axes[2].set_title("Pclass별 Age"); axes[2].set_xlabel("Pclass"); plt.suptitle("")
add_fig(fig, "Age는 어린이 구간에서 생존이 상대적으로 높다(비선형). "
             "Fare는 강한 우편향에 극단값이 존재. Pclass별 Age 중앙값이 뚜렷이 달라 "
             "**전체 중앙값 대치는 부적절**하고 Pclass·호칭별 대치가 맞다.")

# ── 6. 상관 ────────────────────────────────────────────────────
num = train.select_dtypes(include=[np.number]).drop(columns=["PassengerId"])
fig, ax = plt.subplots(figsize=(5, 4))
im = ax.imshow(num.corr(), cmap="RdBu_r", vmin=-1, vmax=1)
ax.set_xticks(range(len(num.columns))); ax.set_xticklabels(num.columns, rotation=45, ha="right", fontsize=8)
ax.set_yticks(range(len(num.columns))); ax.set_yticklabels(num.columns, fontsize=8)
for i in range(len(num.columns)):
    for j in range(len(num.columns)):
        ax.text(j, i, f"{num.corr().iloc[i, j]:.2f}", ha="center", va="center", fontsize=7)
fig.colorbar(im, ax=ax, shrink=0.8); ax.set_title("수치형 상관")
add_fig(fig, "Pclass–Fare(-0.55)가 강한 편. 타깃과의 선형 상관은 모두 약해 "
             "선형 모델만으로는 한계가 있고 상호작용을 잡는 트리 계열이 유리할 것으로 보인다.")

# ── 7. train/test 비교 ─────────────────────────────────────────
ks_rows = []
for c in ["Age", "Fare", "SibSp", "Parch", "Pclass"]:
    a, b = train[c].dropna(), test[c].dropna()
    s, p = stats.ks_2samp(a, b)
    ks_rows.append((c, s, p, "차이 없음" if p > 0.05 else "⚠ 분포 차이"))
id_overlap = len(set(train.PassengerId) & set(test.PassengerId))
test_only_emb = set(test.Embarked.dropna()) - set(train.Embarked.dropna())

# 누수 위험 점검
ticket_dup = int(train.Ticket.duplicated().sum())
ticket_cross = len(set(train.Ticket) & set(test.Ticket))

# ── 8. 특이값 ──────────────────────────────────────────────────
fare_zero = int((train.Fare == 0).sum())
fare_max = train.Fare.max()
fare_max_n = int((train.Fare == fare_max).sum())

# ── HTML ───────────────────────────────────────────────────────
def tbl(df):
    return df.to_html(index=False, border=0, classes="t", float_format=lambda x: f"{x:.4f}")

html = f"""<!doctype html><meta charset="utf-8"><title>EDA — train.csv</title>
<style>
body{{font-family:-apple-system,'Apple SD Gothic Neo',sans-serif;max-width:960px;margin:2rem auto;padding:0 1rem;line-height:1.6;color:#222}}
h1{{border-bottom:3px solid #5a8fd6;padding-bottom:.3rem}} h2{{margin-top:2.2rem;color:#2c5aa0}}
.t{{border-collapse:collapse;margin:.6rem 0}} .t td,.t th{{border:1px solid #ddd;padding:5px 10px;font-size:13px}}
.t th{{background:#f2f6fb}} .cap{{color:#555;font-size:14px;background:#f8f9fb;border-left:3px solid #5a8fd6;padding:.6rem .9rem;margin:.3rem 0 1.4rem}}
.warn{{background:#fff6e5;border-left-color:#e0a030}} img{{max-width:100%}}
code{{background:#f0f2f5;padding:1px 5px;border-radius:3px}}
</style>
<h1>EDA — train.csv</h1>
<p><b>potato-kit</b> 시운전 · 생성일 2026-08-06 · 데이터 Titanic (공개)</p>

<h2>1. 개요</h2>
<table class=t>
<tr><th>행 × 열</th><td>{n_rows} × {n_cols}</td></tr>
<tr><th>메모리</th><td>{train.memory_usage(deep=True).sum()/1024:.0f} KB</td></tr>
<tr><th>중복 행</th><td>{dup}</td></tr>
<tr><th>상수 컬럼</th><td>{const_cols or '없음'}</td></tr>
<tr><th>ID 추정 컬럼</th><td>{id_like}</td></tr>
<tr><th>데이터 성격</th><td>일반(i.i.d.) 표 형태 — 시간·공간 축 없음, 개체 반복측정 아님</td></tr>
</table>
<div class=cap>승객 단위 1행 = 1개체이므로 표준 층화 K-fold가 적절하다.
시계열·공간 분할이나 GroupKFold는 필요 없다. 다만 아래 6절의 Ticket 중복은 별도로 확인이 필요하다.</div>

<h2>2. 타깃 분포</h2>
<img src="data:image/png;base64,{figs[0][0]}"><div class=cap>{figs[0][1]}</div>

<h2>3. 결측</h2>
<img src="data:image/png;base64,{figs[1][0]}"><div class=cap>{figs[1][1]}</div>

<h2>4. 범주형 변수와 생존율</h2>
<img src="data:image/png;base64,{figs[2][0]}"><div class=cap>{figs[2][1]}</div>

<h2>5. 수치형 분포</h2>
<img src="data:image/png;base64,{figs[3][0]}"><div class=cap>{figs[3][1]}</div>

<h2>6. 상관</h2>
<img src="data:image/png;base64,{figs[4][0]}"><div class=cap>{figs[4][1]}</div>

<h2>7. train / test 분포 비교</h2>
{tbl(pd.DataFrame(ks_rows, columns=["변수","KS 통계량","p-value","판정"]))}
<div class=cap>모든 변수에서 p&gt;0.05로 <b>train과 test의 분포 차이가 없다</b>.
교차검증 점수를 리더보드 점수의 대리 지표로 신뢰할 수 있다는 뜻이다.
PassengerId 겹침 {id_overlap}건, test에만 있는 Embarked 범주 {test_only_emb or '없음'}.</div>

<h2>8. 누수·특이값 점검</h2>
<table class=t>
<tr><th>Ticket 중복 (train 내부)</th><td>{ticket_dup}건</td></tr>
<tr><th>Ticket이 train·test에 걸침</th><td>{ticket_cross}건</td></tr>
<tr><th>Fare = 0</th><td>{fare_zero}건</td></tr>
<tr><th>Fare 최댓값</th><td>{fare_max:.4f} ({fare_max_n}건, 동일 티켓 일행)</td></tr>
</table>
<div class="cap warn"><b>주의</b> — 같은 Ticket을 가진 일행이 train과 test에 나뉘어 들어가 있다({ticket_cross}건).
이 대회의 공식 분할이므로 그대로 쓰지만, <b>내부 교차검증에서 Ticket 단위로 나누지 않으면
같은 일행의 정보가 폴드를 넘나들어 점수가 낙관적으로 나온다.</b>
Fare=0은 결측이 아니라 무임 승선으로 보이며 대치 대상이 아니다.</div>

<h2>9. 다음 단계 제안</h2>
<ol>
<li><code>Title</code>(호칭)을 Name에서 추출 — Age 결측 대치의 근거로 쓴다</li>
<li><code>FamilySize</code> = SibSp + Parch + 1, <code>IsAlone</code></li>
<li><code>HasCabin</code> 플래그 (Cabin 77% 결측을 버리지 않고 쓰는 방법)</li>
<li>Age 대치는 <b>Pclass·Title 그룹 중앙값</b>으로, 반드시 <b>파이프라인 안에서</b></li>
<li>검증은 StratifiedKFold(5, shuffle=True, seed=42). Ticket 기준 GroupKFold도 함께 비교</li>
</ol>
"""

out = ROOT / "reports/eda-train.html"
out.parent.mkdir(exist_ok=True)
out.write_text(html, encoding="utf-8")

print(f"규모: {n_rows}행 x {n_cols}열 / 중복 {dup} / 타깃 {tgt.iloc[0]:.1%} vs {tgt.iloc[1]:.1%}")
print("결측:", ", ".join(f"{k} {v:.1f}%" for k, v in miss.items()))
print(f"Ticket 중복 {ticket_dup}, train-test 걸침 {ticket_cross}")
print("KS 검정:", ", ".join(f"{c} p={p:.3f}" for c, s, p, _ in ks_rows))
print(f"리포트 → {out}")
