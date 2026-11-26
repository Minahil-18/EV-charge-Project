"""Driver agents and the four supplied decision rules.

Each Driver object is built from ONE private row only (its own). When it must
decide after a full charge it receives a public Observation (time, own
departure, current fee, queue length). It never sees another driver's private
row, strategy label or future arrivals.
"""
from dataclasses import dataclass, field

RULES = ("release", "hold", "reciprocal", "fee_aware")
MAX_IDLE = 2


@dataclass(frozen=True)
class Observation:
    """Everything a driver is allowed to see when it decides."""
    t: int                # current boundary
    departure_slot: int   # own departure
    fee: float            # public idle fee F
    queue_length: int     # public: cars currently waiting


@dataclass
class VisitMemory:
    fully_served: bool
    waiting_slots: int


@dataclass
class Driver:
    driver_id: str
    private_type: str
    v: float   # value per kWh
    w: float   # wait cost per slot
    h: float   # idle benefit per slot
    rule: str
    last_visit: VisitMemory | None = field(default=None)

    @classmethod
    def from_private_row(cls, row, rule_override=None):
        rule = rule_override or row.get("private_strategy", "release")
        if rule not in RULES:
            raise ValueError(f"unknown rule {rule!r}")
        return cls(driver_id=row["driver_id"], private_type=row["private_type"],
                   v=float(row["value_per_kwh"]), w=float(row["wait_cost_per_slot"]),
                   h=float(row["idle_benefit_per_slot"]), rule=rule)

    # ------------------------------------------------------------------
    @staticmethod
    def legal_holds(obs: Observation):
        """Idle slots O that fit before departure (0 = release)."""
        return [o for o in range(0, MAX_IDLE + 1) if obs.t + o <= obs.departure_slot]

    def decide(self, obs: Observation) -> int:
        """Return number of idle slots to hold (0 = Release)."""
        legal = self.legal_holds(obs)
        if self.rule == "release":
            return 0
        if self.rule == "hold":
            return max(legal)
        if self.rule == "reciprocal":
            if self.last_visit is None:
                return 0
            if self.last_visit.fully_served and self.last_visit.waiting_slots <= 2:
                return 0
            return 1 if 1 in legal else 0
        if self.rule == "fee_aware":
            best, best_val = 0, 0.0          # Release first so ties go to Release
            for o in legal:
                val = (self.h - obs.fee) * o
                if val > best_val:
                    best, best_val = o, val
            return best
        raise ValueError(self.rule)

    def remember(self, fully_served: bool, waiting_slots: int):
        """Store the outcome of the visit that just ended (Reciprocal memory)."""
        self.last_visit = VisitMemory(fully_served, waiting_slots)
