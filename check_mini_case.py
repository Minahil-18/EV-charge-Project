"""Check the simulator against the supplied one-charger, three-driver mini case (P0).

Run:  python check_mini_case.py
"""
import json
import sys
from pathlib import Path

from sim.data import read_csv
from sim.engine import simulate_day, utility
from sim.rules import Driver

DATA = Path(__file__).resolve().parent / "starter_data"


def run_case(override):
    public = read_csv(DATA / "mini_case_public.csv")
    for r in public:
        r["day"] = 1
    drivers = {row["driver_id"]: Driver.from_private_row(row, "release")
               for row in read_csv(DATA / "mini_case_private.csv")}
    visits = simulate_day(public, drivers, ["C01"], fee=0, end_boundary=6,
                          kwh_per_slot=3, action_override=override)
    out, tot_u, tot_w, tot_e = {}, 0, 0, 0
    for v in visits:
        _, _, u = utility(v, drivers[v.driver_id], 0)
        out[v.driver_id] = {"start": v.start_slot, "finish": v.finish_slot,
                            "release": v.release_slot, "wait_slots": v.waiting_slots,
                            "utility": u}
        tot_u, tot_w, tot_e = tot_u + u, tot_w + v.waiting_slots, tot_e + v.delivered_kwh
    out.update(total_utility=tot_u, total_wait_slots=tot_w, delivered_kwh=tot_e)
    return out


def main():
    expected = json.loads((DATA / "mini_case_expected.json").read_text())
    ok = True
    for name, override in [("all_release", {}), ("A_holds_one_slot", {"A": 1})]:
        got = run_case(override)
        exp = expected[name]
        match = all(got[k] == exp[k] for k in exp)
        ok &= match
        print(f"{name:18s} {'PASS' if match else 'FAIL'}")
        for k in ("A", "B", "C"):
            print(f"   {k}: {got[k]}")
        print(f"   totals: wait={got['total_wait_slots']} energy={got['delivered_kwh']} "
              f"utility={got['total_utility']}")
        if not match:
            print("   expected:", exp)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
