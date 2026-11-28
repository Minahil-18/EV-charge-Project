"""Animated miniature charging station for one simulated day.

Builds a self-contained HTML/SVG/JS page from the saved visits of a run
(results/runs/<run>/visits.csv). Nothing is re-simulated: every car's arrival,
plug-in, finish, idle hold and departure comes straight from the saved file,
and the animation only interpolates between those slot boundaries.
"""
import json
import math

KWH_PER_SLOT = 3.0


def _num(x):
    if x is None:
        return None
    try:
        if isinstance(x, float) and math.isnan(x):
            return None
    except TypeError:
        pass
    return x


def _clock(t):
    m = 8 * 60 + 30 * int(t)
    return f"{m // 60:02d}:{m % 60:02d}"


def build_scenario(day_visits, label, policy, fee):
    """day_visits: DataFrame rows of one day of one run."""
    cars, events = [], []
    for r in day_visits.to_dict("records"):
        c = {
            "id": r["driver_id"], "type": r["private_type"], "rule": r["rule"],
            "a": int(r["arrival_slot"]), "d": int(r["departure_slot"]),
            "s": _num(r["start_slot"]), "f": _num(r["finish_slot"]), "r": _num(r["release_slot"]),
            "req": float(r["requested_kwh"]), "kwh": float(r["delivered_kwh"]),
            "ch": _num(r["charger_id"]), "act": r["action"], "idle": int(r["idle_slots"]),
            "wait": int(r["waiting_slots"]),
        }
        for k in ("s", "f", "r"):
            if c[k] is not None:
                c[k] = int(c[k])
        cars.append(c)

        who = f"<b>{c['id']}</b>"
        events.append((c["a"], 0, "arrive", f"{who} arrives · needs {c['req']:.0f} kWh"))
        if c["s"] is None:
            events.append((c["d"], 3, "bad", f"{who} gives up · never got a charger (waited {c['wait']} slots)"))
            continue
        w = f" after waiting {c['wait']} slot{'s' if c['wait'] != 1 else ''}" if c["wait"] else " straight away"
        events.append((c["s"], 2, "plug", f"{who} plugs into {c['ch']}{w}"))
        if c["act"] == "incomplete":
            events.append((c["r"], 1, "bad", f"{who} leaves {c['ch']} with only {c['kwh']:.0f}/{c['req']:.0f} kWh"))
        elif c["act"] in ("release", "forced_release"):
            events.append((c["f"], 1, "ok", f"{who} full · releases {c['ch']} right away"))
        else:
            fee_txt = f" · pays {fee * c['idle']:.0f} pts" if fee else " · no fee"
            events.append((c["f"], 1, "idle", f"{who} full · <b>holds {c['ch']} idle</b> for {c['idle']} slot"
                                              f"{'s' if c['idle'] > 1 else ''} ({c['rule']}){fee_txt}"))
            events.append((c["r"], 1, "ok", f"{who} finally frees {c['ch']}"))
    events.sort(key=lambda e: (e[0], e[1]))
    return {"label": label, "policy": policy, "fee": fee, "cars": cars,
            "events": [{"t": t, "k": k, "txt": f"<span class='tm'>{_clock(t)}</span>{txt}"}
                       for t, _, k, txt in events]}


def station_html(scenarios, chargers, day, slots=16):
    data = {"scenarios": scenarios, "chargers": chargers, "slots": slots, "day": day,
            "kwhPerSlot": KWH_PER_SLOT}
    return _TEMPLATE.replace("__DATA__", json.dumps(data))


def station_height(n_scenarios):
    return 130 + 760 * n_scenarios


_TEMPLATE = r"""<!doctype html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root{--lime:#c8ff3d;--cyan:#3dd6ff;--amber:#ffb547;--red:#ff5d6c;--text:#e8edf2;--muted:#8a97a6;--border:#1c252e;--panel:#0b1015}
*{box-sizing:border-box}
body{margin:0;background:transparent;color:var(--text);font-family:Inter,'Segoe UI',system-ui,sans-serif}
.bar{display:flex;align-items:center;gap:14px;flex-wrap:wrap;border:1px solid var(--border);border-radius:18px;
     padding:12px 16px;background:var(--panel);margin-bottom:14px}
.clock{font-family:'Space Grotesk','Segoe UI',sans-serif;font-size:2rem;font-weight:700;min-width:104px;color:var(--lime);letter-spacing:-.02em}
.clock small{display:block;font-size:.66rem;color:var(--muted);letter-spacing:.16em;text-transform:uppercase;font-weight:500}
button{background:#121a21;color:var(--text);border:1px solid var(--border);border-radius:999px;padding:8px 16px;
       font:600 .85rem Inter,'Segoe UI',sans-serif;cursor:pointer}
button:hover{border-color:#33414e}
button.main{background:var(--lime);color:#07090c;border-color:var(--lime);min-width:92px}
.speed button{padding:6px 11px;font-size:.75rem}
.speed button.on{background:#223019;border-color:var(--lime);color:var(--lime)}
.scrub{flex:1;min-width:240px;display:flex;flex-direction:column;gap:3px}
input[type=range]{width:100%;accent-color:var(--lime)}
.ticks{display:flex;justify-content:space-between;color:var(--muted);font-size:.66rem;font-family:'Space Grotesk',sans-serif}
.legend{display:flex;gap:14px;color:var(--muted);font-size:.74rem}
.legend i{display:inline-block;width:11px;height:11px;border-radius:3px;margin-right:5px;vertical-align:-1px}
.station{border:1px solid var(--border);border-radius:22px;background:var(--panel);padding:14px 16px 16px;margin-bottom:14px}
.shead{display:flex;align-items:center;justify-content:space-between;gap:10px;flex-wrap:wrap;margin-bottom:10px}
.stitle{font-family:'Space Grotesk','Segoe UI',sans-serif;font-weight:600;font-size:1.05rem}
.stitle span{color:var(--muted);font-weight:500;font-size:.85rem;margin-left:8px}
.chips{display:flex;gap:8px;flex-wrap:wrap}
.chip{border:1px solid var(--border);border-radius:12px;padding:5px 11px;background:#0d1318;min-width:74px}
.chip .v{font-family:'Space Grotesk',sans-serif;font-size:1.15rem;font-weight:600}
.chip .l{font-size:.6rem;letter-spacing:.12em;text-transform:uppercase;color:var(--muted)}
.grid{display:grid;grid-template-columns:minmax(0,1fr) 290px;gap:14px}
svg{width:100%;height:auto;display:block;border-radius:16px}
.log{border:1px solid var(--border);border-radius:16px;background:#0a0e12;padding:10px 12px;overflow:hidden;
     display:flex;flex-direction:column;gap:6px;font-size:.78rem;line-height:1.35;max-height:540px}
.log h4{margin:0 0 4px;font:600 .66rem Inter,sans-serif;letter-spacing:.16em;text-transform:uppercase;color:var(--muted)}
.ev{padding:6px 8px;border-radius:9px;background:#10161c;border-left:3px solid #33414e;color:#c6d0da;animation:pop .35s ease}
.ev.plug{border-left-color:var(--lime)}.ev.idle{border-left-color:var(--red);background:#1a1013}
.ev.bad{border-left-color:#c38bff}.ev.ok{border-left-color:var(--cyan)}
.ev .tm{font-family:'Space Grotesk',sans-serif;color:var(--muted);margin-right:7px}
@keyframes pop{from{opacity:0;transform:translateY(-5px)}to{opacity:1}}
.pulse{animation:pulse 1s ease-in-out infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.35}}
.flow{stroke-dasharray:5 6;animation:flow .6s linear infinite}
@keyframes flow{to{stroke-dashoffset:-11}}
@media (max-width:900px){.grid{grid-template-columns:1fr}.log{max-height:220px}}
</style></head><body>
<div class="bar">
  <div class="clock" id="clock">08:00<small id="slotlbl">slot 0 / 16</small></div>
  <button class="main" id="play">▶ Play</button>
  <button id="back" title="previous slot">⏮</button>
  <button id="fwd" title="next slot">⏭</button>
  <button id="reset">↺</button>
  <div class="speed" id="speed"></div>
  <div class="scrub"><input type="range" id="scrub" min="0" max="16" step="0.01" value="0"><div class="ticks" id="ticks"></div></div>
  <div class="legend"><span><i style="background:var(--amber)"></i>Urgent</span><span><i style="background:var(--cyan)"></i>Flexible</span>
  <span><i style="background:var(--lime)"></i>Charging</span><span><i style="background:var(--red)"></i>Idle hold</span></div>
</div>
<div id="stations"></div>
<script>
const DATA = __DATA__;
const SL = DATA.slots, CH = DATA.chargers, KPS = DATA.kwhPerSlot;
const COL = {lime:'#c8ff3d',cyan:'#3dd6ff',amber:'#ffb547',red:'#ff5d6c',muted:'#8a97a6',dead:'#4a5663'};
const TYPE = {urgent:COL.amber, flexible:COL.cyan};
const NS = 'http://www.w3.org/2000/svg';
const W = 1000, H = 540;
const NB = CH.length, BAY_W = 128, GAP = (W - 40 - NB*BAY_W)/(NB-1 || 1);
const bayX = i => 20 + i*(BAY_W+GAP);
const BAY_CY = 196, QY = 384, QHEAD = 905, QGAP = 76, QMAX = 11, ROAD_Y = 488;
const ENTRY = [-70, ROAD_Y], EXIT = [W+80, ROAD_Y];

function clock(t){const m = Math.floor(480 + 30*t + 1e-6); return String(Math.floor(m/60)).padStart(2,'0')+':'+String(m%60).padStart(2,'0');}
function S(tag, attrs, parent){const e=document.createElementNS(NS,tag);for(const k in attrs)e.setAttribute(k,attrs[k]);if(parent)parent.appendChild(e);return e;}

function staticScene(svg){
  svg.innerHTML = `
  <defs>
    <pattern id="asph" width="8" height="8" patternUnits="userSpaceOnUse"><rect width="8" height="8" fill="#0c1116"/><circle cx="2" cy="3" r=".6" fill="#141b22"/><circle cx="6" cy="6" r=".5" fill="#121920"/></pattern>
    <pattern id="solar" width="22" height="14" patternUnits="userSpaceOnUse"><rect width="22" height="14" fill="#0e1a26"/><rect x="1" y="1" width="20" height="12" fill="#13263a" stroke="#1d3a58" stroke-width=".8"/></pattern>
    <filter id="sh" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="4"/></filter>
    <radialGradient id="glow"><stop offset="0" stop-color="#c8ff3d" stop-opacity=".35"/><stop offset="1" stop-color="#c8ff3d" stop-opacity="0"/></radialGradient>
    <radialGradient id="rglow"><stop offset="0" stop-color="#ff5d6c" stop-opacity=".35"/><stop offset="1" stop-color="#ff5d6c" stop-opacity="0"/></radialGradient>
  </defs>
  <rect width="${W}" height="${H}" rx="16" fill="url(#asph)"/>
  <rect x="0" y="0" width="${W}" height="38" fill="url(#solar)" opacity=".9"/>
  <text x="14" y="25" fill="#5f7d99" font-size="11" letter-spacing="3" font-family="Space Grotesk,sans-serif">SOLAR CANOPY · ${NB} × 6 kW CHARGERS</text>
  <rect x="0" y="${QY-44}" width="${W}" height="88" fill="#0f151b"/>
  <line x1="0" y1="${QY-44}" x2="${W}" y2="${QY-44}" stroke="#2a3540" stroke-width="2"/>
  <line x1="0" y1="${QY+44}" x2="${W}" y2="${QY+44}" stroke="#2a3540" stroke-width="2"/>
  <text x="14" y="${QY-50}" fill="#5d6a77" font-size="10" letter-spacing="3" font-family="Space Grotesk,sans-serif">WAITING LANE · FIRST COME, FIRST SERVED →</text>
  ${[...Array(12)].map((_,i)=>`<path d="M${120+i*72} ${QY} l10 0 m-4 -4 l4 4 l-4 4" stroke="#26313b" stroke-width="2" fill="none"/>`).join('')}
  <rect x="0" y="${ROAD_Y-34}" width="${W}" height="68" fill="#161c22"/>
  <line x1="0" y1="${ROAD_Y}" x2="${W}" y2="${ROAD_Y}" stroke="#c9a640" stroke-width="2" stroke-dasharray="18 14" opacity=".55"/>
  <text x="12" y="${ROAD_Y+28}" fill="#5d6a77" font-size="10" letter-spacing="3" font-family="Space Grotesk,sans-serif">ENTRY →</text>
  <text x="${W-12}" y="${ROAD_Y+28}" text-anchor="end" fill="#5d6a77" font-size="10" letter-spacing="3" font-family="Space Grotesk,sans-serif">→ EXIT</text>
  `;
  // trees
  [[W-26,QY-70],[26,QY-70],[W/2,ROAD_Y+46]].forEach(([x,y])=>{S('circle',{cx:x,cy:y,r:11,fill:'#16301d'},svg);S('circle',{cx:x-3,cy:y-3,r:6,fill:'#1f4429'},svg);});
  const bays = [];
  CH.forEach((id,i)=>{
    const x = bayX(i), g = S('g',{},svg);
    S('rect',{x:x,y:50,width:BAY_W,height:230,rx:6,fill:'#0e1419',stroke:'#2a3540','stroke-width':1.5},g);
    S('line',{x1:x,y1:280,x2:x+BAY_W,y2:280,stroke:'#e8edf2','stroke-width':2,opacity:.25,'stroke-dasharray':'8 6'},g);
    const glow = S('ellipse',{cx:x+BAY_W/2,cy:BAY_CY,rx:76,ry:96,fill:'url(#glow)',opacity:0},g);
    const t = S('text',{x:x+BAY_W/2,y:268,'text-anchor':'middle',fill:'#2c3843','font-size':26,'font-weight':700,'font-family':'Space Grotesk,sans-serif'},g); t.textContent=id;
    // pedestal
    S('rect',{x:x+BAY_W/2-30,y:56,width:60,height:46,rx:7,fill:'#1a232c',stroke:'#33414e'},g);
    const screen = S('rect',{x:x+BAY_W/2-25,y:61,width:50,height:24,rx:4,fill:'#05080a'},g);
    const st1 = S('text',{x:x+BAY_W/2,y:71,'text-anchor':'middle','font-size':8.5,'font-weight':700,fill:COL.muted,'font-family':'Space Grotesk,sans-serif'},g);
    const st2 = S('text',{x:x+BAY_W/2,y:81,'text-anchor':'middle','font-size':7.5,fill:COL.muted,'font-family':'Inter,sans-serif'},g);
    const light = S('circle',{cx:x+BAY_W/2,cy:94,r:4,fill:'#2a3540'},g);
    const cable = S('path',{d:`M${x+BAY_W/2+22} 98 C ${x+BAY_W/2+40} 130, ${x+BAY_W/2+30} 150, ${x+BAY_W/2+8} 158`,stroke:COL.lime,'stroke-width':3,fill:'none',opacity:0,'stroke-linecap':'round'},g);
    bays.push({glow,screen,st1,st2,light,cable});
  });
  const carLayer = S('g',{},svg);
  const overflow = S('g',{opacity:0},svg);
  S('rect',{x:6,y:QY-15,width:52,height:30,rx:15,fill:COL.red},overflow);
  const ovT = S('text',{x:32,y:QY+5,'text-anchor':'middle','font-size':13,'font-weight':700,fill:'#07090c','font-family':'Space Grotesk,sans-serif'},overflow);
  return {bays, carLayer, overflow, ovT};
}

function makeCar(c, layer){
  const g = S('g',{opacity:0},layer);
  const tt = S('title',{},g);
  tt.textContent = `${c.id} · ${c.type} · rule: ${c.rule}\narrive ${clock(c.a)} · must leave ${clock(c.d)}\nneeds ${c.req} kWh · got ${c.kwh} kWh\noutcome: ${c.act.replace('_',' ')}`;
  const ring = S('rect',{x:-38,y:-38,width:76,height:76,rx:14,fill:'none',stroke:COL.red,'stroke-width':2.5,'stroke-dasharray':'6 4',class:'pulse',display:'none'},g);
  S('ellipse',{cx:3,cy:5,rx:36,ry:22,fill:'#000',opacity:.55,filter:'url(#sh)'},g);
  const body = S('g',{},g);
  const col = TYPE[c.type] || COL.cyan;
  const paint = S('rect',{x:-33,y:-17,width:66,height:34,rx:11,fill:col},body);
  S('rect',{x:-30,y:-14,width:60,height:28,rx:9,fill:'#fff',opacity:.12},body);
  S('rect',{x:6,y:-13,width:13,height:26,rx:4,fill:'#0b1218',opacity:.85},body);
  S('rect',{x:-25,y:-12,width:9,height:24,rx:3,fill:'#0b1218',opacity:.6},body);
  S('rect',{x:-14,y:-11,width:18,height:22,rx:3,fill:'#000',opacity:.12},body);
  [[-20,-19],[16,-19],[-20,16],[16,16]].forEach(([x,y])=>S('rect',{x:x,y:y,width:11,height:4,rx:2,fill:'#05080a'},body));
  S('circle',{cx:31,cy:-11,r:2,fill:'#fff8d0'},body);S('circle',{cx:31,cy:11,r:2,fill:'#fff8d0'},body);
  const lbl = S('text',{x:0,y:4,'text-anchor':'middle','font-size':10.5,'font-weight':700,fill:'#07090c','font-family':'Space Grotesk,sans-serif'},g);
  lbl.textContent = c.id;
  const batt = S('g',{},g);
  S('rect',{x:-24,y:-52,width:48,height:9,rx:3,fill:'#05080a',stroke:'#33414e'},batt);
  const fill = S('rect',{x:-23,y:-51,width:0,height:7,rx:2,fill:COL.lime},batt);
  const btxt = S('text',{x:0,y:-57,'text-anchor':'middle','font-size':9,fill:'#c6d0da','font-family':'Space Grotesk,sans-serif'},batt);
  const badge = S('g',{opacity:0},g);
  S('rect',{x:-30,y:30,width:60,height:16,rx:8,fill:COL.red},badge);
  const bt = S('text',{x:0,y:41.5,'text-anchor':'middle','font-size':9,'font-weight':700,fill:'#07090c','font-family':'Space Grotesk,sans-serif'},badge);
  return {g, ring, body, paint, fill, btxt, badge, bt, batt, x:ENTRY[0], y:ENTRY[1], ang:0, vis:false};
}

function carState(c, T){
  const leave = c.r != null ? c.r : c.d;
  if (T < c.a) return null;
  if (T >= leave) return T < leave + .8 ? 'leaving' : null;
  if (c.s == null || T < c.s) return 'waiting';
  const ce = c.f != null ? c.f : leave;
  return T < ce ? 'charging' : 'holding';
}
function energy(c, T){
  if (c.s == null || T < c.s) return 0;
  const leave = c.r != null ? c.r : c.d, ce = c.f != null ? c.f : leave;
  return Math.min(c.kwh, KPS*(Math.min(T, ce) - c.s));
}

class Station{
  constructor(sc, root){
    this.sc = sc;
    const el = document.createElement('div'); el.className='station';
    el.innerHTML = `<div class="shead"><div class="stitle">${sc.label}<span>${sc.fee ? 'idle fee '+sc.fee+' pts per slot' : 'no idle fee'}</span></div><div class="chips"></div></div>
      <div class="grid"><div class="svgw"></div><div class="log"><h4>Live event feed</h4><div class="evs"></div></div></div>`;
    root.appendChild(el);
    this.chips = el.querySelector('.chips'); this.evs = el.querySelector('.evs');
    const svg = S('svg',{viewBox:`0 0 ${W} ${H}`}); el.querySelector('.svgw').appendChild(svg);
    Object.assign(this, staticScene(svg));
    this.cars = sc.cars.map(c => ({c, v: makeCar(c, this.carLayer)}));
    this.chipDefs = [['wait','Waiting',COL.amber],['chg','Charging',COL.lime],['idle','Idle hold',COL.red],
                     ['done','Served ✓',COL.cyan],['away','Turned away','#c38bff'],['kwh','kWh given','#e8edf2'],['fees','Fees paid','#e8edf2']];
    this.chips.innerHTML = this.chipDefs.map(([k,l,c])=>`<div class="chip"><div class="v" data-k="${k}" style="color:${c}">0</div><div class="l">${l}</div></div>`).join('');
    this.nEv = -1;
  }
  update(T, dt, snap, speed){
    const st = this.cars.map(o => carState(o.c, T));
    const waiting = this.cars.filter((o,i)=>st[i]==='waiting').sort((a,b)=> a.c.a-b.c.a || (a.c.id<b.c.id?-1:1));
    const qi = new Map(waiting.map((o,i)=>[o,i]));
    const occ = {};
    const stats = {wait:waiting.length, chg:0, idle:0, done:0, away:0, kwh:0, fees:0};
    const k = snap ? 1 : 1 - Math.exp(-dt*6*Math.max(1, speed/0.5));
    this.cars.forEach((o,i)=>{
      const c=o.c, v=o.v, s=st[i];
      const e = energy(c, T); stats.kwh += e;
      const leave = c.r != null ? c.r : c.d;
      if (c.f != null && c.idle) stats.fees += this.sc.fee * Math.max(0, Math.min(T, leave) - c.f);
      if (T >= leave){ if (c.s == null || c.act==='incomplete') stats.away++; else stats.done++; }
      if (!s){ if (v.vis){v.vis=false; v.g.setAttribute('opacity',0);} return; }
      let tx, ty, ta;
      if (s==='waiting'){
        const q = Math.min(qi.get(o), QMAX); tx = QHEAD - q*QGAP; ty = QY; ta = 0;
        if (qi.get(o) >= QMAX) tx = 32;
      } else if (s==='leaving'){
        if (v.y < ROAD_Y - 12){ tx = Math.min(v.x + 60, W - 20); ty = ROAD_Y; } else { tx = EXIT[0]; ty = ROAD_Y; }
        ta = 0;
      } else {
        const bi = CH.indexOf(c.ch); tx = bayX(bi) + BAY_W/2; ty = BAY_CY; ta = -90;
        occ[bi] = {o, s}; if (s==='charging') stats.chg++; else stats.idle++;
      }
      if (!v.vis){ v.vis = true; if (snap){v.x=tx;v.y=ty;v.ang=ta;} else {v.x=ENTRY[0]; v.y=ENTRY[1]; v.ang=0;} }
      v.x += (tx - v.x)*k; v.y += (ty - v.y)*k; v.ang += (ta - v.ang)*k;
      if (s==='leaving' && snap){ v.x = tx; v.y = ty; }
      const op = s==='leaving' ? Math.max(0, 1 - (T-leave)/.8) : 1;
      v.g.setAttribute('opacity', op.toFixed(3));
      v.g.setAttribute('transform', `translate(${v.x.toFixed(1)},${v.y.toFixed(1)})`);
      v.body.setAttribute('transform', `rotate(${v.ang.toFixed(1)})`);
      const dead = s==='leaving' && (c.s == null || c.act==='incomplete');
      v.paint.setAttribute('fill', dead ? COL.dead : (TYPE[c.type]||COL.cyan));
      const frac = Math.max(0, Math.min(1, e / c.req));
      v.fill.setAttribute('width', (46*frac).toFixed(1));
      v.fill.setAttribute('fill', s==='holding' ? COL.red : (frac >= 1 ? COL.cyan : COL.lime));
      v.btxt.textContent = s==='waiting' ? `0/${c.req} kWh` : `${e.toFixed(1).replace('.0','')}/${c.req} kWh`;
      v.batt.setAttribute('opacity', s==='leaving' || s==='waiting' ? 0 : 1);
      const held = s==='holding';
      v.ring.setAttribute('display', held ? 'inline' : 'none');
      v.badge.setAttribute('opacity', held || dead || (s==='waiting' && T - c.a >= 2) ? 1 : 0);
      if (held){ const el = Math.max(0, T - c.f); v.bt.textContent = this.sc.fee ? `IDLE −${(this.sc.fee*el).toFixed(1)}` : 'IDLE'; v.badge.firstChild.setAttribute('fill', COL.red); }
      else if (dead){ v.bt.textContent = c.s==null ? 'GAVE UP' : 'PARTIAL'; v.badge.firstChild.setAttribute('fill', '#c38bff'); }
      else if (s==='waiting'){ v.bt.textContent = `WAIT ${Math.floor(T-c.a)}`; v.badge.firstChild.setAttribute('fill', COL.amber); }
    });
    const over = Math.max(0, waiting.length - QMAX);
    this.overflow.setAttribute('opacity', over ? 1 : 0); this.ovT.textContent = '+'+over;
    this.bays.forEach((b,i)=>{
      const x = occ[i];
      if (!x){ b.st1.textContent='FREE'; b.st1.setAttribute('fill',COL.muted); b.st2.textContent='ready'; b.light.setAttribute('fill','#2a3540');
               b.light.removeAttribute('class'); b.cable.setAttribute('opacity',0); b.glow.setAttribute('opacity',0); return; }
      const c = x.o.c;
      if (x.s==='charging'){
        b.st1.textContent='⚡ 6 kW'; b.st1.setAttribute('fill',COL.lime); b.st2.textContent=c.id;
        b.light.setAttribute('fill',COL.lime); b.light.setAttribute('class','pulse');
        b.cable.setAttribute('opacity',1); b.cable.setAttribute('stroke',COL.lime); b.cable.setAttribute('class','flow');
        b.glow.setAttribute('fill','url(#glow)'); b.glow.setAttribute('opacity',1);
      } else {
        b.st1.textContent='IDLE'; b.st1.setAttribute('fill',COL.red); b.st2.textContent= this.sc.fee ? `fee ${this.sc.fee}/slot` : 'blocking';
        b.light.setAttribute('fill',COL.red); b.light.setAttribute('class','pulse');
        b.cable.setAttribute('opacity',.8); b.cable.setAttribute('stroke',COL.red); b.cable.removeAttribute('class');
        b.glow.setAttribute('fill','url(#rglow)'); b.glow.setAttribute('opacity',1);
      }
    });
    stats.kwh = Math.round(stats.kwh); stats.fees = Math.round(stats.fees*10)/10;
    for (const [kk] of this.chipDefs) this.chips.querySelector(`[data-k="${kk}"]`).textContent = stats[kk];
    const evs = this.sc.events.filter(e => e.t <= T + 1e-6);
    if (evs.length !== this.nEv){
      this.nEv = evs.length;
      this.evs.innerHTML = evs.length ? evs.slice(-9).reverse().map(e=>`<div class="ev ${e.k}">${e.txt}</div>`).join('')
                                      : '<div class="ev">Station opens at 08:00. Press ▶ Play.</div>';
    }
  }
}

const root = document.getElementById('stations');
const stations = DATA.scenarios.map(sc => new Station(sc, root));
let T = 0, playing = false, speed = 0.5, last = null, snapNext = true;
const scrub = document.getElementById('scrub'), playB = document.getElementById('play');
document.getElementById('ticks').innerHTML = [0,2,4,6,8,10,12,14,16].map(t=>`<span>${clock(t)}</span>`).join('');
const sp = document.getElementById('speed');
[[0.25,'¼×'],[0.5,'1×'],[1,'2×'],[2,'4×']].forEach(([v,l])=>{const b=document.createElement('button');b.textContent=l;
  if (v===speed) b.className='on'; b.onclick=()=>{speed=v;[...sp.children].forEach(x=>x.className='');b.className='on';}; sp.appendChild(b);});
function setPlaying(p){ playing = p; playB.textContent = p ? '❚❚ Pause' : '▶ Play'; last = null; }
playB.onclick = () => { if (T >= SL) { T = 0; snapNext = true; } setPlaying(!playing); };
document.getElementById('reset').onclick = () => { T = 0; snapNext = true; setPlaying(false); };
document.getElementById('fwd').onclick = () => { setPlaying(false); T = Math.min(SL, Math.floor(T + 1e-6) + 1); };
document.getElementById('back').onclick = () => { setPlaying(false); T = Math.max(0, Math.ceil(T - 1e-6) - 1); snapNext = true; };
scrub.oninput = () => { T = parseFloat(scrub.value); snapNext = true; setPlaying(false); };
document.addEventListener('keydown', e => { if (e.code === 'Space'){ e.preventDefault(); playB.click(); } });
function frame(ts){
  const dt = last == null ? 0 : Math.min(.1, (ts - last)/1000); last = ts;
  if (playing){ T += dt*speed; if (T >= SL){ T = SL; setPlaying(false); } }
  scrub.value = T;
  document.getElementById('clock').firstChild.nodeValue = clock(Math.min(T, SL));
  document.getElementById('slotlbl').textContent = `day ${DATA.day} · slot ${Math.min(SL, Math.floor(T))} / ${SL}`;
  stations.forEach(s => s.update(T, dt, snapNext, speed));
  snapNext = false;
  requestAnimationFrame(frame);
}
requestAnimationFrame(frame);
</script></body></html>"""
