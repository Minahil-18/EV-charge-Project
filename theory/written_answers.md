# Written game-theory answers (Sections 3 and 4)

All numbers below are reproduced by `python -m theory.calculations`.
The C/H table is a teaching table, **not** the simulator's energy formula.

## 3A Small normal and extensive form games

C = release, H = hold one slot. First payoff belongs to P1.

|        | P2 C      | P2 H        |
|--------|-----------|-------------|
| **P1 C** | (4, 4)    | (0, **6**)  |
| **P1 H** | (**6**, 0) | (**1**, **1**) |

Bold = best response.
- P1: against C, H gives 6 > 4; against H, H gives 1 > 0. **H is strictly dominant.** P2 is symmetric.
- **Unique pure Nash equilibrium: (H, H) with payoffs (1, 1).**
- The best joint outcome is (C, C) = (4, 4) (total 8 vs 2). It is not an equilibrium because each player gains 2 by switching to H alone. This is a prisoner's-dilemma structure: individual incentives work against shared use.

**Sequential version (P1 first, P2 observes):**
```
                P1
             /      \
           C          H
          P2          P2
         /  \        /  \
        C    H      C    H
     (4,4) (0,6)  (6,0) (1,1)
```
Backward induction: after C, P2 picks H (6 > 4); after H, P2 picks H (1 > 0).
P1 compares C → (0,6) and H → (1,1), so picks H.
- Complete strategies: **P1 = H; P2 = (H after C, H after H)**.
- Path: H then H. Payoffs **(1, 1)**.

**Hidden P1 move:** P2's two nodes are joined in one information set (dashed line below). P2 cannot condition on P1's move, so the game is the normal form above, and the equilibrium is again (H, H).
```
                P1
             /      \
           C          H
          P2 - - - - P2      (one information set)
         /  \        /  \
        C    H      C    H
```
This is **imperfect information** because P2 does not know which node it is at. It still has **perfect recall**: each player moves once, so nobody can forget their own earlier moves or observations.

## 3B Two kinds of forgotten information (memory_tree.csv)

Leaves (P1 first, P2, P1 second → payoffs):
LLL (1,3), LLR (8,4), LRL (6,1), LRR (0,2), RLL (6,5), RLR (2,2), RRL (3,4), RRR (1,1).

```
                         P1 (root)
                 L /                 \ R
                 P2                   P2
             L /    \ R           L /    \ R
            P1a      P1b         P1c      P1d
           /  \     /  \        /  \     /  \
          L    R   L    R      L    R   L    R
        (1,3)(8,4)(6,1)(0,2) (6,5)(2,2)(3,4)(1,1)
```

1. **Full information** (all nodes separate), backward induction:
   - P1a (L,L): R (8 > 1) → (8,4). P1b (L,R): L (6 > 0) → (6,1). P1c (R,L): L (6 > 2) → (6,5). P1d (R,R): L (3 > 1) → (3,4).
   - P2 after L: L gives 4, R gives 1 → **L**. P2 after R: L gives 5, R gives 4 → **L**.
   - P1 root: L → 8, R → 6 → **L**.
   - Equilibrium: P1 = (L at root; R at P1a, L at P1b, L at P1c, L at P1d), P2 = (L, L). **Path L-L-R, payoffs (8, 4).**
   - P1 knows its own first move, P2's move, and that it is the second visit.
2. **Forget own first action**: the root stays separate. Join {P1a, P1c} (P2 played L) and join {P1b, P1d} (P2 played R).
   P1 knows it is at the later move and sees P2's action, but not its own first action. One action must be chosen per information set, so P1 cannot play R at P1a and L at P1c. This is imperfect recall, because P1 forgot its own earlier action.
3. **Forget the stage**: join the root and all of P1a–P1d into **one** information set. P1 sees no clock, counter, earlier choice or P2 action, so it must use the same action (or the same randomisation) every time it moves. P2 still observes P1's first action.

(No full equilibrium is computed for cases 2 and 3, as the brief allows.)

## 3C Mixed vs behavioral (P2 fixed to L)

P1 payoffs: LL = 1, LR = 8, RL = 6, RR = 2.

| Strategy | P(LL) | P(LR) | P(RL) | P(RR) | Sum | E[u₁] |
|---|---|---|---|---|---|---|
| Mixed: 50-50 lottery over "always L" / "always R" | 0.5 | 0 | 0 | 0.5 | 1 | 0.5·1 + 0.5·2 = **1.5** |
| Behavioral, forgotten stage: fresh 50-50 at each visit | 0.25 | 0.25 | 0.25 | 0.25 | 1 | (1+8+6+2)/4 = **4.25** |
| Behavioral with perfect recall: 50-50 first, then repeat remembered action | 0.5 | 0 | 0 | 0.5 | 1 | **1.5** |

With perfect recall, the behavioral strategy reproduces the mixed lottery exactly, so the terminal probabilities are identical (Kuhn's theorem). With a forgotten stage, P1 cannot tell the first visit from the second and has no memory of its first action, so it cannot "repeat" anything. Its draws are independent, which also reaches LR and RL. Under imperfect recall, mixed and behavioral strategies are **not** equivalent (1.5 vs 4.25).

## 4A Finite and infinite repeated games

**Finite, 3 known rounds.** In round 3 there is no future, so the stage game is played and (H,H) is the unique NE (H is dominant). In round 2, round 3's outcome is fixed whatever happens now, so again (H,H). The same holds for round 1. **Outcome: (H,H) in all three rounds**, giving 1 per round, or 3 in total (r(1−δ³)/(1−δ) if discounted).

**Infinite, grim trigger.** δ is the weight placed today on a payoff received one round later.
- Cooperate forever: 4 + 4δ + 4δ² + … = 4/(1−δ)
- Deviate now: 6 + δ + δ² + … = 6 + δ/(1−δ)

Cooperation is sustained when 4/(1−δ) ≥ 6 + δ/(1−δ).
Multiplying by (1−δ): 4 ≥ 6(1−δ) + δ = 6 − 5δ, so **δ ≥ 0.4**.

| δ | Cooperate | Deviate now | Result |
|---|---|---|---|
| 0.2 | 4/0.8 = 5.00 | 6 + 0.2/0.8 = 6.25 | deviation pays |
| 0.5 | 4/0.5 = 8.00 | 6 + 0.5/0.5 = 7.00 | cooperation sustained |

**Punishment check:** once the opponent plays H forever, H gives 1 and C gives 0, so H remains a best response. The threat is credible.

**Optional:** cooperate twice, then deviate: 4 + 4δ + 6δ² + δ³/(1−δ). At δ=0.5 this gives 7.75 < 8, and at δ=0.2 it gives 5.05 > 5. The threshold is the same, 0.4. The 60-day simulation is finite and does not prove this infinite-horizon result.

## 4B Bayesian game (π = 0.30 Urgent, F = 1.5, Flexible +1 on own H)

Own payoffs: C/C 4, C/H 0, H/C 6 − 1.5 + α, H/H 1 − 1.5 + α, with α = 0 for Urgent and α = 1 for Flexible.
Proposed plan: Urgent → C, Flexible → H. So the opponent plays C with probability 0.30 and H with probability 0.70.

| Own type | E[C] | E[H] | Best | Plan |
|---|---|---|---|---|
| Urgent | 0.30×4 + 0.70×0 = **1.20** | 0.30×4.5 + 0.70×(−0.5) = **1.00** | C | C ✓ |
| Flexible | 0.30×4 + 0.70×0 = **1.20** | 0.30×5.5 + 0.70×0.5 = **2.00** | H | H ✓ |

The game is symmetric, so the same four numbers apply to P1 and P2. No type of either player gains by changing alone, so **the plan is a Bayesian Nash equilibrium.**

## 5A Evolutionary graph

`python -m theory.evolutionary` saves `results/evolutionary.png` and `.csv`.
- F = 0: fC − fH = −(1 + x) < 0, so **C becomes less common** (x: 0.5 → 0.124 after 30 updates).
- F = 2: fC − fH = 1 − x > 0, so **C becomes more common** (x: 0.5 → 0.653).
- First step check: fC = 2, fH = 3.5, x₁ = 0.48125 ✓. Every share stays in [0, 1].
- This is a model path, not proof of an ESS or a forecast of real drivers.
