"""Every check listed in the brief before the final presentation.

Run:  python run_all_checks.py
"""
import subprocess
import sys

from sim.checks import check_run
from sim.data import load_inputs, run_scenario, summarize
from sim.rules import Driver, Observation

OK = True


def report(name, passed):
    global OK
    OK &= bool(passed)
    print(f"[{'PASS' if passed else 'FAIL'}] {name}")


def step(cmd):
    return subprocess.run([sys.executable, *cmd], capture_output=True, text=True).returncode == 0


report("mini case (all_release and A_holds_one_slot)", step(["check_mini_case.py"]))
report("memory tree, probability totals, repeated game, Bayesian payoffs", step(["-m", "theory.calculations"]))
report("first evolutionary update = 0.48125 and shares stay in [0,1]", step(["-m", "theory.evolutionary"]))

inputs = load_inputs("data/seed_0")
for scenario in ("low", "medium", "high"):
    for policy in ("P0", "P1"):
        recs, log = run_scenario(inputs, scenario, policy, collect_log=True)
        try:
            check_run(recs, log)
            report(f"no double charging / no energy outside visit or during hold / "
                   f"energy <= request / unserved wait cost: {scenario} {policy}", True)
        except AssertionError as e:
            report(f"safety checks {scenario} {policy}: {e}", False)

a, _ = run_scenario(inputs, "medium", "P1")
b, _ = run_scenario(inputs, "medium", "P1")
report("identical inputs and settings give identical results", a == b and summarize(a) == summarize(b))

# privacy: a driver is built from its own row only and decides from a public observation
import inspect
src = inspect.signature(Driver.decide)
report("driver decision sees only its own row and a public Observation",
       list(src.parameters) == ["self", "obs"] and
       set(Observation.__dataclass_fields__) == {"t", "departure_slot", "fee", "queue_length"})

# rules sanity
d = Driver("X", "flexible", 2, 1, 2, "fee_aware")
report("fee_aware: holds 2 under P0, releases on tie under P1 (h=F=2)",
       d.decide(Observation(5, 10, 0, 0)) == 2 and d.decide(Observation(5, 10, 2, 0)) == 0)
h = Driver("Y", "urgent", 3, 3, 1, "hold")
report("hold: largest legal hold (only 1 slot fits before departure)", h.decide(Observation(5, 6, 0, 0)) == 1)

print("\nALL CHECKS PASSED" if OK else "\nSOME CHECKS FAILED")
sys.exit(0 if OK else 1)
