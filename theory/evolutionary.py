"""Section 5A: replicator-style update for the C/H game.

x = share choosing C.   fC = 4x,   fH = (6-F)x + (1-F)(1-x)
x_next = x + 0.05 * x(1-x)(fC - fH)

Run:  python -m theory.evolutionary   (saves results/evolutionary.csv and .png)
"""
import csv
from pathlib import Path

STEP = 0.05
ROOT = Path(__file__).resolve().parent.parent


def payoffs(x, fee):
    f_c = 4 * x
    f_h = (6 - fee) * x + (1 - fee) * (1 - x)
    return f_c, f_h


def update(x, fee, step=STEP):
    f_c, f_h = payoffs(x, fee)
    return x + step * x * (1 - x) * (f_c - f_h)


def path(fee, x0=0.5, updates=30):
    xs = [x0]
    for _ in range(updates):
        xs.append(update(xs[-1], fee))
    return xs


def save(out_dir=ROOT / "results"):
    out_dir.mkdir(exist_ok=True)
    p0, p2 = path(0), path(2)
    with open(out_dir / "evolutionary.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["update", "x_share_C_F0", "x_share_C_F2"])
        for i, (a, b) in enumerate(zip(p0, p2)):
            w.writerow([i, f"{a:.6f}", f"{b:.6f}"])
    fig = make_figure(p0, p2)
    fig.savefig(out_dir / "evolutionary.png", dpi=150, bbox_inches="tight")
    return p0, p2


def make_figure(p0=None, p2=None):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    p0 = p0 or path(0)
    p2 = p2 or path(2)
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(range(len(p0)), p0, marker="o", ms=3, label="F = 0 (no fee)", color="#c0392b")
    ax.plot(range(len(p2)), p2, marker="s", ms=3, label="F = 2 (idle fee)", color="#2471a3")
    ax.set_xlabel("Update")
    ax.set_ylabel("Share choosing C (release), x")
    ax.set_ylim(0, 1)
    ax.set_title("Share of release (C) behaviour over 30 updates, start x = 0.5")
    ax.grid(alpha=0.3)
    ax.legend()
    return fig


if __name__ == "__main__":
    f_c, f_h = payoffs(0.5, 0)
    x1 = update(0.5, 0)
    print(f"first no-fee step: fC={f_c}, fH={f_h}, x_next={x1}")
    assert (f_c, f_h) == (2, 3.5) and abs(x1 - 0.48125) < 1e-12
    p0, p2 = save()
    assert all(0 <= x <= 1 for x in p0 + p2)
    print(f"F=0: x30 = {p0[-1]:.4f}   F=2: x30 = {p2[-1]:.4f}   (all shares in [0,1])")
