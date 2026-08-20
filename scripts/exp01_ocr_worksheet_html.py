#!/usr/bin/env python3
"""Render the OCR token inventory as a local, self-contained review page.

Reads worksheet.json produced by exp01_ocr_token_inventory.py and emits a single
HTML file with no external assets, so it opens straight from disk and works with
networking off. This keeps reviewer evidence on the workstation, consistent with
ADR-001 local-first.

Progress is saved in the browser's local storage. Export writes a JSON file whose
rows carry reviewer_verdict, ready to be read back.

Applies no correctness judgment and runs no second observer. It only presents the
inventory for a human to compare against the rendered originals.

Output goes under evaluation/runs/ which is gitignored. Do not commit its output.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

PAGE = """<!doctype html>
<meta charset="utf-8">
<title>OCR token review</title>
<style>
:root{--bg:#faf9f7;--fg:#1a1a1a;--mut:#6b6b6b;--line:#e0ddd8;--card:#fff;
--ok:#1f7a4d;--okbg:#e6f4ec;--bad:#b3261e;--badbg:#fbeae9;--unk:#8a6d1f;--unkbg:#fdf4e0;--acc:#2a5db0;}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);
font:16px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;}
header{background:var(--card);border-bottom:1px solid var(--line);padding:14px 28px;}
h1{margin:0 0 6px;font-size:20px;}
.sub{color:var(--mut);font-size:14px;max-width:70ch;}
.wrap{max-width:1000px;margin:0 auto;padding:14px 28px 80px;}
.note{background:#fff8e6;border:1px solid #eadfb8;border-radius:8px;padding:0 16px;
margin:10px 0;font-size:14px;line-height:1.6;}
.note[open]{padding:0 16px 14px;}
.note summary{cursor:pointer;padding:11px 0;font-weight:600;color:#7a5c00;list-style:none;}
.note summary::-webkit-details-marker{display:none}
.note summary::before{content:"▸  ";}
.note[open] summary::before{content:"▾  ";}
.note b{color:#7a5c00;}
.pages{display:flex;flex-wrap:wrap;gap:8px;margin:20px 0 8px;}
.pg{border:1px solid var(--line);background:var(--card);border-radius:8px;padding:8px 12px;
cursor:pointer;font-size:14px;min-width:74px;text-align:center;}
.pg:hover{border-color:var(--acc);}
.pg.active{background:var(--acc);color:#fff;border-color:var(--acc);}
.pg .n{display:block;font-size:11px;opacity:.75;margin-top:2px;}
.pg.done{border-color:var(--ok);}
.pg.done .n{color:var(--ok);}
.pg.active.done .n{color:#d6f2e2;}
.bar{height:8px;background:var(--line);border-radius:99px;overflow:hidden;margin:14px 0 4px;}
.bar>i{display:block;height:100%;background:var(--ok);width:0;transition:width .2s;}
.tot{font-size:13px;color:var(--mut);margin-bottom:18px;}
table{width:100%;border-collapse:collapse;background:var(--card);
border:1px solid var(--line);border-radius:10px;overflow:hidden;}
th,td{padding:11px 12px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top;}
th{background:#f4f2ee;font-size:12px;text-transform:uppercase;letter-spacing:.05em;color:var(--mut);}
tr:last-child td{border-bottom:none}
td.ln{color:var(--mut);font-size:13px;width:52px;white-space:nowrap;}
code{font:15px/1.4 ui-monospace,SFMono-Regular,Menlo,monospace;background:#f0eeea;
padding:2px 7px;border-radius:5px;border:1px solid var(--line);}
.ctx{color:var(--mut);font-size:12.5px;margin-top:5px;font-family:ui-monospace,Menlo,monospace;
white-space:pre-wrap;word-break:break-word;}
.btns{display:flex;gap:6px;}
button.v{border:1px solid var(--line);background:var(--card);border-radius:7px;
padding:6px 11px;cursor:pointer;font-size:13px;white-space:nowrap;}
button.v:hover{border-color:var(--acc)}
tr.f button.v[data-v=faithful]{background:var(--okbg);border-color:var(--ok);color:var(--ok);font-weight:600}
tr.s button.v[data-v=substitution]{background:var(--badbg);border-color:var(--bad);color:var(--bad);font-weight:600}
tr.u button.v[data-v=unreadable_in_original]{background:var(--unkbg);border-color:var(--unk);color:var(--unk);font-weight:600}
tr.s code{background:var(--badbg);border-color:var(--bad);}
.foot{position:fixed;left:0;right:0;bottom:0;background:var(--card);
border-top:1px solid var(--line);padding:12px 28px;display:flex;gap:12px;align-items:center;}
.foot .sp{flex:1;font-size:13px;color:var(--mut);}
button.go{background:var(--acc);color:#fff;border:none;border-radius:8px;
padding:10px 18px;font-size:14px;cursor:pointer;}
button.gh{background:transparent;color:var(--acc);border:1px solid var(--acc);}
</style>
<header>
<h1>OCR token review — RMC 77-2024 (scanned)</h1>
<div class="sub">Open the <b>scanned PDF</b> at the page selected below, find each number on the page, and compare it with the grey box in the middle column. Then click a verdict button on the right. Keyboard: <b>1</b> faithful,
<b>2</b> substitution, <b>3</b> unreadable. Your progress saves automatically in this browser.</div>
</header>
<div class="wrap">
<details class="note">
<summary>Before you start — three things to know</summary>
<b>This is an inventory, not a list of findings.</b> Nothing below is claimed to be wrong.
You are establishing how often OCR misread a number — the answer may well be zero beyond the
one already known.<br><br>
<b>Do not skip rows.</b> The "in a gold fact" column is <i>not</i> a priority filter — a
misread number can never match, so real errors systematically show blank there.<br><br>
<b>This measures misreadings only.</b> A number the computer dropped entirely leaves no row
here and cannot be found this way.
</details>
<div class="bar"><i id="pb"></i></div>
<div class="tot" id="tot"></div>
<div class="pages" id="pgs"></div>
<table><thead><tr><th>Line</th><th>What the computer read &mdash; compare this to the PDF</th><th>In a gold fact</th><th>Record your verdict here</th></tr></thead><tbody id="rows"></tbody></table>
</div>
<div class="foot">
<div class="sp" id="status"></div>
<button class="go gh" id="clear">Reset all</button>
<button class="go" id="exp">Export results</button>
</div>
<script>
const DATA = __DATA__;
const KEY = "kendra-ocr-review:" + DATA.run_id;
let verdicts = JSON.parse(localStorage.getItem(KEY) || "{}");
const rows = DATA.rows.map((r,i)=>({...r,_i:i}));
const pages = [...new Set(rows.map(r=>r.physical_page))].sort((a,b)=>a-b);
let cur = pages[0];
const save=()=>localStorage.setItem(KEY,JSON.stringify(verdicts));
const cls={faithful:"f",substitution:"s",unreadable_in_original:"u"};

function paint(){
  const done=Object.keys(verdicts).length, tot=rows.length;
  document.getElementById("pb").style.width=(100*done/tot)+"%";
  document.getElementById("tot").textContent=done+" of "+tot+" reviewed"+
    (done===tot?" — complete, export below.":"");
  const pc=document.getElementById("pgs"); pc.innerHTML="";
  pages.forEach(p=>{
    const rs=rows.filter(r=>r.physical_page===p);
    const d=rs.filter(r=>verdicts[r._i]).length;
    const b=document.createElement("div");
    b.className="pg"+(p===cur?" active":"")+(d===rs.length?" done":"");
    b.innerHTML="Page "+p+"<span class='n'>"+d+"/"+rs.length+"</span>";
    b.onclick=()=>{cur=p;paint();};
    pc.appendChild(b);
  });
  const tb=document.getElementById("rows"); tb.innerHTML="";
  rows.filter(r=>r.physical_page===cur).forEach(r=>{
    const tr=document.createElement("tr");
    const v=verdicts[r._i]; if(v) tr.className=cls[v];
    tr.innerHTML="<td class='ln'>"+r.line+"</td>"+
      "<td><code>"+esc(r.surface_form)+"</code><div class='ctx'>"+esc(r.line_context)+"</div></td>"+
      "<td>"+(r.asserted_by_a_gold_fact?"yes":"")+"</td>"+
      "<td><div class='btns'>"+
      "<button class='v' data-v='faithful'>Faithful</button>"+
      "<button class='v' data-v='substitution'>Misread</button>"+
      "<button class='v' data-v='unreadable_in_original'>Unreadable</button></div></td>";
    tr.querySelectorAll("button.v").forEach(b=>b.onclick=()=>{
      const val=b.dataset.v;
      if(verdicts[r._i]===val) delete verdicts[r._i]; else verdicts[r._i]=val;
      save();paint();
    });
    tb.appendChild(tr);
  });
  document.getElementById("status").textContent="Page "+cur+" of this 12-page scan.";
}
function esc(s){return String(s).replace(/[&<>]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;"}[c]));}
document.getElementById("exp").onclick=()=>{
  const out={...DATA, exported_at:new Date().toISOString(),
    rows:DATA.rows.map((r,i)=>({...r,reviewer_verdict:verdicts[i]||""})),
    review_summary:{reviewed:Object.keys(verdicts).length,total:DATA.rows.length,
      faithful:Object.values(verdicts).filter(v=>v==="faithful").length,
      substitution:Object.values(verdicts).filter(v=>v==="substitution").length,
      unreadable_in_original:Object.values(verdicts).filter(v=>v==="unreadable_in_original").length}};
  const a=document.createElement("a");
  a.href=URL.createObjectURL(new Blob([JSON.stringify(out,null,2)],{type:"application/json"}));
  a.download="ocr-review-results.json"; a.click();
};
document.getElementById("clear").onclick=()=>{
  if(confirm("Clear every verdict you have recorded?")){verdicts={};save();paint();}
};
addEventListener("keydown",e=>{
  const m={"1":"faithful","2":"substitution","3":"unreadable_in_original"}[e.key];
  if(!m)return;
  const nxt=rows.filter(r=>r.physical_page===cur).find(r=>!verdicts[r._i]);
  if(nxt){verdicts[nxt._i]=m;save();paint();}
});
paint();
</script>
"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--worksheet", required=True, type=pathlib.Path)
    ap.add_argument("--out", required=True, type=pathlib.Path)
    args = ap.parse_args()

    data = json.loads(args.worksheet.read_text(encoding="utf-8"))
    blob = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    args.out.write_text(PAGE.replace("__DATA__", blob), encoding="utf-8")
    print(f"wrote {args.out} ({args.out.stat().st_size // 1024} KB, "
          f"{len(data['rows'])} rows, no external assets)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
