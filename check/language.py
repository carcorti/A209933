"""Bounded strategy diagnostic: verify a finite language certificate, not a campaign."""
import json, time, hashlib
from pathlib import Path

started = time.perf_counter()
classes = [L for L in range(1, 2521) if 2520 % L == 0 and L % 10]
assert len(classes) == 30
initial = {L: [L * 1111] for L in range(1, 9)}
initial.update({9: [1199, 9999], 12: [1332, 1333],
                18: [1999], 24: [2664, 2666], 36: [3999]})
closed = {L: {0: [(L, 0)]} for L in range(1, 9)}
closed.update({9: {0: [(9, 0)], 2: [(9, 2)]},
               12: {0: [], 1: [(2, 0), (3, 1)]},
               18: {1: [(9, 1)]},
               24: {0: [], 2: [(4, 0), (6, 2)]},
               36: {3: [(9, 3)]}})
rows = []
for L in classes:
    divisors = [d for d in range(1, L + 1) if L % d == 0]
    alphabet = {str(c) for c in range(1, 10) if L % c == 0}
    def allowed(P):
        return all(P // d == 0 or set(str(P // d)) <= alphabet
                   for d in divisors)
    actual_initial = [P for P in range(1000, 10000) if allowed(P)]
    assert actual_initial == initial.get(L, []), (L, actual_initial)
    small = [P for P in range(1, 1000) if P % L == 0 and allowed(P)]
    expected_small = ([L, 11*L, 111*L] if L <= 9 else
                      [12, 132] if L == 12 else
                      [15] if L == 15 else
                      [24, 48, 264] if L == 24 else [])
    assert small == expected_small, (L, small)
    graph = closed.get(L, {})
    assert {P % L for P in actual_initial} == set(graph)
    for r, wanted in graph.items():
        actual = [(x, (10*r+x) % L) for x in range(1, 10)
                  if all(str((10*(r % d)+x)//d) in alphabet
                         for d in divisors)]
        assert actual == wanted, (L, r, actual)
        assert all(dest in graph for x, dest in actual)
    rows.append(dict(L=L, alphabet=''.join(sorted(alphabet)),
                     small=small, initial4=actual_initial,
                     closed_transitions=graph))
print(json.dumps(dict(scope='Finite initial and closed-transition language certificate only; no new b-file values',
                      status='PASS', rows=rows,
                      initial_four_digit_checks=len(classes)*9000,
                      initial_small_checks=len(classes)*999,
                      positive_quotient_start=1000,
                      source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                      wall_seconds=time.perf_counter()-started), indent=2))
