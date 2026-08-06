"""
/optimize 스킬 시운전 — 간호사 3교대 근무표 (CP-SAT)
실행: conda run --no-capture-output -n potato python optimize_test.py

스킬 절차 준수
  1. 정식화 (결정변수/목적함수/제약을 코드보다 먼저 — 아래 주석)
  2. 도구 선택: 조합·스케줄링 → OR-Tools CP-SAT
  3. 작은 예제로 먼저 (손으로 답을 아는 크기)
  4. 실제 규모로 확대
  5. 민감도 분석  ← 생략 금지
"""
from ortools.sat.python import cp_model

# ─────────────────────────────────────────────────────────────
# 1. 정식화 — 코드보다 먼저
#
#   결정변수 : x[n][d][s] = 간호사 n 이 d일 s교대에 근무하는가 (0/1)
#   목적함수 : 최소화 — 근무일수의 최대·최소 격차 (공평성)
#   제약     : (1) 각 교대에 정확히 required 명
#              (2) 하루 최대 1교대
#              (3) 야간 다음날 휴무 (연속근무 금지)
#              (4) 주당 최소 2일 휴무
#              (5) 개인 휴가 요청 존중
# ─────────────────────────────────────────────────────────────

SHIFTS = ["주간", "저녁", "야간"]


def solve(n_nurses, n_days, required, time_limit=20, demand_bump=None, verbose=True):
    """demand_bump: 민감도 분석용. 특정 교대 인원을 +1 하는 시나리오"""
    req = dict(required)
    # `if demand_bump:` 로 쓰면 안 된다 — 교대 인덱스 0(주간)이 거짓으로 처리되어
    # 그 시나리오가 조용히 건너뛰어진다. 시운전에서 실제로 걸린 버그다.
    if demand_bump is not None:
        req[demand_bump] = req[demand_bump] + 1

    m = cp_model.CpModel()
    x = {(n, d, s): m.NewBoolVar(f"x{n}_{d}_{s}")
         for n in range(n_nurses) for d in range(n_days) for s in range(len(SHIFTS))}

    # (1) 각 교대 필요 인원
    for d in range(n_days):
        for s in range(len(SHIFTS)):
            m.Add(sum(x[n, d, s] for n in range(n_nurses)) == req[s])

    # (2) 하루 최대 1교대
    for n in range(n_nurses):
        for d in range(n_days):
            m.Add(sum(x[n, d, s] for s in range(len(SHIFTS))) <= 1)

    # (3) 야간(2) 다음날은 휴무
    for n in range(n_nurses):
        for d in range(n_days - 1):
            for s in range(len(SHIFTS)):
                m.Add(x[n, d, 2] + x[n, d + 1, s] <= 1)

    # (4) 주당 최소 2일 휴무 (7일 창)
    for n in range(n_nurses):
        for w in range(0, n_days - 6):
            m.Add(sum(x[n, d, s] for d in range(w, w + 7)
                      for s in range(len(SHIFTS))) <= 5)

    # (5) 개인 휴가 요청 (간호사 0 은 0~2일, 간호사 1 은 3일)
    #     소규모 예제에서 범위를 벗어날 수 있으므로 존재하는 (간호사, 날짜)만 건다
    vacations = [(0, d) for d in (0, 1, 2)] + [(1, 3)]
    for n, d in vacations:
        if n < n_nurses and d < n_days:
            for s in range(len(SHIFTS)):
                m.Add(x[n, d, s] == 0)

    # 목적: 근무일수 격차 최소화 (공평성)
    worked = []
    for n in range(n_nurses):
        w = m.NewIntVar(0, n_days, f"w{n}")
        m.Add(w == sum(x[n, d, s] for d in range(n_days) for s in range(len(SHIFTS))))
        worked.append(w)
    lo, hi = m.NewIntVar(0, n_days, "lo"), m.NewIntVar(0, n_days, "hi")
    m.AddMinEquality(lo, worked); m.AddMaxEquality(hi, worked)
    m.Minimize(hi - lo)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    solver.parameters.random_seed = 42
    st = solver.Solve(m)
    name = solver.StatusName(st)

    if st not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        if verbose:
            print(f"  해 없음 ({name}) — 제약이 과하다")
        return None

    load = [solver.Value(w) for w in worked]
    return {"status": name, "gap": solver.Value(hi) - solver.Value(lo),
            "load": load, "sec": solver.WallTime()}


def capacity_check(label, n, days, req, n_vac_slots, max_per_7=5):
    """푸는 것보다 먼저 하는 산수. 여기서 걸리면 솔버를 돌릴 필요가 없다."""
    need = days * sum(req.values())
    cap = n * days * max_per_7 / 7 - n_vac_slots
    ok = cap >= need
    print(f"  [용량점검] {label}: 필요 {need} vs 공급상한 {cap:.0f} "
          f"→ {'여지 있음' if ok else f'구조적 실행불가 (부족 {need-cap:.0f})'}")
    if ok and cap - need < need * 0.05:
        print(f"             ⓘ 여유 {cap-need:.0f}슬롯({(cap-need)/need:.1%})뿐 — "
              f"추가 제약이 걸리면 깨지기 쉽다")
    return ok


print("=" * 72)
print("3. 작은 예제 — 손으로 검산 가능한 크기")
print("=" * 72)
capacity_check("5명/3일", 5, 3, {0: 2, 1: 1, 2: 1}, 3, max_per_7=7)
print("  → 여유가 0이라 '야간 다음날 휴무' 제약과 충돌한다. 6명으로 올린다.\n")
capacity_check("6명/3일", 6, 3, {0: 2, 1: 1, 2: 1}, 3, max_per_7=7)
small = solve(6, 3, {0: 2, 1: 1, 2: 1}, verbose=True)
if small:
    need = 3 * (2 + 1 + 1)          # 총 필요 근무 슬롯
    print(f"  {small['status']} · 근무일수 {small['load']} 합계 {sum(small['load'])}")
    print(f"  검산: 필요 슬롯 {need} == 배정 합계 {sum(small['load'])} "
          f"→ {'✓ 일치' if need == sum(small['load']) else '✗ 불일치'}")
    print(f"  간호사0 휴가(0~2일) 반영: 근무 {small['load'][0]}일 "
          f"→ {'✓' if small['load'][0] == 0 else '✗'}")

print()
print("=" * 72)
print("4. 실제 규모 — 간호사 16명 / 28일")
print("=" * 72)
BASE = {0: 4, 1: 3, 2: 2}
capacity_check("12명/28일", 12, 28, BASE, 4)
print("  → 12명으로는 구조적으로 불가능. 16명으로 올린다.\n")
capacity_check("16명/28일", 16, 28, BASE, 4)
full = solve(16, 28, BASE)
if full:
    print(f"  {full['status']} · 격차 {full['gap']}일 · {full['sec']:.2f}초")
    print(f"  근무일수 분포: 최소 {min(full['load'])} ~ 최대 {max(full['load'])}일")
    print(f"  간호사별: {full['load']}")

print()
print("=" * 72)
print("5. 민감도 분석 — 수요가 늘면 답이 얼마나 흔들리나 (생략 금지)")
print("=" * 72)
print(f"  {'시나리오':22s} {'상태':12s} {'격차':>5s} {'총근무':>7s} {'시간':>7s}")
rows = [("기준 (4/3/2)", None)] + [(f"{SHIFTS[s]} +1명", s) for s in range(3)]
base_total = sum(full["load"]) if full else 0
for label, bump in rows:
    r = solve(16, 28, BASE, demand_bump=bump)
    if r:
        tot = sum(r["load"])
        delta = f"{tot - base_total:+d}" if bump is not None else "—"
        print(f"  {label:22s} {r['status']:12s} {r['gap']:5d} {tot:7d} {r['sec']:6.2f}s  ({delta})")
    else:
        print(f"  {label:22s} {'실행불가':12s} {'—':>5s} {'—':>7s}   ← 제약 충돌")

print()
print("  해석: 어느 교대에 인원을 더해도 실행가능하고 공평성 격차가 유지되면")
print("        그 최적해는 수요 변동에 강건하다. 하나라도 실행불가가 나오면")
print("        그 방향의 여유가 없다는 뜻이므로 현장에 알려야 한다.")
