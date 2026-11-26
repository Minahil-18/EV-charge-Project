"""Arithmetic checks for Sections 3 and 4 (no game-tree solver -- just the numbers).

Run:  python -m theory.calculations
"""
import csv
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "starter_data"

# ---------------------------------------------------------------- Section 3A
G = {("C", "C"): (4, 4), ("C", "H"): (0, 6), ("H", "C"): (6, 0), ("H", "H"): (1, 1)}
A = ("C", "H")


def section_3a():
    print("== 3A normal form ==")
    br1 = {b: max(A, key=lambda a: G[(a, b)][0]) for b in A}
    br2 = {a: max(A, key=lambda b: G[(a, b)][1]) for a in A}
    print("P1 best response to P2:", br1, "| P2 best response to P1:", br2)
    ne = [(a, b) for a in A for b in A if br1[b] == a and br2[a] == b]
    print("pure Nash equilibria:", ne, "payoffs", [G[x] for x in ne])
    best_joint = max(G, key=lambda k: sum(G[k]))
    print("best joint outcome:", best_joint, G[best_joint])
    assert ne == [("H", "H")] and best_joint == ("C", "C")
    # sequential: P2 observes P1
    p2_plan = {a: br2[a] for a in A}
    p1 = max(A, key=lambda a: G[(a, p2_plan[a])][0])
    print("backward induction: P2 plan", p2_plan, "P1 chooses", p1,
          "path", (p1, p2_plan[p1]), "payoffs", G[(p1, p2_plan[p1])])


# ---------------------------------------------------------------- Section 3B/C
def section_3b_3c():
    print("\n== 3B memory tree (full information, backward induction) ==")
    leaves = {(r["p1_first"], r["p2_action"], r["p1_second"]): (int(r["p1_payoff"]), int(r["p2_payoff"]))
              for r in csv.DictReader(open(DATA / "memory_tree.csv"))}
    LR = ("L", "R")
    p1_late = {(a, b): max(LR, key=lambda c: leaves[(a, b, c)][0]) for a in LR for b in LR}
    val_after = {(a, b): leaves[(a, b, p1_late[(a, b)])] for a in LR for b in LR}
    p2 = {a: max(LR, key=lambda b: val_after[(a, b)][1]) for a in LR}
    root = max(LR, key=lambda a: val_after[(a, p2[a])][0])
    path = (root, p2[root], p1_late[(root, p2[root])])
    print("P1 later moves:", p1_late)
    print("P2 moves:", p2)
    print("P1 root:", root, "| path:", path, "| payoffs:", leaves[path])
    assert path == ("L", "L", "R") and leaves[path] == (8, 4)

    print("\n== 3C mixed vs behavioral (P2 fixed to L) ==")
    u = {"LL": leaves[("L", "L", "L")][0], "LR": leaves[("L", "L", "R")][0],
         "RL": leaves[("R", "L", "L")][0], "RR": leaves[("R", "L", "R")][0]}
    print("P1 payoffs by action pair:", u)
    mixed = {"LL": .5, "LR": 0, "RL": 0, "RR": .5}
    fresh = {k: .25 for k in u}
    recall = {"LL": .5 * 1, "LR": .5 * 0, "RL": .5 * 0, "RR": .5 * 1}   # repeat remembered first action
    for name, p in [("mixed 50-50 lottery", mixed), ("fresh 50-50 draws (forgot stage)", fresh),
                    ("behavioral with perfect recall", recall)]:
        assert abs(sum(p.values()) - 1) < 1e-12
        ev = sum(p[k] * u[k] for k in u)
        print(f"  {name:34s} probs={p}  sum={sum(p.values())}  E[u1]={ev}")
    assert sum(mixed[k] * u[k] for k in u) == 1.5 and sum(fresh[k] * u[k] for k in u) == 4.25


# ---------------------------------------------------------------- Section 4A
def section_4a():
    print("\n== 4A repeated game ==")
    print("Finite (3 rounds): stage NE (H,H) is unique and in dominant strategies,")
    print("  so round 3 is (H,H); rounds 2 and 1 then cannot affect the future -> (H,H) each round.")
    print("  total per player (undiscounted) =", 3 * 1)
    # grim trigger: 4/(1-d) >= 6 + d/(1-d)  <=>  4 >= 6(1-d) + d  <=>  d >= 0.4
    threshold = 2 / 5
    print("Threshold: 4/(1-d) >= 6 + d/(1-d)  ->  4 >= 6 - 5d  ->  d >= 0.4")
    for d in (0.2, 0.4, 0.5):
        coop = 4 / (1 - d)
        dev = 6 + d / (1 - d)
        ext = 4 + 4 * d + 6 * d ** 2 + d ** 3 / (1 - d)
        print(f"  d={d}: cooperate={coop:.4f}  deviate now={dev:.4f}  "
              f"coop twice then deviate={ext:.4f}  -> {'C sustained' if coop >= dev else 'deviation pays'}")
    assert abs(4 / (1 - .5) - 8) < 1e-12 and abs(6 + .5 / .5 - 7) < 1e-12
    assert abs(4 / .8 - 5) < 1e-12 and abs(6 + .2 / .8 - 6.25) < 1e-12
    print("Punishment phase: opponent plays H, so H gives 1 > C gives 0 -> H stays a best response.")
    # finite formula check: r(1-d^T)/(1-d)
    print("  check finite formula, r=1,T=3,d=0.5:", 1 * (1 - .5 ** 3) / (1 - .5))


# ---------------------------------------------------------------- Section 4B
def section_4b(pi=0.30, fee=1.5):
    print("\n== 4B Bayesian game (F=1.5, pi=0.30) ==")
    alpha = {"urgent": 0, "flexible": 1}
    plan = {"urgent": "C", "flexible": "H"}
    prior = {"urgent": pi, "flexible": 1 - pi}

    def u(own, opp, own_type):
        base = G[(own, opp)][0]
        return base - fee + alpha[own_type] if own == "H" else base

    is_bne = True
    for t in ("urgent", "flexible"):
        ev = {a: sum(prior[o] * u(a, plan[o], t) for o in prior) for a in A}
        terms = {a: " + ".join(f"{prior[o]:.2f} x {u(a, plan[o], t):g}" for o in prior) for a in A}
        best = max(A, key=lambda a: ev[a])
        print(f"  {t:8s} C: {terms['C']} = {ev['C']:.2f}   H: {terms['H']} = {ev['H']:.2f}"
              f"   best={best} plan={plan[t]}")
        is_bne &= best == plan[t]
    print("  (both players are symmetric, so the same check covers P1 and P2)")
    print("  Bayesian Nash equilibrium:", is_bne)
    assert is_bne


if __name__ == "__main__":
    section_3a()
    section_3b_3c()
    section_4a()
    section_4b()
    print("\nAll theory checks passed.")
