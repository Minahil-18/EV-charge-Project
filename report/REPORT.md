# Fair Access to Shared EV Chargers: Does an Idle Penalty Help, and Whom?

*Game Theory / Multiagent Systems semester project. All data are synthetic teaching data and utilities are teaching points, not prices.*

---

## 1. Problem and research question

At a shared charging site, a driver may finish charging but leave the car plugged in to avoid moving it. The charger is then **idle but occupied**, and another driver waits. Real networks respond with idle fees: a charge for every minute a car stays connected after charging ends [1]. Drivers differ, though. An urgent driver loses a lot from waiting, while a flexible driver gains more from not having to move the car. So a rule that helps the average driver can still harm some drivers.

**Research question:** *Does an idle penalty reduce waiting, and how does it affect drivers with different needs?*

We compare two policies at one site with six chargers and a pool of 40 drivers:
- **P0:** first come, first served, no penalty.
- **P1:** the same queue order, with a penalty of **F = 2 points per idle slot**.

Each policy is run at three demand levels with five random seeds. The drivers' choices are then explained with small game-theory models: normal and extensive form, information and recall, mixed and behavioral strategies, repeated games, Bayesian games and evolutionary dynamics.

## 2. Reading

**Course book [2].** Chapter 3 (normal-form games, best responses, Nash equilibrium) underpins our C/H table. Chapter 5 (extensive form, backward induction, information sets, perfect and imperfect recall) underpins the memory-tree exercise. Section 6.1 (finitely and infinitely repeated games, discounting, trigger strategies) and Section 6.3 (Bayesian games, types, Bayes–Nash equilibrium) underpin Section 6 of this report. Section 7.7 (evolutionary learning, replicator dynamics) underpins the evolutionary graph.

**Research paper: Lee, Li and Low (2019), ACN-Data [3].**
- *Problem:* EV-charging research lacked large, open records of real charging sessions. The paper introduces a public dataset collected from workplace charging sites with adaptive charging, and shows how it can be used to study driver behaviour and charging-scheduling algorithms.
- *Players:* the drivers who connect their cars, and the site operator who allocates limited capacity across many connected cars.
- *Choices:* drivers choose when to arrive, how long to stay connected and how much energy to request. The operator chooses how to schedule power among connected cars.
- *One difference from our project:* ACN-Data records what happened (connection, disconnection, energy delivered). It does not reveal a driver's urgency, true energy need, private utility, or *why* a car stayed connected. Our project instead uses **synthetic drivers with known private types and programmed rules**. We can therefore attribute idle time to a decision and measure utility, but we cannot claim that our numbers describe a real campus.

**Context [1], [4].** Idle fees in public networks [1] motivate P1. The evolutionary model of shared charging in [4] uses different players (distribution entities rather than individual drivers) and a different payoff structure. We use it only as an example of evolutionary analysis applied to shared charging.

## 3. Model and assumptions

**Time and capacity.** One site has six identical 6 kW chargers. A day has 16 half-hour slots (boundaries 0–16 cover 08:00–16:00). A charger delivers at most 3 kWh per full slot and never more than the energy still requested.

**Requests.** `sessions_public.csv` (regenerated for each seed) holds 4,320 requests per seed: 720 at low demand, 1,440 at medium and 2,160 at high, each over 60 days. Each request has an arrival slot, a departure slot and a requested energy. Demand levels are run separately.

**Actions after a full charge:** Release, Hold 1 or Hold 2. A hold must end at or before departure. Only one hold decision is allowed, and holds cannot be extended. A car that finishes exactly at its departure time is forced to release.

**Utility** (per visit):

> U = v·kWh − w·waiting slots + h·idle slots − F·idle slots

| Type | v (per kWh) | w (per wait slot) | h (per idle slot) |
|---|---|---|---|
| Urgent | 3 | 3 | 1 |
| Flexible | 2 | 1 | 2 |

Waiting ends when charging starts. An unserved driver waits from arrival to departure. F = 0 under P0 and F = 2 under P1. We report utility **before** and **after** the penalty separately.

**Driver rules** (from `private_strategy`): **Release** always releases. **Hold** takes the largest legal hold, up to 2 slots. **Reciprocal** releases on the first visit; afterwards it releases if the last visit was fully served with at most 2 waiting slots, and otherwise holds 1 slot if legal. **Fee aware** maximises (h − F)·O over legal O and releases on ties. The pool has 10 drivers of each rule. The number of Urgent drivers varies by seed (12, 11, 15, 10 and 6 for seeds 0–4) around the model prior of 0.30.

**Information.** A driver knows its own type, request and history. It sees the current queue length and the fee. It never sees another driver's private row, strategy label or future arrivals.

**Recorded modelling choices.** Ties in the queue are broken by arrival slot, then driver ID. Free chargers are filled in charger-ID order. Energy for slot [t, t+1) is credited at boundary t+1. "Fully served" means delivered = requested. Missing values are written `NA`. Reciprocal memory persists across days within a run and is reset between runs.

## 4. Simulator design

The code is Python (`sim/`). It has three layers:

1. **Agents (`sim/rules.py`).** Each `Driver` object is built from **one** private row and decides from a public `Observation` (time, own departure, fee, queue length). Nothing else is passed in, so a driver cannot read another driver's row.
2. **Engine (`sim/engine.py`).** This simulates one day. At every boundary t it (1) credits the energy delivered in the previous slot, (2) removes departures, including incomplete and unserved drivers, (3) takes the release or hold choice from newly completed drivers and ends expiring holds, then (4) adds arrivals, allocates free chargers by (arrival, ID) and charges during [t, t+1). Nothing is charged after boundary 16.
3. **Runner (`run_experiments.py`).** This runs one 60-day scenario. Queues reset every day, while driver memory persists within a run. Every visit is saved with its arrival, start, finish, release, energy, waiting, action, idle slots, penalty and utility before/after the penalty. Settings, input-file hashes and summaries are saved to `results/`.

**Verification.**
- **Mini case (one charger, three drivers, P0):** with everyone releasing, starts are 0/2/3, waiting 4, energy 15 kWh and utility 25. With A holding one slot, starts are 0/3/4, waiting 6 and utility 23. Every per-driver value in `mini_case_expected.json` matches (`check_mini_case.py`).
- **Safety checks on every run (721,602 checks):** no charger serves two drivers in the same slot. No energy is delivered before arrival, after departure or during a hold. Delivered energy never exceeds the request. Unserved drivers carry the full waiting cost. A hold always ends exactly at finish + idle slots.
- **Determinism:** identical inputs and settings give identical visit records (`run_all_checks.py`).

The results screen (`app/results_app.py`, Streamlit) reads only the saved files, so every displayed number matches them. It lets the user choose the demand level, policy and seed, and shows the settings and input files used. It also has a charger timeline, comparisons by type and by rule, the paired seed comparison, the game-theory calculations, the evolutionary graph and the mini case re-run live.

## 5. Experiments

- **Inputs:** five input sets generated with the supplied generator: `generate_data.py --seed k --urgent-prior 0.30` for k = 0–4 (`data/seed_k/`).
- **Main runs:** 2 policies × 3 demand levels × 5 seeds = **30 runs** of 60 days each. Within a seed, requests, types and starting rules are identical across policies, and all state is reset between runs.
- **Limit check:** at medium demand every driver is set to fixed Hold, under both policies, for the same five seeds (**10 runs**).
- **Comparison method:** P1 − P0 is computed **within each seed first**. We then report the mean change and the min–max range over the five seeds (`results/paired_comparison.csv`).

## 6. Findings

### 6.1 Waiting and completion (mean over five seeds)

| Demand | Avg wait P0 | Avg wait P1 | Change [seed range] | Fully served P0 → P1 | Energy change (kWh) | Idle slots P0 → P1 |
|---|---|---|---|---|---|---|
| Low    | 0.521 | 0.380 | **−0.141** [−0.158, −0.124] | 93.2% → 95.0% | +78 | 559 → 283 |
| Medium | 2.877 | 2.635 | **−0.241** [−0.253, −0.224] | 59.8% → 63.3% | +518 | 681 → 417 |
| High   | 4.257 | 4.102 | **−0.155** [−0.174, −0.133] | 38.2% → 40.7% | +614 | 615 → 393 |

The idle penalty **reduces average waiting at every demand level, and all five seeds agree in sign**. It also raises completion and delivered energy. The effect is largest at medium demand. At low demand there is little queue to clear. At high demand the six chargers are so congested that freeing a few idle slots helps only marginally (fewer than 41% of requests are fully served even under P1).

### 6.2 By driver type

| Demand | Urgent wait change | Flexible wait change | Urgent served change | Flexible served change |
|---|---|---|---|---|
| Low    | −0.154 | −0.138 | +2.0 pp | +1.8 pp |
| Medium | −0.240 | −0.241 | +3.5 pp | +3.5 pp |
| High   | −0.152 | −0.155 | +2.3 pp | +2.5 pp |

Both types wait less and complete more often under P1, by almost the same amount. The queue is first come, first served, so the freed capacity is shared without regard to type.

### 6.3 Who gains and who loses (utility)

**Total utility change (points, P1 − P0, mean over seeds):**

| Demand | Before penalty | Penalty paid | After penalty [range] |
|---|---|---|---|
| Low    | −146 | 566 | **−712** [−858, −590] |
| Medium | +1,262 | 834 | **+428** [+300, +527] |
| High   | +1,514 | 786 | **+728** [+594, +916] |

**Average utility per visit after the penalty (P1 − P0):**

| Group | Low | Medium | High |
|---|---|---|---|
| Urgent | −0.66 | +0.94 | +0.75 |
| Flexible | −1.13 | +0.03 | +0.17 |
| Release rule | +0.49 | +1.38 | +0.86 |
| Reciprocal rule | +0.26 | +0.45 | +0.51 |
| Hold rule | **−2.54** | −0.52 | −0.02 |
| Fee-aware rule | **−2.05** | −0.13 | +0.00 |

- **Winners:** drivers who release anyway (Release, and mostly Reciprocal). They wait less and never pay.
- **Losers:** fixed-Hold drivers keep holding and simply pay. Fee-aware drivers switch to releasing (with h = 2 = F, Flexible fee-aware drivers are exactly indifferent and release by the tie rule), so they give up their idle benefit h.
- **Flexible drivers** value idling more (h = 2), so they gain least and lose most at low demand.
- **When the fee does not help:** at **low demand, total utility after the penalty falls** in every seed. Waiting barely falls because there is little queue to clear, while the penalties and the lost idle benefit are real. Even *before* the penalty, total utility falls slightly (−146), because idle benefit is lost faster than waiting cost is saved. At medium and high demand, the time saved and the extra energy outweigh the penalty.

### 6.4 Limit check: everyone fixed to Hold

At medium demand with all 40 drivers fixed to Hold, P0 and P1 give **identical** waiting, completion, energy and idle slots in all five seeds. The only difference is the penalty (−2,093 points on average, range [−2,142, −2,054]). **A fee changes outcomes only through drivers who respond to it.** In the main runs that means the Fee-aware drivers directly (25% of the pool) and the Reciprocal drivers indirectly, through better previous visits.

## 7. Game-theory explanation (summary; full calculations in the appendix)

**Normal and extensive form.** In the teaching C/H game, H (hold) is strictly dominant (6 > 4 and 1 > 0). The unique Nash equilibrium is therefore (H, H) = (1, 1), even though (C, C) = (4, 4) is jointly best. This is a prisoner's dilemma over the plug, and it explains why holding persists without a fee. With sequential moves, backward induction gives P2 = (H after C, H after H) and P1 = H, so the path is H→H with payoffs (1, 1). Hiding P1's move puts P2's two nodes in one information set. The result is imperfect information with perfect recall, and the same equilibrium.

**Information and recall.** In the memory tree, full information gives the path L-L-R with payoffs (8, 4). Forgetting one's own first action, or forgetting the stage, merges P1's nodes into shared information sets, so P1 must use one action per set. Under the forgotten stage, a 50-50 mixed lottery over "always L" and "always R" earns **1.5**, while fresh 50-50 behavioral draws earn **4.25**. With perfect recall, a behavioral strategy (randomise first, then repeat the remembered action) reproduces the mixed lottery exactly. Without recall it cannot. The simulator's Reciprocal rule depends on this kind of memory.

**Repetition.** With three known rounds, (H, H) is played in every round by backward induction. With an infinite horizon and a grim trigger, cooperation holds when 4/(1−δ) ≥ 6 + δ/(1−δ), i.e. **δ ≥ 0.4**. At δ = 0.2 the values are 5.00 vs 6.25, so deviating pays. At δ = 0.5 they are 8.00 vs 7.00, so cooperation holds. The 60-day queue is finite and its rules are programmed, so it does not test this result.

**Private needs.** With π = 0.30 Urgent, F = 1.5 and a +1 bonus for a Flexible player's own H, the plan "Urgent → C, Flexible → H" is a **Bayesian Nash equilibrium**. Urgent: E[C] = 1.20 > E[H] = 1.00. Flexible: E[H] = 2.00 > E[C] = 1.20. This matches the simulator: Flexible drivers value idling more, so a moderate fee changes their behaviour less and costs them more.

**Evolution.** With fC = 4x and fH = (6−F)x + (1−F)(1−x), the release share falls from 0.5 to **0.124** after 30 updates when F = 0 (fC − fH = −(1+x) < 0). It rises to **0.653** when F = 2 (fC − fH = 1 − x > 0). The first step reproduces x₁ = 0.48125. This agrees in direction with the simulator, but it is not a forecast.

## 8. Limits and what remains uncertain

- **Synthetic data.** Arrivals, energy needs, types and utility weights are modelling assumptions and are not fitted to real sessions. Five seeds are five samples, not proof of behaviour at a real campus.
- **Programmed rules.** These are fixed rules, not equilibrium strategies. Only the Fee-aware rule responds to F directly, so the size of the effect depends on how many such drivers exist (25% here). Real drivers might adapt differently.
- **Knife-edge tie.** With h = F = 2, Flexible fee-aware drivers are exactly indifferent. A slightly different fee could change their response.
- **Separate models.** The queue utility and the C/H teaching table are different models. The game-theory results explain the direction of the incentives, not the exact simulator numbers.
- **What the study supports:** in this model, an idle penalty of 2 points reduces waiting and raises completion for both Urgent and Flexible drivers at every demand level. It transfers utility from holders to releasers, and it lowers total welfare when demand is low. It does **not** support the claim that the fee is always best or that it predicts a specific real-world improvement.

## References

[1] Electrify America, *Charging FAQ* (idle fees). Context only; the project's points are not real fees.
[2] Y. Shoham and K. Leyton-Brown, *Multiagent Systems: Algorithmic, Game-Theoretic, and Logical Foundations*, Cambridge University Press, 2009. Ch. 3, Ch. 5, §6.1, §6.3, §7.7.
[3] Z. J. Lee, T. Li and S. H. Low, "ACN-Data: Analysis and Applications of an Open EV Charging Dataset," *Proc. ACM e-Energy*, 2019.
[4] "Evolutionary Game Analysis of Electric Vehicle Distribution Entities with Shared Charging Facilities," *Mathematics*, 12(21), 3413, 2024.

Software: Python standard library, pandas, matplotlib, Plotly and Streamlit. The supplied `generate_data.py` was used unchanged. No other code was borrowed.

---

## Appendix A: Calculations

The full worked answers with tree diagrams are in `theory/written_answers.md`. They are verified by `python -m theory.calculations` and `python -m theory.evolutionary`, and shown interactively in the app's *Game theory* and *Evolution* tabs.

| Check | Result |
|---|---|
| Mini case, all release | waiting 4, energy 15, utility 25 ✓ |
| Mini case, A holds 1 | waiting 6, energy 15, utility 23 ✓ |
| Normal-form NE | (H, H) = (1, 1) |
| Memory tree, full information | path L-L-R, payoffs (8, 4) |
| Probability totals (3 strategies) | each sums to 1 |
| Mixed vs fresh behavioral | 1.5 vs 4.25 |
| Grim-trigger threshold | δ ≥ 0.4 (δ = 0.2: 5 < 6.25; δ = 0.5: 8 > 7) |
| Bayesian expected payoffs | Urgent C 1.20 / H 1.00; Flexible C 1.20 / H 2.00 → BNE |
| First evolutionary update | fC = 2, fH = 3.5, x₁ = 0.48125 ✓ |

## Appendix B: Reproducing the results

```
pip install -r requirements.txt
python run_experiments.py
python -m theory.evolutionary
python run_all_checks.py
streamlit run app/results_app.py
```
