"""Consolidated files and the report. The page is built from artifact_data.json only."""

from __future__ import annotations

import csv
import json
import statistics
from datetime import datetime
from pathlib import Path
from typing import Any

from rebbi.demo import hill
from rebbi.demo.team import ROLE_TEXT, ROLES

TOY = Path(__file__).resolve().parent.parent.parent / "docs" / "demo" / "preview_toy.html"
SCENARIO_ORDER = ["1", "2", "3", "3-on-B", "3b", "4"]
NAMES = {"1": "Equal fixed budgets", "2": "Manager sets budgets", "3": "Manager + Rebbi",
         "3-on-B": "3-on-B: scenario 3 on Exercise B", "3b": "Rebbi learns (Exercise B)", "4": "Open market"}
RULES = {
    "1": "T/5 tokens each per window. No Rebbi. How most organizations set agent limits today.",
    "2": "A manager agent splits T from the role descriptions, once. No Rebbi.",
    "3": "The manager's budgets, plus a Shareable (% of budget) per agent. An agent that runs short asks Rebbi, "
         "which lends other agents' unused shareable tokens.",
    "3-on-B": "Scenario 3's settings, unchanged, on Exercise B. The fair comparison for 3b.",
    "3b": "On Exercise B. The manager sees per-role usage from scenario 3 of the same repeat and returns new budgets "
          "and shareable %. Compare with 3-on-B, never with scenario 1.",
    "4": "The manager's budgets. Each agent sets its own shareable % every window. Tokens lent earn a claim of "
         "lent x 1.05. An agent at 0% cannot borrow. Debt is limited to one window of the agent's own budget.",
}


def read_results(base: Path) -> list[dict[str, str]]:
    path = base / "results.csv"
    if not path.exists():
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_run(base: Path, row: dict[str, str]) -> dict[str, Any]:
    d = base / row["run_id"]
    return {"run_id": row["run_id"], "scenario": row["scenario"], "scenario_name": NAMES.get(row["scenario"], "Calibration"),
            "exercise": row["exercise"], "repeat": int(row["repeat"]),
            "config": json.loads((d / "config.json").read_text(encoding="utf-8")),
            "summary": json.loads((d / "summary.json").read_text(encoding="utf-8")),
            "windows": read_jsonl(d / "windows.jsonl"), "events": read_jsonl(d / "events.jsonl")}


def counted(row: dict[str, str]) -> bool:
    return row.get("status") == "complete" and row.get("ledger_check") == "PASS"


def artifact(base: Path, config: dict[str, Any], scripted: bool) -> dict[str, Any]:
    rows = [r for r in read_results(base) if counted(r)]
    runs = [load_run(base, r) for r in rows]
    cal = next((r for r in runs if r["scenario"] == "cal"), None)
    cal_conf = config.get("calibration", {})
    return {
        "title": "Rebbi Demo",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "scripted": scripted,
        "measured_on": "scripted stand-in model, zero plan usage" if scripted else "Claude Pro in subscription mode",
        "setup": {
            "models": sorted({m for r in runs for m in r["config"]["models"].values()}),
            "coder_model": config.get("coder_model"),
            "tokens_per_window_T": cal_conf.get("T"),
            "summit_exercise_A_score": cal_conf.get("target_A", cal_conf.get("summit_A")),
            "summit_exercise_B_score": cal_conf.get("target_B", cal_conf.get("summit_B")),
            "scipy_forbidden": config.get("forbid_scipy", False),
            "windows_cap": 20,
            "roles": [{"id": r, "description": ROLE_TEXT[r]} for r in ROLES],
            "exercises": {k: {"circles": n, "published_best_known": hill.REFERENCE[k]} for k, n in hill.EXERCISES.items()},
            "calibration_notes": cal_conf.get("notes", []),
            "frozen_manager": config.get("manager"),
            "frozen_learned": config.get("learned"),
        },
        "calibration": cal,
        "runs": [r for r in runs if r["scenario"] != "cal"],
        "results_table": rows,
    }


def table_md(rows: list[dict[str, str]]) -> str:
    cols = ["run_id", "scenario", "exercise", "repeat", "windows_to_summit", "best_score", "tokens_used",
            "tokens_expired", "interruptions", "loans_count", "tokens_moved", "ledger_check", "status"]
    out = ["| " + " | ".join(cols) + " |", "|" + " --- |" * len(cols)]
    out += ["| " + " | ".join(r.get(c, "") for c in cols) + " |" for r in rows]
    return "\n".join(out) + "\n"


def build_all(ctx) -> None:
    from rebbi.demo.runner import load_config
    base = ctx.base
    base.mkdir(parents=True, exist_ok=True)
    rows = read_results(base)
    (base / "table.md").write_text(table_md(rows), encoding="utf-8")
    data = artifact(base, load_config(ctx), ctx.rehearsal)
    (base / "artifact_data.json").write_text(json.dumps(data, indent=1), encoding="utf-8")
    build_html(data, ctx.report_path)


def build_html(data: dict[str, Any], out: Path) -> None:
    css = ""
    if TOY.exists():
        text = TOY.read_text(encoding="utf-8", errors="replace")
        css = text[text.index("<style>") + 7:text.index("</style>")]
    payload = json.dumps(data).replace("</", "<\\/")
    html = TEMPLATE.replace("__CSS__", css).replace("__DATA__", payload)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")


def median_range(vals: list[float]) -> tuple[float, float, float] | None:
    return (statistics.median(vals), min(vals), max(vals)) if vals else None


TEMPLATE = r"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Rebbi Demo</title>
<style>
__CSS__
.banner{background:var(--rebbi-soft);color:var(--fg);border-radius:var(--r);padding:12px 16px;font-size:14px}
.banner b{font-weight:600}
.packbox{width:100%;max-width:300px;aspect-ratio:1;background:var(--sunk);border:1px solid var(--line)}
.range{width:100%}
.notrun{color:var(--muted);font-style:italic}
ul.lim{margin:0;padding-left:18px;display:flex;flex-direction:column;gap:4px;font-size:13.5px;color:var(--muted)}
</style></head><body>
<div class="wrap">
<header>
  <div class="eyebrow">MAS.665 AI Studio, Rebbi, measured results</div>
  <h1>Rebbi Demo</h1>
  <p class="lede">Five agents climb the same circle-packing hill under five budget regimes. Every regime issues the same tokens per window. We count windows to the summit, tokens that expire unused, interruptions, and tokens Rebbi moves.</p>
  <div id="scripted" class="notice" hidden><b>Scripted rehearsal.</b> The model is a stand-in, not Claude. These numbers are not evidence.</div>
  <div class="banner" id="banner"></div>
</header>

<section><div class="sechead"><div class="eyebrow">What stays fixed</div><h2>The test bench</h2></div>
  <div class="setup" id="setup"></div></section>

<section><div class="sechead"><div class="eyebrow">Replay of recorded windows</div><h2>Pick a scenario</h2></div>
  <div class="tabs" role="tablist" id="tabs"></div>
  <div class="rules"><div class="txt"><div class="eyebrow" id="r-eyebrow"></div><h3 id="r-title"></h3><p id="r-desc"></p>
    <div class="controls"><span class="muted" id="repeat-label"></span><div class="seg" id="repeats"></div></div></div>
    <div class="scroll-x"><table class="btab" id="btab"></table></div></div>
  <div class="controls"><button class="btn primary" id="play" type="button">Play</button>
    <input class="range" type="range" id="slider" min="1" max="1" value="1" aria-label="Window" style="max-width:420px">
    <span class="seedtag" id="wlabel"></span></div>
  <div class="sim">
    <div class="panel"><div class="panel-h"><h3>The climb</h3><span class="eyebrow" id="phase"></span></div>
      <svg class="hillsvg" id="hill" viewBox="0 0 600 320" role="img" aria-label="Best score by window"></svg>
      <div class="tiles" id="tiles"></div>
      <div class="panel-h"><h3>Best packing so far</h3><span class="eyebrow" id="packtag"></span></div>
      <svg class="packbox" id="pack" viewBox="0 0 100 100"></svg>
      <div class="panel-h"><h3>Event log</h3><span class="eyebrow">newest first</span></div>
      <div class="log" id="log"></div></div>
    <div class="panel"><div class="panel-h"><h3>Token flow this window</h3><span class="eyebrow" id="flowtag"></span></div>
      <svg class="routesvg" id="route" viewBox="0 0 400 290"></svg>
      <div class="panel-h"><h3>Budget bars this window</h3><span class="eyebrow">k tokens</span></div>
      <div class="lanes" id="lanes"></div>
      <div class="legend"><span><i class="seg-used"></i>used</span><span><i class="seg-lent"></i>lent out</span>
        <span><i class="seg-exp" style="border:1px solid var(--line)"></i>expired</span><span><i class="seg-unmet"></i>needed, not covered</span>
        <span><i style="width:2px;background:var(--fg)"></i>budget</span><span><i style="width:0;border-left:2px dotted var(--rebbi);border-radius:0"></i>dotted: shareable part is to its right</span></div></div>
  </div></section>

<section><div class="sechead"><div class="eyebrow">Side by side</div><h2>The race</h2>
  <p class="lede">Best score after each window, median over repeats. Scenario 3b runs Exercise B, so its fair comparison is the dashed 3-on-B line.</p></div>
  <div class="race"><div class="panel"><svg class="racesvg" id="race" viewBox="0 0 640 330"></svg></div>
    <div class="panel"><h3>Results</h3><div class="scroll-x"><table class="rtab" id="rtab"></table></div></div></div></section>

<section><div class="sechead"><div class="eyebrow">Read before quoting</div><h2>Limitations</h2></div>
  <ul class="lim" id="lim"></ul></section>
<footer id="foot"></footer>
</div>
<script>
const D=__DATA__;
const SC=['1','2','3','3-on-B','3b','4'];
const NAME={'1':'Equal fixed budgets','2':'Manager sets budgets','3':'Manager + Rebbi','3-on-B':'3-on-B','3b':'Rebbi learns (B)','4':'Open market'};
const TAB={'1':'1','2':'2','3':'3','3-on-B':'3B','3b':'3b','4':'4'};
const COL={'1':'--s1','2':'--s2','3':'--s3','3-on-B':'--s3','3b':'--s3b','4':'--s4'};
const RULE={'1':'T/5 tokens each per window. No Rebbi. How most organizations set agent limits today.','2':'A manager agent splits T from the role descriptions, once. No Rebbi.','3':"The manager's budgets plus a Shareable (% of budget) per agent. An agent that runs short asks Rebbi, which lends other agents' unused shareable tokens.",'3-on-B':"Scenario 3's settings, unchanged, on Exercise B. The fair comparison for 3b.",'3b':'On Exercise B. The manager sees per-role usage from scenario 3 of the same repeat and returns new budgets and shareable %. Compare with 3-on-B.','4':"The manager's budgets. Each agent sets its own shareable % each window. Tokens lent earn a claim of lent x 1.05; an agent at 0% cannot borrow; debt is limited to one window of its own budget."};
const ROLES=D.setup.roles.map(r=>r.id);
const $=id=>document.getElementById(id);
const el=(t,a,h)=>{const e=document.createElement(t);for(const k in a||{})e.setAttribute(k,a[k]);if(h!=null)e.innerHTML=h;return e};
const ns='http://www.w3.org/2000/svg';
const sv=(t,a,h)=>{const e=document.createElementNS(ns,t);for(const k in a||{})e.setAttribute(k,a[k]);if(h!=null)e.textContent=h;return e};
const fk=n=>n==null?'n/a':(Math.abs(n)>=1000?(n/1000).toFixed(Math.abs(n)>=10000?0:1)+'k':String(Math.round(n)));
const f3=n=>n==null?'n/a':Number(n).toFixed(3);
const med=a=>{if(!a.length)return null;const s=[...a].sort((x,y)=>x-y),m=s.length>>1;return s.length%2?s[m]:(s[m-1]+s[m])/2};
const runs=sc=>D.runs.filter(r=>r.scenario===sc).sort((a,b)=>a.repeat-b.repeat);
const cnt=sc=>runs(sc).length;
let sc=SC.find(s=>cnt(s))||'1', rep=null, win=1, timer=null;
const cur=()=>{const rs=runs(sc);return rs.find(r=>r.repeat===rep)||rs[0]||null};

function banner(){
  const per=SC.map(s=>`${s}: ${cnt(s)}`).join(', ');
  const dates=D.runs.map(r=>r.summary.started_at).concat(D.runs.map(r=>r.summary.ended_at)).sort();
  $('banner').innerHTML=`<b>Complete runs per scenario:</b> ${per}. <b>Models:</b> ${D.setup.models.join(', ')||'none yet'}. <b>Exercises:</b> A (26 circles), B (32 circles). <b>Dates:</b> ${dates.length?dates[0].slice(0,10)+' to '+dates[dates.length-1].slice(0,10):'no run yet'}. <b>Measured on ${D.measured_on}.</b>`;
  $('scripted').hidden=!D.scripted;
}
function setup(){
  const s=D.setup,ex=s.exercises;
  const refA=ex.A.published_best_known.map(r=>r.value).join(' / '),refB=ex.B.published_best_known.map(r=>r.value).join(' / ');
  $('setup').innerHTML=`<div><span class="k">The hill</span><h3>Circle packing</h3><p>Place n disjoint circles in the unit square to maximize the sum of radii. <strong>Exercise A: n = 26. Exercise B: n = 32.</strong> Published best-known: ${refA} (A), ${refB} (B); these are not our results.</p></div>
  <div><span class="k">The team</span><h3>Five roles, fresh memory</h3><p><strong>Planner, Researcher, Coder, Evaluator, Reviewer.</strong> Coder model: ${s.coder_model||'n/a'}. Each run starts with empty agent memory.</p></div>
  <div><span class="k">The clock</span><h3>Budget windows</h3><p>One window is one round of five turns. <strong>Unused tokens expire at the refill.</strong> The org issues T = ${fk(s.tokens_per_window_T)} tokens per window in every scenario, up to ${s.windows_cap} windows.</p></div>
  <div><span class="k">The summit</span><h3>From calibration</h3><p>Exercise A summit: <strong>${f3(s.summit_exercise_A_score)}</strong>. Exercise B summit: <strong>${f3(s.summit_exercise_B_score)}</strong> (same relative height).${s.scipy_forbidden?' scipy forbidden (flat-hill guard).':''}</p></div>`;
}
function tabs(){
  const t=$('tabs');t.innerHTML='';
  SC.forEach(s=>{const b=el('button',{class:'tab',role:'tab','aria-selected':String(s===sc),style:`--c:var(${COL[s]})`},`<span class="n">${TAB[s]}</span>${NAME[s]}${cnt(s)?'':' (not run)'}`);
    b.onclick=()=>{sc=s;rep=null;win=1;stop();draw()};t.appendChild(b)});
}
function rules(){
  $('r-eyebrow').textContent='Scenario '+TAB[sc];$('r-title').textContent=NAME[sc];$('r-desc').textContent=RULE[sc];
  const rs=runs(sc),r=cur();const rp=$('repeats');rp.innerHTML='';
  $('repeat-label').textContent=rs.length>1?'Repeat:':'';
  if(rs.length>1)rs.forEach(x=>{const b=el('button',{type:'button','aria-pressed':String(x===r)},String(x.repeat));b.onclick=()=>{rep=x.repeat;win=1;draw()};rp.appendChild(b)});
  const bt=$('btab');
  if(!r){bt.innerHTML='<tr><td class="notrun">not run</td></tr>';return}
  const c=r.config,ws=r.windows;
  let h='<tr><th>Agent</th><th>Budget / window</th><th>Shareable (% of budget)</th><th>Avg new work / window</th></tr>';
  ROLES.forEach(a=>{const b=c.budgets[a];const sh=(c.rebbi&&!c.market)?c.shareable_pct[a]:null;
    const work=ws.length?ws.reduce((s,w)=>s+w.agents[a].used+w.agents[a].unmet,0)/ws.length:null;
    const shTxt=c.market?'set by agent':(sh==null?'n/a':`${Math.round(sh)}% · ${fk(b*sh/100)}`);
    h+=`<tr><td>${a}</td><td>${fk(b)}</td><td>${shTxt}</td><td class="${work>b?'over':'under'}">${fk(work)}</td></tr>`});
  bt.innerHTML=h;
}
function hill(){
  const svg=$('hill');svg.innerHTML='';const r=cur();if(!r){svg.appendChild(sv('text',{x:20,y:40,fill:'currentColor'},'not run'));return}
  const ws=r.windows,ex=r.exercise,refs=D.setup.exercises[ex].published_best_known;
  const top=Math.max(...refs.map(x=>x.value),...ws.map(w=>w.team.best_score),r.config.summit||0)*1.05;
  const X=i=>40+(i-1)*(540/Math.max(ws.length-1,1)),Y=v=>290-v/top*270;
  const line=(y,cls,label,dash)=>{svg.appendChild(sv('line',{x1:40,x2:580,y1:Y(y),y2:Y(y),stroke:`var(${cls})`,'stroke-dasharray':dash||'','stroke-width':1.5}));svg.appendChild(sv('text',{x:582,y:Y(y)+4,'font-size':9,fill:'currentColor'},label))};
  if(r.config.summit)line(r.config.summit,'--ok','summit '+f3(r.config.summit));
  refs.forEach(x=>line(x.value,'--ref',x.value+' best-known (published)','4 4'));
  svg.appendChild(sv('polyline',{points:ws.slice(0,win).map((w,i)=>`${X(i+1)},${Y(w.team.best_score)}`).join(' '),fill:'none',stroke:`var(${COL[r.scenario]||'--s3'})`,'stroke-width':2.5}));
  ws.slice(0,win).forEach((w,i)=>{svg.appendChild(sv('circle',{cx:X(i+1),cy:Y(w.team.candidate_score),r:2.5,fill:'var(--muted)'}))});
  // milestone flags: first window at or above 25%, 50%, 75%, 100% of the summit
  const sm=r.config.summit;if(sm)[.25,.5,.75,1].forEach(f=>{const i=ws.findIndex(w=>w.team.best_score>=f*sm);if(i>=0&&i<win){svg.appendChild(sv('line',{x1:X(i+1),x2:X(i+1),y1:Y(ws[i].team.best_score),y2:Y(ws[i].team.best_score)-24,stroke:'var(--fg)'}));svg.appendChild(sv('text',{x:X(i+1)+3,y:Y(ws[i].team.best_score)-26,'font-size':9,fill:'currentColor'},Math.round(f*100)+'% of summit'))}});
  svg.appendChild(sv('text',{x:300,y:314,'font-size':10,'text-anchor':'middle',fill:'currentColor'},'window'));
  svg.appendChild(sv('text',{x:6,y:14,'font-size':10,fill:'currentColor'},'sum of radii'));
}
function tiles(){
  const r=cur(),t=$('tiles');if(!r){t.innerHTML='';return}
  const ws=r.windows.slice(0,win),sum=(f)=>ws.reduce((s,w)=>s+f(w),0);
  const exp=sum(w=>Object.values(w.agents).reduce((s,a)=>s+a.expired,0)),used=sum(w=>w.team.tokens_used),intr=sum(w=>Object.values(w.agents).filter(a=>a.interrupted).length);
  const loans=r.events.filter(e=>e.kind==='loan'&&e.decision==='LEND'&&e.window<=win);
  const issued=r.config.scenario==='cal'?null:r.config.T*ws.length;
  const w=r.windows[win-1];
  t.innerHTML=[['Window',win,'of '+r.windows.length+' run'],['Best score',f3(w.team.best_score),'candidate '+f3(w.team.candidate_score)],['Tokens expired',fk(exp),issued?Math.round(100*exp/issued)+'% of issued':''],['Interruptions',intr,'agent-windows'],['Moved by Rebbi',fk(loans.reduce((s,e)=>s+e.tokens,0)),loans.length+' loans']].map(x=>`<div class="tile"><span class="l">${x[0]}</span><span class="v">${x[1]}</span><span class="s">${x[2]}</span></div>`).join('');
  $('phase').textContent='candidate: '+w.team.candidate_reason+(w.team.accepted?' (accepted)':'');
}
function pack(){
  const svg=$('pack');svg.innerHTML='';const r=cur();if(!r)return;const w=r.windows[win-1],p=w.team.best_packing;
  svg.appendChild(sv('rect',{x:0,y:0,width:100,height:100,fill:'none',stroke:'var(--line)'}));
  if(p&&p.centers)p.centers.forEach((c,i)=>svg.appendChild(sv('circle',{cx:c[0]*100,cy:100-c[1]*100,r:p.radii[i]*100,fill:'var(--rebbi-soft)',stroke:'var(--rebbi)','stroke-width':.4})));
  $('packtag').textContent='sum of radii '+f3(w.team.best_score);
}
function logv(){
  const r=cur(),l=$('log');l.innerHTML='';if(!r)return;
  const rows=r.events.filter(e=>e.window<=win&&e.kind!=='settle').slice().reverse().slice(0,60);
  rows.forEach(e=>{let cls='',txt='';
    if(e.kind==='loan'){cls=e.decision==='LEND'?'e-loan':'e-blk';txt=e.decision==='LEND'?`<b>${e.borrower}</b> borrowed ${fk(e.tokens)} from ${e.lender}${e.partial?' (partial: '+e.limit_reason+')':''}`:`<b>${e.borrower}</b> asked Rebbi for ${fk(e.asked)}: CANNOT_MOVE ${e.blocker||''}`}
    else if(e.kind==='interruption'){cls='e-blk';txt=`<b>${e.agent}</b> interrupted: needed ${fk(e.needed)}, had ${fk(e.balance)}`}
    else if(e.kind==='acceptance'){cls='e-ms';txt=`candidate accepted, best ${f3(e.score)}`}
    l.appendChild(el('div',{class:cls},`<span>w${e.window}</span><span>${txt}</span>`))});
  if(!rows.length)l.innerHTML='<div><span></span><span class="notrun">no events yet</span></div>';
}
function route(){
  const svg=$('route');svg.innerHTML='';const r=cur();if(!r)return;
  const pos={};ROLES.forEach((a,i)=>{const t=-Math.PI/2+i*2*Math.PI/ROLES.length;pos[a]=[200+110*Math.cos(t),145+100*Math.sin(t)]});
  const ev=r.events.filter(e=>e.kind==='loan'&&e.decision==='LEND'&&e.window===win);
  $('flowtag').textContent=ev.length?ev.length+' loans':'no loans';
  ev.forEach(e=>{const a=pos[e.lender],b=pos[e.borrower];svg.appendChild(sv('line',{x1:a[0],y1:a[1],x2:b[0],y2:b[1],stroke:'var(--rebbi)','stroke-width':1+Math.min(5,e.tokens/20000)}));svg.appendChild(sv('text',{x:(a[0]+b[0])/2,y:(a[1]+b[1])/2,'font-size':9,fill:'var(--rebbi)','text-anchor':'middle'},fk(e.tokens)))});
  ROLES.forEach(a=>{const p=pos[a];svg.appendChild(sv('circle',{cx:p[0],cy:p[1],r:22,fill:'var(--surface)',stroke:'var(--fg)'}));svg.appendChild(sv('text',{x:p[0],y:p[1]+3,'font-size':9,'text-anchor':'middle',fill:'currentColor'},a.slice(0,9)))});
}
function lanes(){
  const r=cur(),l=$('lanes');l.innerHTML='';if(!r)return;const w=r.windows[win-1];
  const mx=Math.max(...ROLES.map(a=>w.agents[a].budget+w.agents[a].borrowed+w.agents[a].unmet));
  ROLES.forEach(a=>{const s=w.agents[a],P=v=>(100*v/mx)+'%';let x=0;
    const seg=(cls,v)=>{const h=`<i class="${cls}" style="left:${P(x)};width:${P(v)}"></i>`;x+=v;return h};
    let bar=seg('seg-used',s.used)+seg('seg-lent',Math.min(s.lent,s.budget))+seg('seg-exp',s.expired)+seg('seg-unmet',s.unmet);
    bar+=`<span class="bline" style="left:${P(s.budget)}"></span>`;
    if(r.config.rebbi)bar+=`<span class="afsline" style="left:${P(s.reserve)}"></span>`;
    l.appendChild(el('div',{class:'lane'},`<div class="who"><b>${a}</b><span>${s.interrupted?'<span class="chip blk">interrupted</span>':''}${s.borrowed?'<span class="chip bor">borrowed '+fk(s.borrowed)+'</span>':''}${s.lent?'<span class="chip lend">lent '+fk(s.lent)+'</span>':''}</span></div><div class="bar">${bar}</div><div class="num">${fk(s.used)} / ${fk(s.budget)}${s.claim_balance!=null?'<br>claim '+fk(s.claim_balance):''}</div>`))});
}
function carry(r,k){const ws=r.windows;return ws[Math.min(k,ws.length)-1].team.best_score}
function race(){
  const svg=$('race');svg.innerHTML='';const all=D.runs;if(!all.length){svg.appendChild(sv('text',{x:20,y:40,fill:'currentColor'},'not run'));return}
  const W=Math.max(...all.map(r=>r.windows.length)),top=Math.max(...all.map(r=>Math.max(...r.windows.map(w=>w.team.best_score))))*1.1;
  const X=k=>40+(k-1)*(580/Math.max(W-1,1)),Y=v=>300-v/top*270;
  SC.forEach(s=>{const rs=runs(s);if(!rs.length)return;const pts=[];for(let k=1;k<=W;k++){const v=med(rs.map(r=>carry(r,k)));pts.push(`${X(k)},${Y(v)}`)}
    svg.appendChild(sv('polyline',{points:pts.join(' '),fill:'none',stroke:`var(${COL[s]})`,'stroke-width':2.2,'stroke-dasharray':s==='3-on-B'?'6 4':''}));
    svg.appendChild(sv('text',{x:622,y:Y(med(rs.map(r=>carry(r,W))))+3,'font-size':9,fill:`var(${COL[s]})`},TAB[s]))});
  svg.appendChild(sv('text',{x:320,y:324,'font-size':10,'text-anchor':'middle',fill:'currentColor'},'window'));
}
function results(){
  const rng=a=>a.length>1?` (${f3(Math.min(...a))} to ${f3(Math.max(...a))})`:'';
  const rngI=a=>a.length>1?` (${Math.min(...a)} to ${Math.max(...a)})`:'';
  let h='<tr><th>Scenario</th><th>Runs</th><th>Windows to summit</th><th>Best score</th><th>Expired (% of issued)</th><th>Interruptions</th><th>Moved by Rebbi</th></tr>';
  SC.forEach(s=>{const rs=runs(s);const n=`<span class="sw" style="--c:var(${COL[s]})"></span>${NAME[s]}`;
    if(!rs.length){h+=`<tr><td>${n}</td><td colspan="6" class="notrun">not run</td></tr>`;return}
    const wts=rs.map(r=>r.summary.windows_to_summit).filter(v=>typeof v==='number'),sc2=rs.map(r=>r.summary.best_score);
    const ex=rs.map(r=>100*r.summary.tokens_expired/r.summary.tokens_issued),ints=rs.map(r=>r.summary.interruptions),mv=rs.map(r=>r.summary.tokens_moved);
    h+=`<tr><td>${n}</td><td class="n">${rs.length}</td><td class="n">${wts.length?med(wts)+rngI(wts)+(wts.length<rs.length?', '+(rs.length-wts.length)+' not reached':''):'not reached'}</td><td class="n">${f3(med(sc2))}${rng(sc2)}</td><td class="n">${med(ex).toFixed(0)}%</td><td class="n">${med(ints)}${rngI(ints)}</td><td class="n">${fk(med(mv))}</td></tr>`});
  if(D.calibration){const c=D.calibration.summary;h+=`<tr class="ref"><td>Calibration (not a scenario)</td><td class="n">1</td><td class="n">n/a</td><td class="n">${f3(c.best_score)}</td><td class="n">n/a</td><td class="n">${c.interruptions}</td><td class="n">n/a</td></tr>`}
  $('rtab').innerHTML=h;
}
function limits(){
  const n=Math.max(...SC.map(cnt),0);
  $('lim').innerHTML=[`${n<=1?'Most scenarios have one run, so a difference may be noise.':'Repeats vary; the median and range are shown.'}`,
   'Token counts include input, cache writes, cache reads and output, as the harness meters them from the stream. Plan usage is not the same as API cost.',
   'The Evaluator and Reviewer agents write short reports; the harness applies the rule that accepts a candidate (valid and better) and requires both agents to have run that window.',
   'The 3b result is compared with 3-on-B only. Published best-known values are other teams\' results, shown for scale.',
   'Agents have no tools; the harness asks Rebbi for a loan on their behalf when a call would not fit their balance.',
   'Missing cells say "not run".'].map(t=>`<li>${t}</li>`).join('');
  $('foot').textContent='Generated '+D.generated_at+' from artifact_data.json. Every number comes from a completed run.';
}
function stop(){if(timer){clearInterval(timer);timer=null}$('play').textContent='Play'}
$('play').onclick=()=>{if(timer){stop();return}const r=cur();if(!r)return;if(win>=r.windows.length)win=1;$('play').textContent='Pause';timer=setInterval(()=>{if(win>=r.windows.length){stop();return}win++;draw()},900);draw()};
$('slider').oninput=e=>{win=+e.target.value;draw()};
function draw(){
  const r=cur();tabs();rules();$('slider').max=r?r.windows.length:1;$('slider').value=win;$('wlabel').textContent=r?`window ${win} of ${r.windows.length}`:'not run';
  hill();if(r){tiles();pack();logv();route();lanes()}else{['tiles','log','lanes'].forEach(i=>$(i).innerHTML='');$('route').innerHTML='';$('pack').innerHTML=''}
}
banner();setup();draw();race();results();limits();
</script></body></html>
"""
