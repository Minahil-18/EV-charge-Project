# Fair Access to Shared EV Chargers

Charging-queue simulator (P0 vs P1 idle penalty), game-theory calculations, an evolutionary graph and a results screen.
Python 3.10+. The simulator itself uses only the standard library. The graphs and screen need `pandas`, `matplotlib`, `plotly` and `streamlit`.

```
pip install -r requirements.txt
```

## Run everything (no screen needed)
```
python check_mini_case.py          # mini case: must print PASS twice
python run_experiments.py          # generates seeds 0-4, 30 main runs + 10 all-Hold runs
python -m theory.evolutionary      # evolutionary graph -> results/evolutionary.png
python -m theory.calculations      # Section 3/4 arithmetic checks
python run_all_checks.py           # every check in the brief
```
Results screen (reads saved files only):
```
streamlit run app/results_app.py
```

## Layout
| Path | What | 
|---|---|
| `starter_data/` | Supplied archive (unchanged) |
| `data/seed_0..4/` | Inputs generated with `generate_data.py --seed k --urgent-prior 0.30` |
| `sim/rules.py` | Driver agents + 4 rules (each sees only its own private row) |
| `sim/engine.py` | One-day queue with the brief's event order |
| `sim/data.py` | Loading, 60-day run, summary metrics |
| `sim/checks.py` | Safety checks (no double charging, no energy while idle, etc.) |
| `run_experiments.py` | Repeats all 40 comparisons |
| `results/runs/<run_id>/` | `visits.csv`, `settings.json`, `summary.json` per run |
| `results/summary_all.csv`, `results/paired_comparison.csv` | All summaries; P1−P0 by matching seed |
| `theory/` | Evolutionary script, arithmetic checks, written answers |
| `app/results_app.py`, `app/style.py` | Results screen: run explorer, P0 vs P1, game theory, evolution, live mini case, findings |
| `FINDINGS.md` | Main results and interpretation |
| `report/PROPOSAL.md`, `report/REPORT.md` | One-page proposal and the report draft |

## Modelling decisions (record of assumptions)
- Queue order: arrival slot, then driver ID. Free chargers are filled in charger-ID order.
- Energy for slot [t, t+1) is credited at boundary t+1, at most 3 kWh, and never more than what is still requested.
- Missing values are written as `NA` (e.g. `start_slot` for unserved drivers).
- `action` values: `release`, `hold_1`, `hold_2`, `forced_release` (finished exactly at departure), `incomplete` (left before the request was met), `unserved` (never started).
- Unserved waiting = departure − arrival. Incomplete charges have idle = 0.
- Reciprocal memory persists across days within a run and resets between runs. A "fully served" previous visit means delivered = requested.
- Only P0 and P1, and only seeds 0–4. History scores and P2/P3 are not used.
