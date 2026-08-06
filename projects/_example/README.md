# 완주 예제 — Titanic으로 워크플로 한 바퀴

킷을 만들면서 **전 과정을 실제로 돌려본 기록**이다.
"좋은 산출물이 어떻게 생겼는지" 궁금하면 여기를 보면 된다.

무거운 것(데이터·HTML·PPTX·그림·저자 코드 클론)은 지웠고,
**스크립트와 마크다운만** 남겼다. 다시 돌리면 전부 재생성된다.

---

## 무엇을 보면 되나

| 궁금한 것 | 볼 파일 |
| --- | --- |
| 실험 결과를 어떻게 기록하나 | **`results.md`** ← 여기부터 |
| 보고서는 어떻게 생겼나 | `reports/report-titanic-20260806.md` |
| 데이터 출처는 어떻게 남기나 | `sources.md` |
| 경진대회 이력은 | `submissions.md` |
| EDA 코드 | `eda.py` |
| 모델 비교 코드 | `train_compare.py`(v1) → `train_compare_v2.py`(감사 반영) |
| 논문 재현 시 어댑터 | `adapters/titanic_adapter.py` |
| 최적화 문제 | `optimize_test.py` |
| 공공데이터 수집 | `collect_busan_climate.py` |

---

## 이 예제에서 실제로 일어난 일

**감사 에이전트가 실험을 무너뜨렸다.** `train_compare.py`(v1)의 결론이
`methods-reviewer` 감사에서 **fail** 판정을 받았고, 그래서 `train_compare_v2.py`를
새로 썼다. 두 파일을 나란히 보면 무엇이 어떻게 틀렸는지 알 수 있다.

지적받은 것 중 핵심 셋:

1. **`GroupKFold`는 층화를 하지 않는다** — `StratifiedKFold` 결과와 빼서 "누수"라고
   불렀는데, 거기에 층화 상실과 단일분할 노이즈가 섞여 **누수를 1.5배 과대평가**했다.
   → `StratifiedGroupKFold` 로 교체
2. **단일 시드 순위는 우연** — 시드 42에서 1위였던 모델이 5시드 평균에서는 꼴찌.
   모델 간 격차(0.0016)가 시드 변동(0.0040)보다 작아 **구분 불가**가 정답이었다
3. **KS 검정 오용** — `p>0.05`를 "차이 없음"의 근거로 썼고(귀무가설 채택),
   이산변수에 연속형 검정을 적용했다

이 세 가지 교훈은 스킬 문서(`/potato-experiment`, `/potato-eda`)에 반영돼 있다.

---

## 다시 돌려보려면

```bash
# 1) 데이터 받기 (지웠으므로)
mkdir -p data
curl -fsSL -o data/train.csv https://raw.githubusercontent.com/agconti/kaggle-titanic/master/data/train.csv
curl -fsSL -o data/test.csv  https://raw.githubusercontent.com/agconti/kaggle-titanic/master/data/test.csv

# 2) 순서대로
conda run --no-capture-output -n potato python eda.py               # → reports/eda-train.html
conda run --no-capture-output -n potato python train_compare_v2.py  # → reports/cv_v2_summary.csv
conda run --no-capture-output -n potato python predict.py           # → submissions/sub_01.csv
conda run --no-capture-output -n potato python optimize_test.py     # 최적화 (ortools 필요)
conda run --no-capture-output -n potato python collect_busan_climate.py  # 공공데이터 수집
conda run --no-capture-output -n potato python make_slides.py       # → reports/slides-*.pptx
```

추가로 필요한 패키지: `conda run -n potato pip install ortools python-pptx markdown`

`reproduce_pytabkit.py`는 저자 코드(`external/pytabkit`)와 별도 conda 환경이
필요하므로 그대로는 안 돌아간다. **논문 재현의 구조**(어댑터로 데이터를 맞추고,
저자 코드는 건드리지 않고, 폴드 내부에서 대치하는 방식)를 보는 용도로 남겨뒀다.

---

## 주의

이 예제의 목적은 **워크플로 시운전**이지 타이타닉 문제 해결이 아니다.
하이퍼파라미터 튜닝도, 리더보드 제출도 하지 않았다.
성능 수치를 참고값으로 쓰지 말 것 — `results.md`의 "한계" 절에 다 적어뒀다.
