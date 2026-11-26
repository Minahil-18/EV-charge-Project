"""Results screen: Fair Access to Shared EV Chargers.

Run:  streamlit run app/results_app.py

Every simulation number on this screen is READ from the files saved by
run_experiments.py (results/summary_all.csv, results/paired_comparison.csv,
results/runs/<run>/...). The mini case is re-run live with the real engine and
the game-theory numbers are computed live from the starter tables.
"""
import csv
import json
import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "app"))

from check_mini_case import run_case                      # noqa: E402
from theory.calculations import G                         # noqa: E402
from theory.evolutionary import path as evo_path, payoffs, update  # noqa: E402
from style import (AMBER, BORDER, CHARGER_SVG, CSS, CYAN, LIME, MUTED, P0_COLOR,  # noqa: E402
                   P1_COLOR, RED, TEXT, TYPE_COLOR, kpi, section, style_fig, tree_svg)

RESULTS, RUNS, STARTER = ROOT / "results", ROOT / "results" / "runs", ROOT / "starter_data"
CFG = {"displayModeBar": False}

st.set_page_config(page_title="Fair Access · EV Charger Game", page_icon="⚡", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)

if not (RESULTS / "summary_all.csv").exists():
    st.error("No saved results yet. Run `python run_experiments.py` first.")
    st.stop()


# ------------------------------------------------------------------ data
@st.cache_data
def load_all():
    summary = pd.read_csv(RESULTS / "summary_all.csv")
    paired = pd.read_csv(RESULTS / "paired_comparison.csv")
    meta = json.loads((RESULTS / "run_meta.json").read_text())
    seed0 = ROOT / "data" / "seed_0"
    inputs = {
        "chargers": len(pd.read_csv(seed0 / "chargers.csv")),
        "drivers": len(pd.read_csv(seed0 / "drivers_private.csv")),
        "requests": len(pd.read_csv(seed0 / "sessions_public.csv")),
    }
    return summary, paired, meta, inputs


@st.cache_data
def load_run(run_id):
    d = RUNS / run_id
    return (pd.read_csv(d / "visits.csv", na_values=["NA"]),
            json.loads((d / "settings.json").read_text()))


summary, paired, meta, inputs = load_all()
main = summary[summary.variant == "main"]
DEMANDS, SEEDS = ["low", "medium", "high"], meta["seeds"]
POLICY_NAME = {"P0": "P0 · First come, first served", "P1": "P1 · Idle fee 2 pts / slot"}


def pdiff(variant, scenario, metric):
    r = paired[(paired.variant == variant) & (paired.scenario == scenario) & (paired.metric == metric)]
    return r.iloc[0] if len(r) else None


def slot_label(t):
    m = 8 * 60 + 30 * int(t)
    return f"{m // 60:02d}:{m % 60:02d}"


# ------------------------------------------------------------------ nav + hero
st.markdown(
    '<div class="navbar"><div class="brand">⚡ FAIR<span>ACCESS</span> &nbsp;·&nbsp; EV CHARGER GAME</div>'
    '<div><span class="navmeta">Multiagent systems &amp; game theory</span>'
    '<span class="pill">Synthetic data</span><span class="pill on">P0 vs P1</span></div></div>',
    unsafe_allow_html=True)

headline = [pdiff("main", d, "all_avg_waiting_slots") for d in DEMANDS]
total_mwh = main["all_total_energy_kwh"].sum() / 1000
st.markdown(f"""
<div class="hero">
  <div style="display:grid;grid-template-columns:1.35fr 1fr;gap:30px;align-items:center;position:relative;z-index:1">
    <div>
      <div class="eyebrow">Shared charging · idle penalty study</div>
      <h1>Charge. Release.<br><em>Share fairly.</em></h1>
      <p class="lead">A driver finishes charging but keeps the plug, and someone else waits.
      Does an idle fee cut that waiting, and who pays for it? We simulate {inputs['chargers']} chargers and
      {inputs['drivers']} drivers over 60 days, 3 demand levels and {len(SEEDS)} seeds, then explain the choices with game theory.</p>
      <div class="card" style="margin-top:20px;max-width:560px;background:rgba(12,17,22,.75)">
        <div class="eyebrow" style="font-size:.66rem">Headline result · P1 − P0, mean of matched seeds</div>
        <div style="display:flex;gap:28px;margin-top:10px">
          {''.join(f'<div><div class="mono" style="color:{MUTED};text-transform:uppercase;font-size:.7rem">{d}</div>'
                   f'<div style="font-family:Space Grotesk,Segoe UI,sans-serif;font-size:1.7rem;color:{LIME};font-weight:600">'
                   f'{h["mean_diff_P1_minus_P0"]:+.2f}</div><div style="color:{MUTED};font-size:.75rem">waiting slots</div></div>'
                   for d, h in zip(DEMANDS, headline))}
        </div>
      </div>
    </div>
    <div>{CHARGER_SVG}</div>
  </div>
</div>
<div class="stats">
  <div class="stat"><div class="v">{inputs['chargers']}<small>×6 kW</small></div><div class="l">Chargers</div></div>
  <div class="stat"><div class="v">{inputs['drivers']}</div><div class="l">Driver pool</div></div>
  <div class="stat"><div class="v">{inputs['requests']:,}</div><div class="l">Requests / seed</div></div>
  <div class="stat"><div class="v">{meta['runs']}</div><div class="l">Simulation runs</div></div>
  <div class="stat"><div class="v">{total_mwh:,.0f}<small>MWh</small></div><div class="l">Energy simulated</div></div>
  <div class="stat"><div class="v">{meta['safety_checks_passed'] / 1000:,.0f}<small>k</small></div><div class="l">Safety checks passed</div></div>
</div>
<div class="topics"><span>Normal form</span><span>Extensive form</span><span>Perfect recall</span>
<span>Mixed · Behavioral</span><span>Repeated games</span><span>Bayesian</span><span>Evolutionary</span></div>
""", unsafe_allow_html=True)

tab_sim, tab_cmp, tab_gt, tab_evo, tab_mini, tab_find = st.tabs(
    ["Simulator", "Policy comparison", "Game theory", "Evolution", "Mini case check", "Findings"])

# ================================================================== SIMULATOR
with tab_sim:
    st.markdown(section("01 · Run explorer", "Inside one 60-day run",
                        "Choose a demand level, a policy and a seed. Every number below is read from that run's saved files."),
                unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1.1, 1.5, 1.6])
    demand = c1.segmented_control("Demand level", DEMANDS, default="medium", key="sim_d") or "medium"
    policy = c2.segmented_control("Policy", ["P0", "P1"], default="P1", key="sim_p",
                                  format_func=lambda p: POLICY_NAME[p]) or "P1"
    seed = c3.segmented_control("Seed", SEEDS, default=0, key="sim_s", format_func=lambda s: f"Seed {s}")
    seed = 0 if seed is None else seed
    other = "P0" if policy == "P1" else "P1"

    run_id = f"main_{demand}_{policy}_seed{seed}"
    visits, settings = load_run(run_id)
    cur = main[(main.scenario == demand) & (main.seed == seed) & (main.policy == policy)].iloc[0]
    oth = main[(main.scenario == demand) & (main.seed == seed) & (main.policy == other)].iloc[0]

    def dv(col):
        return cur[col] - oth[col]

    k = st.columns(5)
    note = f"vs {other}"
    k[0].markdown(kpi("Avg waiting", f"{cur.all_avg_waiting_slots:.2f}", "slots",
                      dv("all_avg_waiting_slots"), "lower", "{:+.3f}", note), unsafe_allow_html=True)
    k[1].markdown(kpi("Fully served", f"{cur.all_share_fully_served:.1%}", "",
                      dv("all_share_fully_served") * 100, "higher", "{:+.1f} pp", note), unsafe_allow_html=True)
    k[2].markdown(kpi("Energy delivered", f"{cur.all_total_energy_kwh / 1000:.2f}", "MWh",
                      dv("all_total_energy_kwh"), "higher", "{:+,.0f} kWh", note), unsafe_allow_html=True)
    k[3].markdown(kpi("Idle slots", f"{cur.all_total_idle_slots:,.0f}", "",
                      dv("all_total_idle_slots"), "lower", "{:+,.0f}", note), unsafe_allow_html=True)
    k[4].markdown(kpi("Utility after fee", f"{cur.all_total_utility_after_penalty:,.0f}", "pts",
                      dv("all_total_utility_after_penalty"), "higher", "{:+,.0f}", note), unsafe_allow_html=True)

    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
    left, right = st.columns([1.75, 1])
    with left:
        day = st.slider("Day of the run", 1, int(visits.day.max()), 1, key="sim_day")
        d = visits[visits.day == day]
        served = d[d.start_slot.notna()].copy()
        served["charge_end"] = served.finish_slot.fillna(served.release_slot)
        fig = go.Figure()
        hover = ("<b>%{customdata[0]}</b> · %{customdata[1]} · rule %{customdata[2]}<br>"
                 "arrive %{customdata[3]:.0f} · start %{customdata[4]:.0f} · %{customdata[5]:.0f} kWh<extra></extra>")
        cd = served[["driver_id", "private_type", "rule", "arrival_slot", "start_slot", "delivered_kwh"]].values
        fig.add_bar(y=served.charger_id, x=served.charge_end - served.start_slot, base=served.start_slot,
                    orientation="h", name="Charging", customdata=cd, hovertemplate=hover,
                    marker=dict(color=[TYPE_COLOR[t] for t in served.private_type], line=dict(color="#07090c", width=2)),
                    text=served.driver_id, textposition="inside", insidetextanchor="middle",
                    textfont=dict(color="#07090c", size=11))
        idle = served[served.idle_slots > 0]
        fig.add_bar(y=idle.charger_id, x=idle.idle_slots, base=idle.finish_slot, orientation="h",
                    name="Idle hold", marker=dict(color="rgba(255,93,108,.25)", line=dict(color=RED, width=1.5),
                                                  pattern=dict(shape="/", fgcolor=RED, size=6)),
                    customdata=idle[["driver_id", "action", "penalty"]].values,
                    hovertemplate="<b>%{customdata[0]}</b> %{customdata[1]} · fee %{customdata[2]} pts<extra></extra>")
        fig.add_bar(y=[None], x=[None], name="Urgent", marker_color=AMBER, showlegend=True)
        fig.add_bar(y=[None], x=[None], name="Flexible", marker_color=CYAN, showlegend=True)
        fig.data[0].showlegend = False
        fig.update_layout(barmode="overlay",
                          title=dict(text=f"Charger timeline · day {day} · {len(d)} requests, "
                                          f"{int((d.waiting_slots > 0).sum())} waited, {int(d.start_slot.isna().sum())} never started",
                                     font=dict(size=13, color=MUTED), x=0, y=.98))
        fig.update_xaxes(range=[0, 16], tickvals=list(range(0, 17, 2)),
                         ticktext=[slot_label(t) for t in range(0, 17, 2)])
        fig.update_yaxes(categoryorder="array", categoryarray=sorted(visits.charger_id.dropna().unique(), reverse=True))
        st.plotly_chart(style_fig(fig, 370), config=CFG, width="stretch")
    with right:
        order = ["release", "hold_1", "hold_2", "forced_release", "incomplete", "unserved"]
        colors = [LIME, AMBER, RED, CYAN, "#c38bff", "#4a5663"]
        counts = visits.action.value_counts().reindex(order).fillna(0)
        fig = go.Figure(go.Pie(labels=[o.replace("_", " ") for o in order], values=counts.values, hole=.68,
                               marker=dict(colors=colors, line=dict(color="#07090c", width=3)),
                               sort=False, textinfo="none",
                               hovertemplate="%{label}: %{value} visits (%{percent})<extra></extra>"))
        fig.add_annotation(text=f"<b style='font-size:26px'>{len(visits):,}</b><br><span style='color:{MUTED}'>visits · 60 days</span>",
                           showarrow=False, font=dict(color=TEXT, family="Space Grotesk, Segoe UI, sans-serif"))
        fig.update_layout(title=dict(text="What drivers did after charging", font=dict(size=13, color=MUTED), x=0))
        style_fig(fig, 430).update_layout(legend=dict(orientation="h", x=.5, xanchor="center", y=-.08, yanchor="top"),
                                          margin=dict(t=40, b=50))
        st.plotly_chart(fig, config=CFG, width="stretch")

    a, b = st.columns(2)
    both = main[(main.scenario == demand) & (main.seed == seed)].set_index("policy")
    for col, (metric, title, fmt) in zip((a, b), [("avg_waiting_slots", "Average waiting by driver type (slots)", ".2f"),
                                                  ("share_fully_served", "Share fully served by driver type", ".1%")]):
        fig = go.Figure()
        for p, c in (("P0", P0_COLOR), ("P1", P1_COLOR)):
            vals = [both.loc[p, f"{t}_{metric}"] for t in ("urgent", "flexible")]
            fig.add_bar(x=["Urgent", "Flexible"], y=vals, name=POLICY_NAME[p], marker_color=c,
                        marker_line=dict(width=0), text=[format(v, fmt) for v in vals], textposition="outside",
                        opacity=1 if p == policy else .55)
        fig.update_layout(title=dict(text=title, font=dict(size=13, color=MUTED), x=0), barmode="group")
        if metric == "share_fully_served":
            fig.update_yaxes(tickformat=".0%")
        col.plotly_chart(style_fig(fig, 330), config=CFG, width="stretch")

    rules = ["release", "hold", "reciprocal", "fee_aware"]
    fig = go.Figure()
    fig.add_bar(x=rules, y=[both.loc["P0", f"rule_{r}_avg_utility_after_penalty"] for r in rules],
                name="P0 (no fee)", marker_color=P0_COLOR)
    fig.add_bar(x=rules, y=[both.loc["P1", f"rule_{r}_avg_utility_before_penalty"] for r in rules],
                name="P1 before fee", marker_color="rgba(200,255,61,.35)", marker_line=dict(color=LIME, width=1.5))
    fig.add_bar(x=rules, y=[both.loc["P1", f"rule_{r}_avg_utility_after_penalty"] for r in rules],
                name="P1 after fee", marker_color=LIME)
    fig.update_layout(barmode="group", title=dict(
        text="Average utility per visit by driver rule (who gains, who pays)", font=dict(size=13, color=MUTED), x=0))
    st.plotly_chart(style_fig(fig, 340), config=CFG, width="stretch")

    with st.expander("Settings and input files used for this run"):
        s1, s2 = st.columns(2)
        s1.markdown("".join(f'<div class="mono"><span style="color:{MUTED}">{k}</span> &nbsp; {v}</div>'
                            for k, v in settings.items() if k != "input_files_sha256_16"), unsafe_allow_html=True)
        s2.markdown(f'<div class="mono" style="color:{MUTED}">input folder: {settings["input_dir"]}</div>' +
                    "".join(f'<div class="mono">{f} &nbsp;<span style="color:{MUTED}">sha256 {h}…</span></div>'
                            for f, h in settings["input_files_sha256_16"].items()) +
                    f'<div class="mono" style="margin-top:10px;color:{LIME}">saved: results/runs/{run_id}/'
                    f'{{visits.csv, settings.json, summary.json}}</div>', unsafe_allow_html=True)
    with st.expander(f"Visit-level records · {len(visits):,} rows"):
        st.dataframe(visits, hide_index=True, width="stretch", height=360)
        st.download_button("Download visits.csv", (RUNS / run_id / "visits.csv").read_bytes(),
                           file_name=f"{run_id}_visits.csv")

# ================================================================== COMPARISON
with tab_cmp:
    st.markdown(section("02 · Fair experiment", "P0 vs P1 across five matched seeds",
                        "Same requests, types and starting rules in both policies; every pair is compared seed by seed, "
                        "then averaged. Error bars and dots show the full range over seeds."), unsafe_allow_html=True)
    METRICS = {"Avg waiting": ("all_avg_waiting_slots", ".2f", "lower"),
               "Fully served": ("all_share_fully_served", ".1%", "higher"),
               "Energy (kWh)": ("all_total_energy_kwh", ",.0f", "higher"),
               "Idle slots": ("all_total_idle_slots", ",.0f", "lower"),
               "Utility before fee": ("all_total_utility_before_penalty", ",.0f", "higher"),
               "Utility after fee": ("all_total_utility_after_penalty", ",.0f", "higher")}
    mname = st.segmented_control("Metric", list(METRICS), default="Avg waiting", key="cmp_m") or "Avg waiting"
    col, fmt, good = METRICS[mname]

    cards = st.columns(3)
    for c, dmd in zip(cards, DEMANDS):
        r = pdiff("main", dmd, col)
        scale = 100 if fmt.endswith("%") else 1
        unit_fmt = "{:+.1f} pp" if fmt.endswith("%") else ("{:+.3f}" if fmt == ".2f" else "{:+,.0f}")
        c.markdown(kpi(f"{dmd} demand · mean change",
                       unit_fmt.format(r.mean_diff_P1_minus_P0 * scale), "", None) +
                   f'<div style="color:{MUTED};font-size:.8rem;margin:-6px 0 0 4px">range over seeds '
                   f'[{unit_fmt.format(r.min_diff * scale)}, {unit_fmt.format(r.max_diff * scale)}]</div>',
                   unsafe_allow_html=True)

    left, right = st.columns([1.2, 1])
    with left:
        fig = go.Figure()
        ys = [f"{dmd} · seed {s}" for dmd in DEMANDS for s in SEEDS]
        v0 = [main[(main.scenario == dmd) & (main.seed == s) & (main.policy == "P0")][col].iloc[0] for dmd in DEMANDS for s in SEEDS]
        v1 = [main[(main.scenario == dmd) & (main.seed == s) & (main.policy == "P1")][col].iloc[0] for dmd in DEMANDS for s in SEEDS]
        for y, a0, a1 in zip(ys, v0, v1):
            fig.add_trace(go.Scatter(x=[a0, a1], y=[y, y], mode="lines", line=dict(color="#34404b", width=3),
                                     showlegend=False, hoverinfo="skip"))
        fig.add_trace(go.Scatter(x=v0, y=ys, mode="markers", name="P0", marker=dict(size=11, color=P0_COLOR)))
        fig.add_trace(go.Scatter(x=v1, y=ys, mode="markers", name="P1", marker=dict(size=11, color=LIME,
                                                                                    line=dict(color="#07090c", width=1))))
        fig.update_yaxes(autorange="reversed")
        if fmt.endswith("%"):
            fig.update_xaxes(tickformat=".0%")
        fig.update_layout(title=dict(text=f"{mname}: each matched seed", font=dict(size=13, color=MUTED), x=0))
        st.plotly_chart(style_fig(fig, 520), config=CFG, width="stretch")
    with right:
        rows = [("Urgent", "urgent"), ("Flexible", "flexible"), ("Release", "rule_release"),
                ("Hold", "rule_hold"), ("Reciprocal", "rule_reciprocal"), ("Fee aware", "rule_fee_aware")]
        z = [[pdiff("main", dmd, f"{g}_avg_utility_after_penalty").mean_diff_P1_minus_P0 for dmd in DEMANDS] for _, g in rows]
        lim = max(abs(v) for r in z for v in r)
        fig = go.Figure(go.Heatmap(z=z, x=[d.title() for d in DEMANDS], y=[r[0] for r in rows], zmid=0, zmin=-lim, zmax=lim,
                                   colorscale=[[0, RED], [.5, "#10161d"], [1, LIME]], xgap=4, ygap=4,
                                   text=[[f"{v:+.2f}" for v in r] for r in z], texttemplate="%{text}",
                                   textfont=dict(family="Space Grotesk, Segoe UI, sans-serif", size=14, color=TEXT),
                                   colorbar=dict(thickness=10, outlinewidth=0),
                                   hovertemplate="%{y} · %{x}: %{z:+.3f} pts per visit<extra></extra>"))
        fig.update_yaxes(autorange="reversed")
        fig.update_layout(title=dict(text="Who gains, who loses: Δ utility after fee per visit",
                                     font=dict(size=13, color=MUTED), x=0))
        st.plotly_chart(style_fig(fig, 520, legend=False), config=CFG, width="stretch")

    a, b = st.columns([1.2, 1])
    with a:
        fig = go.Figure()
        for name, m, c in [("Δ utility before fee", "all_total_utility_before_penalty", CYAN),
                           ("− penalty paid", "all_total_penalty", RED),
                           ("Δ utility after fee", "all_total_utility_after_penalty", LIME)]:
            vals, lo, hi = [], [], []
            for dmd in DEMANDS:
                r = pdiff("main", dmd, m)
                sign = -1 if m == "all_total_penalty" else 1
                vals.append(sign * r.mean_diff_P1_minus_P0)
                lo.append(sign * r.mean_diff_P1_minus_P0 - min(sign * r.min_diff, sign * r.max_diff))
                hi.append(max(sign * r.min_diff, sign * r.max_diff) - sign * r.mean_diff_P1_minus_P0)
            fig.add_bar(x=[d.title() for d in DEMANDS], y=vals, name=name, marker_color=c,
                        error_y=dict(type="data", array=hi, arrayminus=lo, color="#7d8b99", thickness=1.2, width=5))
        fig.add_hline(y=0, line_color="#46525e")
        fig.update_layout(barmode="group", title=dict(
            text="Total utility change, P1 − P0 (points, mean and seed range)", font=dict(size=13, color=MUTED), x=0))
        st.plotly_chart(style_fig(fig, 360), config=CFG, width="stretch")
    with b:
        lw = pdiff("all_hold", "medium", "all_avg_waiting_slots")
        li = pdiff("all_hold", "medium", "all_total_idle_slots")
        lu = pdiff("all_hold", "medium", "all_total_utility_after_penalty")
        st.markdown(f"""
        <div class="card" style="height:100%">
          <span class="badge info">Limit check · 10 runs</span>
          <h4 style="margin-top:12px">Everyone fixed to Hold, medium demand</h4>
          <p>The fee cannot change behaviour that is programmed not to respond.</p>
          <table class="calc">
            <tr><th>P1 − P0</th><th>mean</th><th>range</th></tr>
            <tr><td>Avg waiting</td><td class="hl">{lw.mean_diff_P1_minus_P0:+.3f}</td><td>[{lw.min_diff:+.3f}, {lw.max_diff:+.3f}]</td></tr>
            <tr><td>Idle slots</td><td class="hl">{li.mean_diff_P1_minus_P0:+.0f}</td><td>[{li.min_diff:+.0f}, {li.max_diff:+.0f}]</td></tr>
            <tr><td>Utility after fee</td><td style="color:{RED};font-weight:600">{lu.mean_diff_P1_minus_P0:+,.0f}</td><td>[{lu.min_diff:+,.0f}, {lu.max_diff:+,.0f}]</td></tr>
          </table>
          <p style="margin-top:10px">Waiting and idle use are identical; drivers only lose the penalty.</p>
        </div>""", unsafe_allow_html=True)

# ================================================================== GAME THEORY
with tab_gt:
    st.markdown(section("03 · Explaining the choices", "Game theory behind the plug",
                        "The C/H table is a teaching model (C = release, H = hold one slot), not the simulator's "
                        "energy formula. All values are computed live from the starter tables."), unsafe_allow_html=True)
    part = st.segmented_control("Topic", ["Normal & extensive form", "Forgotten information", "Mixed vs behavioral",
                                          "Repeated games", "Bayesian game"], default="Normal & extensive form",
                                key="gt_part") or "Normal & extensive form"
    A = ("C", "H")
    br1 = {b: max(A, key=lambda a: G[(a, b)][0]) for b in A}
    br2 = {a: max(A, key=lambda b: G[(a, b)][1]) for a in A}

    if part == "Normal & extensive form":
        l, r = st.columns([1, 1.25])
        with l:
            cells = ""
            for a in A:
                cells += f"<tr><th>P1 {a}</th>"
                for b in A:
                    u1, u2 = G[(a, b)]
                    s1 = f"<b>{u1}</b>" if br1[b] == a else str(u1)
                    s2 = f"<b>{u2}</b>" if br2[a] == b else str(u2)
                    ne = br1[b] == a and br2[a] == b
                    cells += f'<td class="{"ne" if ne else ""}">({s1}, {s2})</td>'
                cells += "</tr>"
            st.markdown(f"""<div class="card"><span class="badge pass">Pure Nash equilibrium (H, H)</span>
            <table class="mx" style="margin-top:12px"><tr><th></th><th>P2 C</th><th>P2 H</th></tr>{cells}</table>
            <p><b style="color:{LIME}">Lime</b> = best response. H is strictly dominant for both players
            (6 &gt; 4 and 1 &gt; 0), so the only equilibrium is (H, H) = (1, 1). The best joint outcome is (C, C) = (4, 4),
            total 8 vs 2, but each player gains 2 by switching to H alone: a prisoner's dilemma over the plug.</p></div>""",
                        unsafe_allow_html=True)
        with r:
            hidden = st.toggle("Hide P1's move from P2 (imperfect information)", key="gt_hide")
            leaves = {(a, b): f"{G[(a, b)][0]}, {G[(a, b)][1]}" for a in A for b in A}
            chosen = {("H",), ("H", "H")} | ({("C", "H")} if not hidden else set())
            st.markdown(tree_svg(2, ["P1", "P2"], leaves, chosen=chosen, actions=A, path=("H", "H"),
                                 info_sets=[[("C",), ("H",)]] if hidden else [], width=620, level_gap=110),
                        unsafe_allow_html=True)
            if hidden:
                st.markdown('<div class="card"><p>P2\'s two nodes form <b>one information set</b> (dashed). P2 cannot '
                            'condition on P1\'s move, so the game is exactly the normal form: equilibrium (H, H). '
                            'It is <b>imperfect information</b> but <b>perfect recall</b>: each player moves once, '
                            'so nobody can forget an earlier move or observation.</p></div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="card"><p><b>Backward induction.</b> After C, P2 picks H (6 &gt; 4); after H, '
                            f'P2 picks H (1 &gt; 0). P1 compares 0 vs 1 and picks H.<br>Complete strategies: '
                            f'<b>P1 = H; P2 = (H after C, H after H)</b>. Path H → H, payoffs <b style="color:{LIME}">(1, 1)</b>.</p></div>',
                            unsafe_allow_html=True)

    elif part == "Forgotten information":
        rows = list(csv.DictReader(open(STARTER / "memory_tree.csv")))
        lv = {(r["p1_first"], r["p2_action"], r["p1_second"]): (int(r["p1_payoff"]), int(r["p2_payoff"])) for r in rows}
        LR = ("L", "R")
        late = {(a, b): max(LR, key=lambda c: lv[(a, b, c)][0]) for a in LR for b in LR}
        val = {(a, b): lv[(a, b, late[(a, b)])] for a in LR for b in LR}
        p2 = {a: max(LR, key=lambda b: val[(a, b)][1]) for a in LR}
        root = max(LR, key=lambda a: val[(a, p2[a])][0])
        bi_path = (root, p2[root], late[(root, p2[root])])
        variant = st.segmented_control("Memory setting", ["Full information", "Forget own first action", "Forget the stage"],
                                       default="Full information", key="gt_mem") or "Full information"
        leaves = {k: f"{v[0]}, {v[1]}" for k, v in lv.items()}
        if variant == "Full information":
            chosen = {(root,)} | {(a, p2[a]) for a in LR} | {(a, b, late[(a, b)]) for a in LR for b in LR}
            sets, pth = [], bi_path
            text = (f"Every node is separate: P1 knows its first move, P2's move and that this is the second visit. "
                    f"Backward induction: later P1 picks {', '.join(f'{late[k]} after {k[0]}{k[1]}' for k in late)}; "
                    f"P2 picks {p2['L']} after L and {p2['R']} after R; P1 starts with {root}. "
                    f"<b>Path {'-'.join(bi_path)}, payoffs ({lv[bi_path][0]}, {lv[bi_path][1]}).</b>")
        elif variant == "Forget own first action":
            chosen, pth = set(), None
            sets = [[("L", "L"), ("R", "L")], [("L", "R"), ("R", "R")]]
            text = ("The root stays separate. P1 knows it is at the <b>later</b> move and sees P2's action, but has forgotten "
                    "its <b>own first action</b>: nodes after (L,L) and (R,L) are one set (cyan), (L,R) and (R,R) another "
                    "(amber). One action must be chosen per set, so P1 can no longer play R after LL and L after RL. "
                    "This is <b>imperfect recall</b>.")
        else:
            chosen, pth = set(), None
            sets = [[(), ("L", "L"), ("L", "R"), ("R", "L"), ("R", "R")]]
            text = ("P1's root and all four later nodes form <b>one information set</b>. P1 sees no clock, counter, "
                    "earlier choice or P2 action, so it cannot tell the first visit from the second and must use the same "
                    "action (or the same randomisation) every time. P2 still observes P1's first action.")
        st.markdown(tree_svg(3, ["P1", "P2", "P1"], leaves, chosen=chosen, info_sets=sets, path=pth, width=980,
                             level_gap=95), unsafe_allow_html=True)
        st.markdown(f'<div class="card"><p>{text}</p></div>', unsafe_allow_html=True)

    elif part == "Mixed vs behavioral":
        rows = list(csv.DictReader(open(STARTER / "memory_tree.csv")))
        lv = {(r["p1_first"], r["p2_action"], r["p1_second"]): int(r["p1_payoff"]) for r in rows}
        u = {"LL": lv[("L", "L", "L")], "LR": lv[("L", "L", "R")], "RL": lv[("R", "L", "L")], "RR": lv[("R", "L", "R")]}
        strat = {"Mixed 50-50 lottery": {"LL": .5, "LR": 0, "RL": 0, "RR": .5},
                 "Fresh 50-50 draws (forgot stage)": {k: .25 for k in u},
                 "Behavioral + perfect recall": {"LL": .5, "LR": 0, "RL": 0, "RR": .5}}
        l, r = st.columns([1, 1])
        with l:
            trs = "".join(f"<tr><td>{n}</td>" + "".join(f"<td>{p[k]:g}</td>" for k in u) +
                          f"<td>{sum(p.values()):g}</td><td class='hl'>{sum(p[k] * u[k] for k in u):g}</td></tr>"
                          for n, p in strat.items())
            st.markdown(f"""<div class="card"><span class="badge info">P2 fixed to L · P1 payoffs
            LL {u['LL']} · LR {u['LR']} · RL {u['RL']} · RR {u['RR']}</span>
            <table class="calc" style="margin-top:12px"><tr><th>Strategy</th><th>LL</th><th>LR</th><th>RL</th><th>RR</th>
            <th>Σ</th><th>E[u₁]</th></tr>{trs}</table>
            <p style="margin-top:12px">With <b>perfect recall</b>, randomising 50-50 first and then repeating the remembered
            first action reproduces the mixed lottery exactly (same terminal probabilities, Kuhn's theorem).
            With a <b>forgotten stage</b> P1 cannot tell visits apart or remember its first action, so its draws are
            independent and also reach LR and RL: 4.25 vs 1.5. Under imperfect recall, mixed ≠ behavioral.</p></div>""",
                        unsafe_allow_html=True)
        with r:
            fig = go.Figure()
            for (n, p), c in zip(strat.items(), (P0_COLOR, LIME, CYAN)):
                fig.add_bar(x=list(u), y=[p[k] for k in u], name=n, marker_color=c)
            fig.update_layout(barmode="group", title=dict(text="Terminal probabilities of P1 action pairs",
                                                          font=dict(size=13, color=MUTED), x=0))
            st.plotly_chart(style_fig(fig, 380), config=CFG, width="stretch")

    elif part == "Repeated games":
        l, r = st.columns([1, 1.3])
        with l:
            dlt = st.slider("Discount factor δ (weight on next round's payoff)", 0.0, 0.95, 0.5, 0.05, key="gt_delta")
            coop, dev = 4 / (1 - dlt), 6 + dlt / (1 - dlt)
            k1, k2 = st.columns(2)
            k1.markdown(kpi("Cooperate forever", f"{coop:.3f}", "", None), unsafe_allow_html=True)
            k2.markdown(kpi("Deviate now", f"{dev:.3f}", "", None), unsafe_allow_html=True)
            ok = coop >= dev - 1e-12
            st.markdown(f"""<div class="card" style="margin-top:14px">
            <span class="badge {'pass' if ok else 'fail'}">{'Cooperation sustained' if ok else 'Deviation pays'}</span>
            <p style="margin-top:10px">4/(1−δ) ≥ 6 + δ/(1−δ) &nbsp;→&nbsp; 4 ≥ 6(1−δ) + δ &nbsp;→&nbsp; 4 ≥ 6 − 5δ
            &nbsp;→&nbsp; <b style="color:{LIME}">δ ≥ 0.4</b>.<br>
            δ = 0.2: 5.00 vs 6.25 (deviate) · δ = 0.5: 8.00 vs 7.00 (cooperate).<br>
            <b>Punishment check:</b> once the other plays H forever, H gives 1 &gt; C gives 0, so H stays a best response.<br>
            <b>Finite, 3 known rounds:</b> (H, H) is the unique stage equilibrium, so round 3 is (H, H); then round 2,
            then round 1. Outcome (H, H) in all three rounds, 1 point each.</p></div>""", unsafe_allow_html=True)
        with r:
            xs = [i / 100 for i in range(0, 96)]
            fig = go.Figure()
            fig.add_scatter(x=xs, y=[4 / (1 - x) for x in xs], name="Cooperate forever  4/(1−δ)", line=dict(color=LIME, width=3))
            fig.add_scatter(x=xs, y=[6 + x / (1 - x) for x in xs], name="Deviate now  6 + δ/(1−δ)", line=dict(color=RED, width=3))
            fig.add_scatter(x=xs, y=[4 + 4 * x + 6 * x * x + x ** 3 / (1 - x) for x in xs], name="Cooperate twice, then deviate",
                            line=dict(color=CYAN, width=2, dash="dot"))
            fig.add_vline(x=.4, line=dict(color=AMBER, dash="dash"), annotation_text="threshold δ = 0.4",
                          annotation_font_color=AMBER)
            fig.add_vline(x=dlt, line=dict(color="#7d8b99", width=1))
            fig.update_yaxes(range=[0, 30], title="discounted total")
            fig.update_xaxes(title="δ")
            st.plotly_chart(style_fig(fig, 430), config=CFG, width="stretch")

    else:  # Bayesian
        l, r = st.columns([1.3, 1])
        fee = 1.5
        alpha = {"urgent": 0, "flexible": 1}
        plan = {"urgent": "C", "flexible": "H"}

        def bayes(pi):
            prior = {"urgent": pi, "flexible": 1 - pi}

            def uu(own, opp, t):
                return G[(own, opp)][0] - fee + alpha[t] if own == "H" else G[(own, opp)][0]
            out = {}
            for t in ("urgent", "flexible"):
                out[t] = {a: (sum(prior[o] * uu(a, plan[o], t) for o in prior),
                              " + ".join(f"{prior[o]:.2f}×{uu(a, plan[o], t):g}" for o in prior)) for a in A}
            return out

        res = bayes(0.30)
        with l:
            trs, ok = "", True
            for t in ("urgent", "flexible"):
                best = max(A, key=lambda a: res[t][a][0])
                ok &= best == plan[t]
                trs += (f"<tr><td>{t.title()}</td><td>{res[t]['C'][1]} = <b>{res[t]['C'][0]:.2f}</b></td>"
                        f"<td>{res[t]['H'][1]} = <b>{res[t]['H'][0]:.2f}</b></td><td class='hl'>{best}</td>"
                        f"<td>{plan[t]} {'✓' if best == plan[t] else '✗'}</td></tr>")
            st.markdown(f"""<div class="card"><span class="badge {'pass' if ok else 'fail'}">
            {'Bayesian Nash equilibrium' if ok else 'Not an equilibrium'}</span>
            <p style="margin-top:10px">π(Urgent) = 0.30, fee F = 1.5 on own H, Flexible +1 on own H.
            Proposed plan: <b>Urgent → C, Flexible → H</b>, so the opponent plays C w.p. 0.30 and H w.p. 0.70.</p>
            <table class="calc"><tr><th>Own type</th><th>E[C]</th><th>E[H]</th><th>Best</th><th>Plan</th></tr>{trs}</table>
            <p style="margin-top:10px">Both players are symmetric, so the same four numbers check P1 and P2.
            No type of either player gains by changing its own choice alone.</p></div>""", unsafe_allow_html=True)
        with r:
            pis = [i / 100 for i in range(0, 101)]
            fig = go.Figure()
            fig.add_scatter(x=pis, y=[bayes(p)["urgent"]["C"][0] - bayes(p)["urgent"]["H"][0] for p in pis],
                            name="Urgent: E[C] − E[H]", line=dict(color=AMBER, width=3))
            fig.add_scatter(x=pis, y=[bayes(p)["flexible"]["H"][0] - bayes(p)["flexible"]["C"][0] for p in pis],
                            name="Flexible: E[H] − E[C]", line=dict(color=CYAN, width=3))
            fig.add_hline(y=0, line_color="#46525e")
            fig.add_vline(x=.3, line=dict(color=LIME, dash="dash"), annotation_text="π = 0.30",
                          annotation_font_color=LIME)
            fig.update_xaxes(title="prior π(Urgent)")
            fig.update_layout(title=dict(text="Optional sensitivity: plan holds while both lines ≥ 0 (π ≤ 0.5)",
                                         font=dict(size=13, color=MUTED), x=0))
            st.plotly_chart(style_fig(fig, 400), config=CFG, width="stretch")

# ================================================================== EVOLUTION
with tab_evo:
    st.markdown(section("04 · Evolutionary dynamics", "Does releasing spread when it pays?",
                        "x = share choosing C. f<sub>C</sub> = 4x, f<sub>H</sub> = (6−F)x + (1−F)(1−x), "
                        "x<sub>next</sub> = x + 0.05·x(1−x)(f<sub>C</sub> − f<sub>H</sub>). Start x = 0.5, 30 updates."),
                unsafe_allow_html=True)
    p0, p2 = evo_path(0), evo_path(2)
    fc, fh = payoffs(0.5, 0)
    x1 = update(0.5, 0)
    k = st.columns(4)
    k[0].markdown(kpi("First step f_C · f_H", f"{fc:g} · {fh:g}", "", None), unsafe_allow_html=True)
    k[1].markdown(kpi("x after 1 update (F=0)", f"{x1:.5f}", "", None) +
                  f'<div style="margin:-4px 0 0 4px"><span class="badge {"pass" if abs(x1 - 0.48125) < 1e-12 else "fail"}">'
                  f'matches 0.48125</span></div>', unsafe_allow_html=True)
    k[2].markdown(kpi("Final share C, F = 0", f"{p0[-1]:.3f}", "", p0[-1] - p0[0], "higher", "{:+.3f}", "since start"),
                  unsafe_allow_html=True)
    k[3].markdown(kpi("Final share C, F = 2", f"{p2[-1]:.3f}", "", p2[-1] - p2[0], "higher", "{:+.3f}", "since start"),
                  unsafe_allow_html=True)
    fig = go.Figure()
    fig.add_scatter(x=list(range(31)), y=p0, name="F = 0 (no fee)", mode="lines+markers",
                    line=dict(color=RED, width=3), marker=dict(size=6))
    fig.add_scatter(x=list(range(31)), y=p2, name="F = 2 (idle fee)", mode="lines+markers",
                    line=dict(color=LIME, width=3), marker=dict(size=6))
    fig.update_yaxes(range=[0, 1], title="share choosing C (release)")
    fig.update_xaxes(title="update")
    st.plotly_chart(style_fig(fig, 440), config=CFG, width="stretch")
    st.markdown(f"""<div class="card"><p><b>F = 0:</b> f<sub>C</sub> − f<sub>H</sub> = −(1 + x) &lt; 0, so holding always
    earns more and <b style="color:{RED}">C becomes less common</b>. <b>F = 2:</b> f<sub>C</sub> − f<sub>H</sub> = 1 − x &gt; 0
    for x &lt; 1, so <b style="color:{LIME}">C becomes more common</b>. Every share stays in [0, 1]
    (min {min(p0 + p2):.3f}, max {max(p0 + p2):.3f}). This is one model path over 30 updates, not proof of an
    evolutionarily stable strategy or a forecast of real drivers.</p></div>""", unsafe_allow_html=True)

# ================================================================== MINI CASE
with tab_mini:
    st.markdown(section("05 · Verification", "The supplied mini case, re-run live",
                        "One charger, three drivers, P0. The real simulator engine runs right now and is compared with "
                        "mini_case_expected.json."), unsafe_allow_html=True)
    expected = json.loads((STARTER / "mini_case_expected.json").read_text())
    arrivals = {r["driver_id"]: int(r["arrival_slot"]) for r in csv.DictReader(open(STARTER / "mini_case_public.csv"))}
    cols = st.columns(2)
    for c, (name, override, label) in zip(cols, [("all_release", {}, "Everyone releases"),
                                                 ("A_holds_one_slot", {"A": 1}, "A holds one slot")]):
        got, exp = run_case(override), expected[name]
        ok = all(got[k] == exp[k] for k in exp)
        with c:
            st.markdown(f'<div class="card"><span class="badge {"pass" if ok else "fail"}">{"PASS" if ok else "FAIL"}</span>'
                        f'<h4 style="margin-top:10px">{label}</h4><p>Total waiting <b>{got["total_wait_slots"]}</b> slots · '
                        f'energy <b>{got["delivered_kwh"]:g}</b> kWh · utility <b style="color:{LIME}">{got["total_utility"]:g}</b></p></div>',
                        unsafe_allow_html=True)
            fig = go.Figure()
            for drv in ("C", "B", "A"):
                g = got[drv]
                fig.add_bar(y=[drv], x=[g["start"] - arrivals[drv]], base=[arrivals[drv]], orientation="h",
                            marker=dict(color="rgba(125,139,153,.25)", line=dict(color="#7d8b99", width=1),
                                        pattern=dict(shape=".", fgcolor="#7d8b99")),
                            name="Waiting", showlegend=drv == "C", legendgroup="w")
                fig.add_bar(y=[drv], x=[g["finish"] - g["start"]], base=[g["start"]], orientation="h",
                            marker_color=LIME, name="Charging", showlegend=drv == "C", legendgroup="c")
                if g["release"] > g["finish"]:
                    fig.add_bar(y=[drv], x=[g["release"] - g["finish"]], base=[g["finish"]], orientation="h",
                                marker=dict(color="rgba(255,93,108,.25)", line=dict(color=RED, width=1.5),
                                            pattern=dict(shape="/", fgcolor=RED)), name="Idle hold", legendgroup="i")
            fig.update_layout(barmode="overlay")
            fig.update_xaxes(range=[0, 6], dtick=1, title="slot boundary")
            st.plotly_chart(style_fig(fig, 250), config=CFG, width="stretch")
            trs = "".join(
                f"<tr><td>{drv}</td>" + "".join(
                    f"<td class='{'hl' if got[drv][f] == exp[drv][f] else ''}'>{got[drv][f]:g}"
                    f"<span style='color:{MUTED}'> / {exp[drv][f]}</span></td>"
                    for f in ("start", "finish", "release", "wait_slots", "utility")) + "</tr>" for drv in ("A", "B", "C"))
            st.markdown(f'<table class="calc"><tr><th>Driver</th><th>Start</th><th>Finish</th><th>Release</th>'
                        f'<th>Wait</th><th>Utility</th></tr>{trs}</table>'
                        f'<p style="color:{MUTED};font-size:.78rem;margin-top:6px">simulated / expected</p>',
                        unsafe_allow_html=True)

# ================================================================== FINDINGS
with tab_find:
    st.markdown(section("06 · What we found", "Does the idle fee help, and whom?",
                        "Numbers below are pulled from results/paired_comparison.csv. Five synthetic seeds are not proof "
                        "of behaviour at a real campus."), unsafe_allow_html=True)
    w = {dmd: pdiff("main", dmd, "all_avg_waiting_slots") for dmd in DEMANDS}
    s = {dmd: pdiff("main", dmd, "all_share_fully_served") for dmd in DEMANDS}
    ua = {dmd: pdiff("main", dmd, "all_total_utility_after_penalty") for dmd in DEMANDS}
    rh = {dmd: pdiff("main", dmd, "rule_hold_avg_utility_after_penalty") for dmd in DEMANDS}
    rr = {dmd: pdiff("main", dmd, "rule_release_avg_utility_after_penalty") for dmd in DEMANDS}
    fu = {dmd: pdiff("main", dmd, "flexible_avg_utility_after_penalty") for dmd in DEMANDS}
    lh = pdiff("all_hold", "medium", "all_avg_waiting_slots")
    c1, c2 = st.columns(2)
    c1.markdown(f"""<div class="card"><span class="badge pass">Waiting falls</span>
    <h4 style="margin-top:10px">P1 reduces waiting at every demand level</h4>
    <p>Mean change in average waiting: low <b>{w['low'].mean_diff_P1_minus_P0:+.3f}</b>, medium
    <b>{w['medium'].mean_diff_P1_minus_P0:+.3f}</b>, high <b>{w['high'].mean_diff_P1_minus_P0:+.3f}</b> slots; every seed
    agrees in sign. Share fully served rises by {s['low'].mean_diff_P1_minus_P0:+.1%}, {s['medium'].mean_diff_P1_minus_P0:+.1%}
    and {s['high'].mean_diff_P1_minus_P0:+.1%}. Urgent and Flexible drivers both benefit.</p></div>""", unsafe_allow_html=True)
    c2.markdown(f"""<div class="card"><span class="badge fail">Not free</span>
    <h4 style="margin-top:10px">At low demand the fee costs more than it saves</h4>
    <p>Total utility after penalty changes by <b style="color:{RED}">{ua['low'].mean_diff_P1_minus_P0:+,.0f}</b> at low demand
    (range {ua['low'].min_diff:+,.0f} to {ua['low'].max_diff:+,.0f}): little queue to clear, so penalties and lost idle
    benefit outweigh the time saved. At medium and high demand it rises
    ({ua['medium'].mean_diff_P1_minus_P0:+,.0f} and {ua['high'].mean_diff_P1_minus_P0:+,.0f}).</p></div>""",
                unsafe_allow_html=True)
    c3, c4 = st.columns(2)
    c3.markdown(f"""<div class="card"><span class="badge info">Who gains · who pays</span>
    <h4 style="margin-top:10px">Releasers win, fixed holders pay</h4>
    <p>Release-rule drivers gain {rr['low'].mean_diff_P1_minus_P0:+.2f} / {rr['medium'].mean_diff_P1_minus_P0:+.2f} /
    {rr['high'].mean_diff_P1_minus_P0:+.2f} points per visit (low / medium / high). Hold-rule drivers change by
    {rh['low'].mean_diff_P1_minus_P0:+.2f} / {rh['medium'].mean_diff_P1_minus_P0:+.2f} / {rh['high'].mean_diff_P1_minus_P0:+.2f}.
    Flexible drivers value idling more (h = 2), so at low demand they lose
    {fu['low'].mean_diff_P1_minus_P0:+.2f} per visit.</p></div>""", unsafe_allow_html=True)
    c4.markdown(f"""<div class="card"><span class="badge info">Limit</span>
    <h4 style="margin-top:10px">A fee only works on drivers who respond</h4>
    <p>With every driver fixed to Hold, waiting changes by exactly {lh.mean_diff_P1_minus_P0:+.3f}: the fee only transfers
    points. In the main runs it acts through the Fee-aware drivers (25 %) and indirectly through Reciprocal memory.
    The evolutionary model agrees in direction: with F = 2 the release share grows, with F = 0 it shrinks.</p></div>""",
                unsafe_allow_html=True)

st.markdown(f'<div style="text-align:center;color:#4a5663;font-size:.75rem;margin:40px 0 10px;letter-spacing:.12em">'
            f'SYNTHETIC TEACHING DATA · UTILITY IN TEACHING POINTS · RESULTS FROM run_experiments.py</div>',
            unsafe_allow_html=True)
