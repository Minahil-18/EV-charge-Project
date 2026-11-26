"""Discrete-slot charging queue (one site, identical chargers, FCFS).

Event order at every boundary t (brief section 1, starter README):
  1. finish energy delivered during slot [t-1, t)
  2. remove drivers whose departure time is t (incl. incomplete / unserved)
  3. newly completed drivers who can stay choose Release / Hold 1 / Hold 2;
     earlier holds that expire at t end
  4. add arrivals, allocate free chargers by (arrival_slot, driver_id),
     charge during [t, t+1)   -- skipped at the final boundary
"""
from dataclasses import dataclass, field

from .rules import Driver, Observation

NA = None  # missing value marker; written as "NA" in files


@dataclass
class Visit:
    request_id: str
    day: int
    driver_id: str
    arrival_slot: int
    departure_slot: int
    requested_kwh: float
    charger_id: str | None = NA
    start_slot: int | None = NA
    finish_slot: int | None = NA
    release_slot: int | None = NA
    delivered_kwh: float = 0.0
    waiting_slots: int = 0
    action: str = NA
    idle_slots: int = 0
    hold_end: int | None = NA
    status: str = "pending"   # pending, waiting, charging, holding, done

    @property
    def fully_served(self):
        return self.delivered_kwh >= self.requested_kwh


@dataclass
class DayLog:
    """What every charger did in every slot -- used by the safety checks."""
    occupancy: list = field(default_factory=list)  # (day, slot, charger, driver, mode, kwh)


def simulate_day(requests, drivers, chargers, fee, end_boundary=16,
                 kwh_per_slot=3.0, action_override=None, log=None):
    """Simulate one day.

    requests: list of dicts with request_id, day, driver_id, arrival_slot,
              departure_slot, requested_kwh
    drivers:  {driver_id: Driver}; state (Reciprocal memory) persists across days
    chargers: list of charger IDs
    action_override: optional {driver_id: idle_slots} fixing a choice (mini case)
    Returns list of finished Visit objects.
    """
    visits = [Visit(r["request_id"], int(r["day"]), r["driver_id"], int(r["arrival_slot"]),
                    int(r["departure_slot"]), float(r["requested_kwh"])) for r in requests]
    occupant = {c: None for c in chargers}   # charger -> Visit
    waiting: list[Visit] = []

    def finalize(v: Visit, t: int):
        if v.status == "waiting":                         # never started
            v.waiting_slots = v.departure_slot - v.arrival_slot
            v.action = "unserved"
        else:
            v.release_slot = t
            if v.charger_id is not None and occupant.get(v.charger_id) is v:
                occupant[v.charger_id] = None
        v.status = "done"
        drivers[v.driver_id].remember(v.fully_served, v.waiting_slots)

    for t in range(0, end_boundary + 1):
        # 1. finish energy from the previous slot ------------------------------
        newly_completed = []
        if t > 0:
            for c in chargers:
                v = occupant[c]
                if v is None:
                    continue
                if v.status == "charging":
                    kwh = min(kwh_per_slot, v.requested_kwh - v.delivered_kwh)
                    v.delivered_kwh += kwh
                    if log is not None:
                        log.occupancy.append((v.day, t - 1, c, v.driver_id, "charge", kwh))
                    if v.fully_served:
                        v.finish_slot = t
                        newly_completed.append(v)
                elif v.status == "holding" and log is not None:
                    log.occupancy.append((v.day, t - 1, c, v.driver_id, "idle", 0.0))

        # 2. departures --------------------------------------------------------
        for v in list(waiting):
            if v.departure_slot == t:
                waiting.remove(v)
                finalize(v, t)
        for c in chargers:
            v = occupant[c]
            if v is not None and v.departure_slot == t:
                if v in newly_completed:
                    v.action = "forced_release"   # completed exactly at departure
                    newly_completed.remove(v)
                elif v.status == "charging":
                    v.action = "incomplete"       # left before request was met
                finalize(v, t)

        # 3. hold / release decisions, then expiring holds ---------------------
        for v in newly_completed:
            obs = Observation(t=t, departure_slot=v.departure_slot, fee=fee,
                              queue_length=len(waiting))
            if action_override and v.driver_id in action_override:
                o = action_override[v.driver_id]
                if o not in Driver.legal_holds(obs):
                    raise ValueError(f"illegal override {o} for {v.driver_id} at {t}")
            else:
                o = drivers[v.driver_id].decide(obs)
            if o == 0:
                v.action = "release"
                finalize(v, t)
            else:
                v.action = f"hold_{o}"
                v.idle_slots = o
                v.hold_end = t + o
                v.status = "holding"
        for c in chargers:
            v = occupant[c]
            if v is not None and v.status == "holding" and v.hold_end == t:
                finalize(v, t)

        if t == end_boundary:          # no interval after the last boundary
            break

        # 4. arrivals and allocation -------------------------------------------
        for v in visits:
            if v.arrival_slot == t and v.status == "pending":
                v.status = "waiting"
                waiting.append(v)
        waiting.sort(key=lambda x: (x.arrival_slot, x.driver_id))
        for c in chargers:
            if occupant[c] is None and waiting:
                v = waiting.pop(0)
                occupant[c] = v
                v.charger_id = c
                v.start_slot = t
                v.waiting_slots = t - v.arrival_slot
                v.status = "charging"

    # anything still open at the final boundary leaves now (defensive)
    for v in visits:
        if v.status != "done":
            if v.status == "charging" and not v.action:
                v.action = "incomplete"
            finalize(v, end_boundary)
    return visits


def utility(visit: Visit, driver: Driver, fee: float):
    """Return (utility before penalty, penalty, utility after penalty)."""
    before = driver.v * visit.delivered_kwh - driver.w * visit.waiting_slots + driver.h * visit.idle_slots
    penalty = fee * visit.idle_slots
    return before, penalty, before - penalty
