# Findings: does the idle penalty (P1) help? (seeds 0–4)

Source: `results/paired_comparison.csv` (P1 − P0 within the same seed; mean and [min, max] over 5 seeds).
These are synthetic teaching runs, not evidence about a real campus.

## Headline: P1 reduces waiting at every demand level, for both types

| Demand | Avg waiting P0 → P1 (slots) | Change [range] | Fully served P0 → P1 | Idle slots change |
|---|---|---|---|---|
| Low    | 0.52 → 0.38 | −0.14 [−0.16, −0.12] | 93.2% → 95.0% | −276 |
| Medium | 2.88 → 2.64 | −0.24 [−0.25, −0.22] | 59.8% → 63.3% | −264 |
| High   | 4.26 → 4.10 | −0.16 [−0.17, −0.13] | 38.2% → 40.7% | −222 |

Waiting falls for both **Urgent** and **Flexible** drivers by about the same amount, and completion rises for both. All 5 seeds agree in sign.

## Who gains and who loses (avg utility after penalty per visit, P1 − P0)

| Rule | Low | Medium | High |
|---|---|---|---|
| Release    | +0.49 | +1.38 | +0.86 |
| Reciprocal | +0.26 | +0.45 | +0.51 |
| Hold       | **−2.54** | −0.52 | −0.02 |
| Fee aware  | **−2.05** | −0.13 | +0.00 |

- **Winners:** drivers who release anyway. They wait less and pay nothing.
- **Losers:** fixed-Hold drivers pay the fee without changing behaviour. Fee-aware drivers lose their idle benefit h. Flexible drivers value idling more (h = 2), so they lose more.
- **When the fee does not help:** at **low demand**, total utility after penalty *falls* (−712 points, range [−858, −590]). There is little queue to clear, so the time saved is small and the penalties and lost idle benefit outweigh it. At medium and high demand, total utility after penalty rises (+428 and +728).

## Limit check: everyone fixed to Hold (medium demand)

Waiting, completion, energy and idle slots are **identical** under P0 and P1 in all 5 seeds. The only change is the penalty (−2093 points on average). A fee only works through drivers who respond to it. In the main runs that is the 25% Fee-aware group, plus indirect effects through Reciprocal memory.

## Limits
- 5 synthetic seeds, programmed (not equilibrium) rules, and teaching-point utilities.
- The fee changes only the Fee-aware rule directly. With h = F = 2, Flexible fee-aware drivers are exactly indifferent and release by the tie rule.
