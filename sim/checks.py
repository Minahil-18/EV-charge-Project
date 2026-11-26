"""Safety checks required before the final presentation (brief, page 6)."""
from collections import defaultdict


def check_run(records, log):
    """Raise AssertionError if any rule is broken. Returns number of checks run."""
    n = 0
    # no charger serves two drivers at once
    seen = defaultdict(set)
    for day, slot, charger, driver, mode, kwh in log.occupancy:
        key = (day, slot, charger)
        assert not seen[key], f"charger {charger} used twice day {day} slot {slot}"
        seen[key].add(driver)
        n += 1
    by_req = {(r["day"], r["driver_id"]): r for r in records}
    energy = defaultdict(float)
    for day, slot, charger, driver, mode, kwh in log.occupancy:
        r = by_req[(day, driver)]
        if mode == "charge":
            # energy only between arrival and departure
            assert r["arrival_slot"] <= slot < r["departure_slot"], "energy outside visit window"
            energy[(day, driver)] += kwh
        else:
            assert kwh == 0, "energy during idle hold"
        n += 1
    for r in records:
        key = (r["day"], r["driver_id"])
        assert abs(energy[key] - r["delivered_kwh"]) < 1e-9, "energy log mismatch"
        assert r["delivered_kwh"] <= r["requested_kwh"] + 1e-9, "delivered > requested"
        if r["start_slot"] is None:   # unserved drivers still pay a waiting cost
            assert r["waiting_slots"] == r["departure_slot"] - r["arrival_slot"]
            assert r["delivered_kwh"] == 0
        else:
            assert r["waiting_slots"] == r["start_slot"] - r["arrival_slot"]
        if r["release_slot"] is not None:
            assert r["release_slot"] <= r["departure_slot"], "stayed past departure"
        assert r["idle_slots"] in (0, 1, 2)
        if r["idle_slots"]:
            assert r["fully_served"] and r["release_slot"] == r["finish_slot"] + r["idle_slots"]
        n += 6
    return n
