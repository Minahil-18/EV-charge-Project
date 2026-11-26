"""Loading inputs and running a full 60-day scenario."""
import csv
import json
from pathlib import Path

from .engine import DayLog, simulate_day, utility
from .rules import Driver

ROOT = Path(__file__).resolve().parent.parent
POLICIES_USED = ("P0", "P1")


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_inputs(data_dir):
    data_dir = Path(data_dir)
    return {
        "sessions": read_csv(data_dir / "sessions_public.csv"),
        "drivers_private": read_csv(data_dir / "drivers_private.csv"),
        "chargers": read_csv(data_dir / "chargers.csv"),
        "policies": {p["policy_id"]: p for p in read_csv(data_dir / "policies.csv")},
        "config": json.loads((data_dir / "config.json").read_text()),
    }


def run_scenario(inputs, scenario, policy_id, rule_override=None, collect_log=False):
    """One run = one demand level x one policy x 60 days. All state is fresh."""
    if policy_id not in POLICIES_USED:
        raise ValueError("this project uses only P0 and P1")
    fee = float(inputs["policies"][policy_id]["fee_per_idle_slot"])
    cfg = inputs["config"]
    kwh_per_slot = float(inputs["chargers"][0]["power_kw"]) * cfg["slot_minutes"] / 60
    chargers = [c["charger_id"] for c in inputs["chargers"]]
    # each Driver object receives only its own private row
    drivers = {row["driver_id"]: Driver.from_private_row(row, rule_override)
               for row in inputs["drivers_private"]}
    rows = [r for r in inputs["sessions"] if r["scenario"] == scenario]
    log = DayLog() if collect_log else None
    records = []
    for day in sorted({int(r["day"]) for r in rows}):
        day_rows = [r for r in rows if int(r["day"]) == day]   # queue reset daily
        visits = simulate_day(day_rows, drivers, chargers, fee, cfg["day_slots"],
                              kwh_per_slot, log=log)
        for v in sorted(visits, key=lambda x: (x.arrival_slot, x.driver_id)):
            d = drivers[v.driver_id]          # evaluator reads private row after play
            before, pen, after = utility(v, d, fee)
            records.append({
                "scenario": scenario, "policy": policy_id, "day": v.day,
                "request_id": v.request_id, "driver_id": v.driver_id,
                "private_type": d.private_type, "rule": d.rule,
                "arrival_slot": v.arrival_slot, "departure_slot": v.departure_slot,
                "requested_kwh": v.requested_kwh, "charger_id": v.charger_id,
                "start_slot": v.start_slot, "finish_slot": v.finish_slot,
                "release_slot": v.release_slot, "delivered_kwh": v.delivered_kwh,
                "waiting_slots": v.waiting_slots, "action": v.action,
                "idle_slots": v.idle_slots, "fully_served": int(v.fully_served),
                "utility_before_penalty": before, "penalty": pen,
                "utility_after_penalty": after,
            })
    return records, log


def summarize(records):
    """Summary metrics for one run. Unserved drivers are included in waiting."""
    def block(rs):
        n = len(rs)
        if n == 0:
            return {"requests": 0}
        return {
            "requests": n,
            "avg_waiting_slots": sum(r["waiting_slots"] for r in rs) / n,
            "share_fully_served": sum(r["fully_served"] for r in rs) / n,
            "share_never_started": sum(r["start_slot"] is None for r in rs) / n,
            "total_energy_kwh": sum(r["delivered_kwh"] for r in rs),
            "total_idle_slots": sum(r["idle_slots"] for r in rs),
            "hold_decisions": sum(str(r["action"]).startswith("hold") for r in rs),
            "total_utility_before_penalty": sum(r["utility_before_penalty"] for r in rs),
            "total_penalty": sum(r["penalty"] for r in rs),
            "total_utility_after_penalty": sum(r["utility_after_penalty"] for r in rs),
            "avg_utility_before_penalty": sum(r["utility_before_penalty"] for r in rs) / n,
            "avg_utility_after_penalty": sum(r["utility_after_penalty"] for r in rs) / n,
        }
    out = {"all": block(records)}
    for t in ("urgent", "flexible"):
        out[t] = block([r for r in records if r["private_type"] == t])
    for rule in ("release", "hold", "reciprocal", "fee_aware"):
        out[f"rule_{rule}"] = block([r for r in records if r["rule"] == rule])
    return out
