# Project Proposal: Fair Access to Shared EV Chargers

**Problem.** At a shared charging site, a driver who has finished charging may keep the charger occupied (idle) while others wait. Public networks use idle fees to discourage this [1]. Drivers differ, though: urgent drivers lose a lot from waiting, while flexible drivers gain more from leaving the car connected. A rule that helps the average driver may therefore harm some drivers.

**Research question.** Does an idle penalty reduce waiting, and how does it affect drivers with different needs?

**Game.**
- *Players:* 40 drivers (one site, six 6 kW chargers, 16 half-hour slots per day).
- *Private types:* Urgent (v=3, w=3, h=1) or Flexible (v=2, w=1, h=2).
- *Actions after a full charge:* Release, Hold 1 or Hold 2 (legal only if the hold fits before departure).
- *Payoff:* U = v·kWh − w·wait + h·idle − F·idle.
- *Information:* each driver sees its own type, request and history, plus the public queue and fee. It sees no other driver's private data or future arrivals.
- *Behaviour:* four supplied rules (Release, Hold, Reciprocal, Fee aware).

**Policies.** P0 = first come, first served, F = 0. P1 = same order, F = 2 per idle slot.

**Method.**
1. Build a discrete-slot queue simulator that follows the brief's event order, and verify it on the supplied mini case (waiting 4 / energy 15 / utility 25, and 6 / 15 / 23 when A holds).
2. Generate seeds 0–4. Run 2 policies × 3 demand levels × 5 seeds = 30 runs of 60 days, plus 10 "everyone Hold" limit-check runs at medium demand.
3. Compare matched seeds (P1 − P0), then report the mean and range for: waiting (including unserved drivers), share fully served, energy, idle slots, and utility before and after the penalty, split by type and by rule.
4. Explain the incentives with small written games: the C/H normal and extensive forms, imperfect information and recall on the memory tree, mixed vs behavioral strategies, finite and infinite repetition (grim trigger), a Bayesian game (π = 0.30) and a replicator-style evolutionary graph for F = 0 and F = 2.
5. Build a local results screen that reads only the saved results.

**Input checks.** All five generated seeds have 4,320 requests (720 / 1,440 / 2,160), 40 drivers (10 per rule), 6 chargers, 0 ≤ arrival < departure ≤ 16, and requested kWh a positive multiple of 3 that fits before departure. The number of Urgent drivers per seed is 12, 11, 15, 10 and 6 (prior 0.30).

**Deliverables.** Simulator and results screen, saved settings and results, a script that repeats every comparison, a 6–8 page report with a calculation appendix, and an 8–10 minute demonstration.

**Reading.** Shoham and Leyton-Brown [2], Chapters 3 and 5 and Sections 6.1, 6.3 and 7.7; Lee, Li and Low (2019) on ACN-Data [3].

**Plan.**
- Week 1: proposal and data checks.
- Week 2: simulator passes the mini case.
- Week 3: experiments, Bayesian, repeated and evolutionary work.
- Week 4: results screen, report and demonstration.
