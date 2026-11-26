"""Visual theme: CSS, Plotly styling, KPI cards and SVG game trees."""
import html

LIME, CYAN, AMBER, RED = "#c8ff3d", "#3dd6ff", "#ffb547", "#ff5d6c"
TEXT, MUTED, PANEL, BORDER, GRID = "#e8edf2", "#8a97a6", "#0f141a", "#1c252e", "#1a232c"
P0_COLOR, P1_COLOR = "#7d8b99", LIME
TYPE_COLOR = {"urgent": AMBER, "flexible": CYAN}

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@400;500;600&display=swap');
.stApp, .stApp p, .stApp div, .stApp label, .stApp li, .stApp button, .stApp input, .stApp td, .stApp th
  {{ font-family: 'Inter', 'Segoe UI', system-ui, sans-serif; }}
.stApp [data-testid="stIconMaterial"], .stApp [data-testid="stExpanderIcon"] {{ font-family: 'Material Symbols Rounded' !important; }}
.stApp {{
  background:
    radial-gradient(900px 500px at 90% -5%, rgba(200,255,61,.07), transparent 60%),
    radial-gradient(700px 400px at -10% 30%, rgba(61,214,255,.05), transparent 60%),
    #07090c;
}}
header[data-testid="stHeader"] {{ background: transparent; }}
#MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"] {{ display: none !important; }}
.block-container {{ padding-top: 1.2rem; max-width: 1380px; }}
h1, h2, h3, h4 {{ font-family: 'Space Grotesk', sans-serif !important; letter-spacing: -.02em; }}

/* nav */
.navbar {{ display:flex; align-items:center; justify-content:space-between; padding: 6px 2px 18px; }}
.brand {{ font-family:'Space Grotesk','Segoe UI',sans-serif; font-weight:700; font-size:1.05rem; color:{TEXT}; letter-spacing:.02em; }}
.brand span {{ color:{LIME}; }}
.navmeta {{ color:{MUTED}; font-size:.78rem; letter-spacing:.14em; text-transform:uppercase; }}
.pill {{ display:inline-block; border:1px solid {BORDER}; border-radius:999px; padding:6px 14px; margin-left:6px;
        color:{TEXT}; font-size:.74rem; letter-spacing:.08em; text-transform:uppercase; background:#0d1217; }}
.pill.on {{ background:{LIME}; color:#07090c; border-color:{LIME}; font-weight:600; }}

/* hero */
.hero {{ position:relative; border:1px solid {BORDER}; border-radius:28px; padding:46px 48px; overflow:hidden;
        background: linear-gradient(120deg, #0d1318 0%, #0a0e12 55%, #10170b 100%); }}
.hero:after {{ content:""; position:absolute; inset:auto -20% -60% 40%; height:120%;
              background: radial-gradient(closest-side, rgba(200,255,61,.16), transparent); pointer-events:none; }}
.eyebrow {{ color:{LIME}; font-size:.74rem; letter-spacing:.28em; text-transform:uppercase; font-weight:600; }}
.hero h1 {{ font-size:4.1rem; line-height:.98; margin:.35em 0 .3em; color:{TEXT}; font-weight:700; }}
.hero h1 em {{ font-style:normal; color:{LIME}; }}
.hero p.lead {{ color:#b4c0cc; font-size:1.06rem; max-width:560px; line-height:1.6; }}
.cta {{ display:inline-block; margin-top:18px; background:{LIME}; color:#07090c !important; padding:11px 22px;
       border-radius:999px; font-weight:600; font-size:.9rem; text-decoration:none; }}
.cta.ghost {{ background:transparent; color:{TEXT} !important; border:1px solid {BORDER}; margin-left:8px; }}

/* stat strip */
.stats {{ display:grid; grid-template-columns: repeat(6, 1fr); border:1px solid {BORDER}; border-radius:22px;
         margin-top:18px; background:#0b1015; }}
.stat {{ padding:20px 22px; border-right:1px solid {BORDER}; }}
.stat:last-child {{ border-right:none; }}
.stat .v {{ font-family:'Space Grotesk','Segoe UI',sans-serif; font-size:2rem; font-weight:600; color:{TEXT}; }}
.stat .v small {{ color:{LIME}; font-size:1rem; margin-left:2px; }}
.stat .l {{ color:{MUTED}; font-size:.72rem; letter-spacing:.14em; text-transform:uppercase; margin-top:2px; }}

.topics {{ display:flex; flex-wrap:wrap; gap:28px; justify-content:space-between; padding:20px 8px 4px;
          color:#5d6a77; font-family:'Space Grotesk','Segoe UI',sans-serif; letter-spacing:.24em; font-size:.78rem; text-transform:uppercase; }}

/* tabs */
.stTabs [data-baseweb="tab-list"] {{ gap:4px; background:#0d1217; padding:6px; border-radius:999px;
    border:1px solid {BORDER}; width:fit-content; margin: 26px 0 10px; }}
.stTabs [data-baseweb="tab"] {{ border-radius:999px; padding:8px 20px; height:auto; color:{MUTED}; background:transparent; }}
.stTabs [data-baseweb="tab"] p {{ font-size:.86rem; font-weight:500; letter-spacing:.02em; }}
.stTabs [aria-selected="true"] {{ background:{LIME} !important; }}
.stTabs [aria-selected="true"] p {{ color:#07090c !important; font-weight:600; }}
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] {{ display:none; }}

/* section headers */
.sec {{ margin: 30px 0 14px; }}
.sec .eyebrow {{ font-size:.7rem; }}
.sec h2 {{ font-size:2rem; margin:.15em 0 .1em; color:{TEXT}; }}
.sec p {{ color:{MUTED}; max-width:820px; margin:0; }}

/* cards */
.kpi {{ background: linear-gradient(180deg,#10161d,#0b1015); border:1px solid {BORDER}; border-radius:20px;
       padding:18px 20px 16px; height:100%; }}
.kpi .label {{ color:{MUTED}; font-size:.7rem; letter-spacing:.16em; text-transform:uppercase; }}
.kpi .value {{ font-family:'Space Grotesk','Segoe UI',sans-serif; font-size:2.15rem; font-weight:600; color:{TEXT}; margin-top:4px; line-height:1.1; }}
.kpi .value small {{ font-size:.95rem; color:{MUTED}; margin-left:3px; font-weight:400; }}
.kpi .delta {{ font-size:.8rem; margin-top:6px; color:{MUTED}; }}
.kpi .delta b.good {{ color:{LIME}; }} .kpi .delta b.bad {{ color:{RED}; }} .kpi .delta b.flat {{ color:{TEXT}; }}
.card {{ background:#0c1116; border:1px solid {BORDER}; border-radius:20px; padding:20px 22px; }}
.card h4 {{ margin:0 0 6px; color:{TEXT}; font-size:1.05rem; }}
.card p, .card li {{ color:#aeb9c4; font-size:.92rem; line-height:1.55; }}
.badge {{ display:inline-block; padding:3px 10px; border-radius:999px; font-size:.7rem; font-weight:600;
         letter-spacing:.1em; text-transform:uppercase; }}
.badge.pass {{ background:rgba(200,255,61,.12); color:{LIME}; border:1px solid rgba(200,255,61,.35); }}
.badge.fail {{ background:rgba(255,93,108,.12); color:{RED}; border:1px solid rgba(255,93,108,.35); }}
.badge.info {{ background:rgba(61,214,255,.1); color:{CYAN}; border:1px solid rgba(61,214,255,.3); }}
.mono {{ font-family: ui-monospace, 'JetBrains Mono', Consolas, monospace; font-size:.85rem; color:#c9d3dc; }}

/* payoff matrix */
table.mx {{ border-collapse:separate; border-spacing:6px; margin:6px 0; }}
table.mx td, table.mx th {{ padding:14px 22px; border-radius:14px; text-align:center; font-family:'Space Grotesk','Segoe UI',sans-serif; }}
table.mx th {{ color:{MUTED}; font-weight:500; font-size:.85rem; }}
table.mx td {{ background:#111820; border:1px solid {BORDER}; color:{TEXT}; font-size:1.15rem; }}
table.mx td.ne {{ background:rgba(200,255,61,.1); border-color:{LIME}; }}
table.mx b {{ color:{LIME}; }}

table.calc {{ width:100%; border-collapse:collapse; }}
table.calc th {{ color:{MUTED}; font-size:.72rem; letter-spacing:.12em; text-transform:uppercase; text-align:left;
                padding:10px 12px; border-bottom:1px solid {BORDER}; font-weight:500; }}
table.calc td {{ padding:11px 12px; border-bottom:1px solid #141b22; color:{TEXT}; font-size:.92rem; }}
table.calc td.hl {{ color:{LIME}; font-weight:600; }}

/* widgets */
div[data-testid="stSegmentedControl"] button, [data-testid="stBaseButton-segmented_control"],
[data-testid="stBaseButton-segmented_controlActive"] {{ border-radius:999px !important; }}
[data-testid="stExpander"] {{ border:1px solid {BORDER}; border-radius:18px; background:#0b1015; }}
[data-testid="stDataFrame"] {{ border-radius:14px; overflow:hidden; }}
</style>
"""

CHARGER_SVG = f"""
<svg viewBox="0 0 360 380" xmlns="http://www.w3.org/2000/svg" style="width:100%;max-width:360px;display:block;margin:auto">
  <defs>
    <linearGradient id="body" x1="0" x2="1"><stop offset="0" stop-color="#1b232b"/><stop offset=".5" stop-color="#2a343e"/><stop offset="1" stop-color="#151b21"/></linearGradient>
    <linearGradient id="screen" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0d1a10"/><stop offset="1" stop-color="#050807"/></linearGradient>
    <radialGradient id="glow"><stop offset="0" stop-color="{LIME}" stop-opacity=".55"/><stop offset="1" stop-color="{LIME}" stop-opacity="0"/></radialGradient>
    <filter id="blur"><feGaussianBlur stdDeviation="6"/></filter>
  </defs>
  <ellipse cx="180" cy="352" rx="150" ry="18" fill="url(#glow)" opacity=".6"/>
  <rect x="110" y="40" width="120" height="300" rx="26" fill="url(#body)" stroke="#36414c"/>
  <rect x="124" y="60" width="92" height="120" rx="14" fill="url(#screen)" stroke="#2b3640"/>
  <circle cx="170" cy="112" r="30" fill="none" stroke="#1e2a20" stroke-width="7"/>
  <circle cx="170" cy="112" r="30" fill="none" stroke="{LIME}" stroke-width="7" stroke-linecap="round"
          stroke-dasharray="150 189" transform="rotate(-90 170 112)">
     <animate attributeName="stroke-dasharray" values="20 189;170 189;20 189" dur="6s" repeatCount="indefinite"/>
  </circle>
  <text x="170" y="119" text-anchor="middle" font-family="Space Grotesk, Segoe UI, sans-serif" font-size="18" fill="{TEXT}" font-weight="600">kWh</text>
  <rect x="136" y="152" width="68" height="6" rx="3" fill="#1d2a1f"/><rect x="136" y="152" width="44" height="6" rx="3" fill="{LIME}"/>
  <rect x="140" y="200" width="60" height="6" rx="3" fill="#25303a"/>
  <rect x="140" y="214" width="40" height="6" rx="3" fill="#25303a"/>
  <rect x="226" y="150" width="20" height="54" rx="8" fill="#20282f" stroke="#36414c"/>
  <path d="M236 204 C 250 280, 300 270, 300 330" fill="none" stroke="#11161b" stroke-width="11" stroke-linecap="round"/>
  <path d="M236 204 C 250 280, 300 270, 300 330" fill="none" stroke="#2a333c" stroke-width="5" stroke-linecap="round"/>
  <rect x="120" y="52" width="100" height="3" rx="2" fill="{LIME}" opacity=".9" filter="url(#blur)"/>
  <rect x="128" y="52" width="84" height="2" rx="1" fill="{LIME}"/>
  <path d="M168 258 l-10 20 h12 l-6 18 l18 -26 h-12 l6 -12 z" fill="{LIME}"/>
</svg>
"""


def style_fig(fig, height=360, legend=True):
    fig.update_layout(
        template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color="#c9d3dc", size=12),
        margin=dict(l=8, r=8, t=64 if legend else 40, b=8), height=height, showlegend=legend,
        legend=dict(orientation="h", yanchor="bottom", y=1.01, x=1, xanchor="right", bgcolor="rgba(0,0,0,0)"),
        hoverlabel=dict(bgcolor="#10161d", bordercolor=BORDER, font=dict(color=TEXT)),
        bargap=0.28,
    )
    fig.update_xaxes(gridcolor=GRID, zeroline=False, linecolor=BORDER)
    fig.update_yaxes(gridcolor=GRID, zeroline=False, linecolor=BORDER)
    return fig


def section(eyebrow, title, sub=""):
    return (f'<div class="sec"><div class="eyebrow">{eyebrow}</div><h2>{title}</h2>'
            + (f"<p>{sub}</p>" if sub else "") + "</div>")


def kpi(label, value, unit="", delta=None, good_when="lower", fmt="{:+.3f}", note="vs other policy"):
    d = ""
    if delta is not None:
        if abs(delta) < 1e-12:
            cls = "flat"
        else:
            cls = "good" if (delta < 0) == (good_when == "lower") else "bad"
        d = f'<div class="delta"><b class="{cls}">{fmt.format(delta)}</b> {note}</div>'
    return (f'<div class="kpi"><div class="label">{label}</div>'
            f'<div class="value">{value}<small>{unit}</small></div>{d}</div>')


def tree_svg(depth, players, leaves, chosen=frozenset(), info_sets=(), width=760, level_gap=92,
             set_colors=(CYAN, AMBER, "#c38bff", LIME), actions=("L", "R"), path=None):
    """Binary L/R (or C/H) game tree.

    players: list of player names per level, e.g. ["P1","P2","P1"]
    leaves: {path tuple: payoff string}
    chosen: set of path prefixes (tuples) whose last edge is highlighted
    info_sets: list of lists of node paths joined in one information set
    """
    actions = list(actions)
    n_leaves = 2 ** depth
    pad = 50
    leaf_x = [pad + i * (width - 2 * pad) / (n_leaves - 1) for i in range(n_leaves)]
    height = 60 + depth * level_gap + 70

    def paths(level):
        out = [()]
        for _ in range(level):
            out = [p + (a,) for p in out for a in actions]
        return out

    def pos(path):
        lvl = len(path)
        idx = 0
        for a in path:
            idx = idx * 2 + actions.index(a)
        span = 2 ** (depth - lvl)
        xs = leaf_x[idx * span:(idx + 1) * span]
        return sum(xs) / len(xs), 40 + lvl * level_gap

    parts = [f'<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" '
             f'style="width:100%;display:block">']
    # edges
    for lvl in range(depth):
        for p in paths(lvl):
            x1, y1 = pos(p)
            for a in actions:
                q = p + (a,)
                x2, y2 = pos(q)
                on = q in chosen
                parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{LIME if on else "#34404b"}" '
                             f'stroke-width="{3 if on else 1.6}"/>')
                mx, my = (x1 + x2) / 2, (y1 + y2) / 2
                parts.append(f'<text x="{mx + (-12 if a == actions[0] else 12)}" y="{my}" text-anchor="middle" '
                             f'font-family="Space Grotesk, Segoe UI, sans-serif" font-size="13" fill="{LIME if on else MUTED}">{a}</text>')
    # information sets
    ring = {}
    for k, group in enumerate(info_sets):
        col = set_colors[k % len(set_colors)]
        pts = sorted((pos(g) for g in group), key=lambda t: (t[1], t[0]))
        for (xa, ya), (xb, yb) in zip(pts, pts[1:]):
            parts.append(f'<line x1="{xa}" y1="{ya}" x2="{xb}" y2="{yb}" stroke="{col}" stroke-width="2" '
                         f'stroke-dasharray="6 6" opacity=".85"/>')
        for g in group:
            ring[g] = col
    # decision nodes
    for lvl in range(depth):
        for p in paths(lvl):
            x, y = pos(p)
            col = ring.get(p)
            parts.append(f'<circle cx="{x}" cy="{y}" r="17" fill="#0f151b" stroke="{col or "#46525e"}" '
                         f'stroke-width="{2.5 if col else 1.5}"/>')
            parts.append(f'<text x="{x}" y="{y + 4.5}" text-anchor="middle" font-family="Space Grotesk, Segoe UI, sans-serif" '
                         f'font-size="12" font-weight="600" fill="{TEXT}">{html.escape(players[lvl])}</text>')
    # leaves
    for p in paths(depth):
        x, y = pos(p)
        on = p == path
        parts.append(f'<rect x="{x - 26}" y="{y - 13}" width="52" height="26" rx="8" '
                     f'fill="{"rgba(200,255,61,.12)" if on else "#0f151b"}" stroke="{LIME if on else "#2b3640"}"/>')
        parts.append(f'<text x="{x}" y="{y + 4.5}" text-anchor="middle" font-family="Space Grotesk, Segoe UI, sans-serif" '
                     f'font-size="12" fill="{LIME if on else TEXT}">{html.escape(leaves.get(p, ""))}</text>')
    parts.append("</svg>")
    return "".join(parts)
