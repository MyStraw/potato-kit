# 완주 예제 — Titanic 워크플로 시운전

> 2026-08-06 ~ 08-07 · potato-kit 검증용

## 목표

킷의 전 과정(EDA → 실험 → 감사 → 보고 → 발표 → 제출)이 실제로 동작하는지 확인한다.
Titanic 문제를 잘 푸는 것이 목적이 **아니다.**

## 진행 기록

- 08-06: `/potato-eda` — Ticket 중복 210건, train-test 걸침 115건 탐지
- 08-06: `/potato-experiment` v1 — 4모델 비교, GroupKFold로 누수 측정
- 08-06: `methods-reviewer` 감사 → **fail**. major 3 / minor 7 / info 5
- 08-06: v2 재실험 — StratifiedGroupKFold + 5시드. 누수 재측정 −0.0219
- 08-06: `/potato-report` → md, `/potato-slides` → 9장 pptx
- 08-07: `/potato-submit` 제출파일 검증 6항목 통과
- 08-07: `/potato-optimize` CP-SAT 근무표 + 민감도, `/potato-find-data` 공공데이터 수집
- 08-07: 정리 — 무거운 산출물 삭제, 예제로 전환
