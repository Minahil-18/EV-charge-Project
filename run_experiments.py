"""Repeat every comparison in the brief.

  * generates seeds 0-4 with the supplied generator (data/seed_k/)
  * 30 main runs: 2 policies x 3 demand levels x 5 seeds
  * 10 limit-check runs: medium demand, every driver fixed to Hold, P0 and P1
  * runs the safety checks on every run
  * saves visit-level CSV, settings JSON and summary JSON per run, plus
    results/summary_all.csv and results/paired_comparison.csv

Run:  python run_experiments.py
No screen is needed; the results app only reads what this script saves.
"""
import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from sim.checks import check_run
from sim.data import load_inputs, run_scenario, summarize

ROOT = Path(__file__).resolve().parent
GENERATOR = ROOT / "starter_data" / "generate_data.py"
DATA = ROOT / "data"
RESULTS = ROOT / "results"
SEEDS = [0, 1, 2, 3, 4]
SCENARIOS = ["low", "medium", "high"]
POLICIES = ["P0", "P1"]
URGENT_PRIOR = 0.30


def ensure_seed_data(seed):
    out = DATA / f"seed_{seed}"
    if not (out / "sessions_public.csv").exists():
        subprocess.run([sys.executable, str(GENERATOR), "--output", str(out),
                        "--seed", str(seed), "--urgent-prior", str(URGENT_PRIOR)],
                       check=True, stdout=subprocess.DEVNULL)
    return out


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:16]


def write_visits(path, records):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(records[0]))
        w.writeheader()
        for r in records:
            w.writerow({k: ("NA" if v is None else v) for k, v in r.items()})


def flat(run_id, seed, scenario, policy, variant, summary):
    row = {"run_id": run_id, "seed": seed, "scenario": scenario, "policy": policy,
           "variant": variant}
    for group, vals in summary.items():
        for k, v in vals.items():
            row[f"{group}_{k}"] = v
    return row


def main():
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "runs").mkdir(exist_ok=True)
    plan = [(s, sc, p, "main", None) for s in SEEDS for sc in SCENARIOS for p in POLICIES]
    plan += [(s, "medium", p, "all_hold", "hold") for s in SEEDS for p in POLICIES]
    rows, total_checks = [], 0
    for seed, scenario, policy, variant, override in plan:
        data_dir = ensure_seed_data(seed)
        inputs = load_inputs(data_dir)
        records, log = run_scenario(inputs, scenario, policy, override, collect_log=True)
        total_checks += check_run(records, log)
        summary = summarize(records)
        run_id = f"{variant}_{scenario}_{policy}_seed{seed}"
        out = RESULTS / "runs" / run_id
        out.mkdir(exist_ok=True)
        write_visits(out / "visits.csv", records)
        settings = {
            "run_id": run_id, "seed": seed, "scenario": scenario, "policy": policy,
            "fee_per_idle_slot": float(inputs["policies"][policy]["fee_per_idle_slot"]),
            "variant": variant, "rule_override": override, "urgent_prior": URGENT_PRIOR,
            "chargers": len(inputs["chargers"]), "days": inputs["config"]["days"],
            "day_slots": inputs["config"]["day_slots"], "queue_order": "arrival_slot, driver_id",
            "input_dir": str(data_dir.relative_to(ROOT)).replace("\\", "/"),
            "input_files_sha256_16": {f: sha(data_dir / f) for f in
                                      ("sessions_public.csv", "drivers_private.csv",
                                       "chargers.csv", "policies.csv", "config.json")},
        }
        (out / "settings.json").write_text(json.dumps(settings, indent=2))
        (out / "summary.json").write_text(json.dumps(summary, indent=2))
        rows.append(flat(run_id, seed, scenario, policy, variant, summary))
        a = summary["all"]
        print(f"{run_id:32s} wait={a['avg_waiting_slots']:.3f} served={a['share_fully_served']:.3f} "
              f"energy={a['total_energy_kwh']:.0f} idle={a['total_idle_slots']}")

    with open(RESULTS / "summary_all.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    # paired comparison: P1 - P0 within the same seed, then mean and range
    metrics = [k for k in rows[0] if k not in ("run_id", "seed", "scenario", "policy", "variant")
               and not k.endswith("_requests")]
    pairs = []
    for variant in ("main", "all_hold"):
        for scenario in SCENARIOS:
            per_seed = []
            for seed in SEEDS:
                p0 = [r for r in rows if (r["variant"], r["scenario"], r["policy"], r["seed"]) == (variant, scenario, "P0", seed)]
                p1 = [r for r in rows if (r["variant"], r["scenario"], r["policy"], r["seed"]) == (variant, scenario, "P1", seed)]
                if p0 and p1:
                    per_seed.append({m: p1[0][m] - p0[0][m] for m in metrics
                                     if m in p0[0] and m in p1[0]})
            if not per_seed:
                continue
            for m in metrics:
                if m not in per_seed[0]:
                    continue
                vals = [d[m] for d in per_seed]
                pairs.append({"variant": variant, "scenario": scenario, "metric": m,
                              **{f"diff_seed{s}": v for s, v in zip(SEEDS, vals)},
                              "mean_diff_P1_minus_P0": sum(vals) / len(vals),
                              "min_diff": min(vals), "max_diff": max(vals)})
    with open(RESULTS / "paired_comparison.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(pairs[0]))
        w.writeheader()
        w.writerows(pairs)
    (RESULTS / "run_meta.json").write_text(json.dumps({
        "runs": len(plan), "main_runs": sum(p[3] == "main" for p in plan),
        "limit_check_runs": sum(p[3] == "all_hold" for p in plan),
        "safety_checks_passed": total_checks, "seeds": SEEDS, "scenarios": SCENARIOS,
        "policies": POLICIES, "urgent_prior": URGENT_PRIOR}, indent=2))
    print(f"\n{len(plan)} runs done, {total_checks} safety checks passed.")
    print("Saved results/summary_all.csv, results/paired_comparison.csv, results/runs/*")


if __name__ == "__main__":
    main()
