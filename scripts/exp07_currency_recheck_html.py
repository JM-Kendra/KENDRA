#!/usr/bin/env python3
"""Render a line-grouped re-check form for digit tokens on currency-bearing lines.

The 2026-08-20 sweep compared fragments. That is blind to one defect: when OCR
destroys a decimal separator, one printed number becomes several tokens and each
fragment still looks like a plausible number. `2.500` and `00` both pass fragment
review; the printed `2,500.00` is gone.

This form asks a different question -- for each captured fragment, what is the
COMPLETE printed number it belongs to -- so the truth unit becomes the printed
number rather than the token. It also offers an explicit "not on the page" answer,
since the sweep confirmed two fabricated tokens.

Scope is fragments matching the defect signature -- an internal separator, or an
orphaned two-digit cents fragment. It is a targeted second pass, not a re-run of
the full 306-token sweep.

No external assets, opens from disk with networking off, per ADR-001.
Output goes under evaluation/runs/ which is gitignored. Do not commit its output.
"""

from __future__ import annotations

import argparse
import collections
import json
import pathlib
import re
import sys

# Select on the defect signature, not on topic words. Two shapes carry the
# split-decimal / misread-separator class:
#   1. a separator sitting between digits, which may be a comma read as a period;
#   2. a bare two-digit token directly following a digit in the line, which is the
#      orphaned cents fragment left when a decimal point is destroyed.
# Selecting by currency vocabulary instead pulled in section references such as
# "Sections 113 and 237" merely because the line mentioned "Sales Invoices".
_SEPARATOR_BETWEEN_DIGITS = re.compile(r"\d[.,]\d")
_BARE_TWO_DIGITS = re.compile(r"\d{2}")


def _is_orphan_cents(row: dict) -> bool:
    if not _BARE_TWO_DIGITS.fullmatch(row["surface_form"]):
        return False
    context = row["line_context"]
    for match in re.finditer(re.escape(row["surface_form"]), context):
        if re.search(r"\d\s*$", context[: match.start()].rstrip()):
            return True
    return False


def _is_at_risk(row: dict) -> bool:
    return bool(_SEPARATOR_BETWEEN_DIGITS.search(row["surface_form"])) or _is_orphan_cents(row)

PAGE = """<!doctype html>
<meta charset="utf-8">
<title>Currency re-check</title>
<style>
:root{--bg:#faf9f7;--fg:#1a1a1a;--mut:#6b6b6b;--line:#e0ddd8;--card:#fff;
--ok:#1f7a4d;--bad:#b3261e;--badbg:#fbeae9;--acc:#2a5db0;}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);
font:16px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;}
header{background:var(--card);border-bottom:1px solid var(--line);padding:14px 28px;}
h1{margin:0 0 6px;font-size:20px;}
.sub{color:var(--mut);font-size:14px;max-width:80ch;}
.wrap{max-width:980px;margin:0 auto;padding:16px 28px 80px;}
.note{background:#fff8e6;border:1px solid #eadfb8;border-radius:8px;
padding:12px 16px;margin:12px 0;font-size:14px;line-height:1.6;}
.bar{height:8px;background:var(--line);border-radius:99px;overflow:hidden;margin:14px 0 4px;}
.bar>i{display:block;height:100%;background:var(--ok);width:0;transition:width .2s;}
.tot{font-size:13px;color:var(--mut);margin-bottom:14px;}
h2{font-size:15px;margin:26px 0 8px;color:var(--mut);
border-bottom:1px solid var(--line);padding-bottom:6px;}
.lineblk{background:var(--card);border:1px solid var(--line);border-radius:10px;
padding:14px 16px;margin-bottom:12px;}
.lno{font-size:12.5px;color:var(--mut);margin-bottom:6px;}
.ctx{font:13px ui-monospace,Menlo,monospace;background:#f4f2ee;border:1px solid var(--line);
border-radius:6px;padding:9px 11px;white-space:pre-wrap;word-break:break-word;margin-bottom:12px;}
.frag{display:flex;align-items:center;gap:10px;flex-wrap:wrap;padding:7px 0;
border-top:1px dashed var(--line);}
.frag:first-of-type{border-top:none}
code{font:15px ui-monospace,Menlo,monospace;background:#f0eeea;padding:3px 9px;
border-radius:5px;border:1px solid var(--line);min-width:86px;text-align:center;}
code.sub{background:var(--badbg);border-color:var(--bad);color:var(--bad);}
.arrow{color:var(--mut)}
input[type=text]{font:15px ui-monospace,Menlo,monospace;padding:7px 10px;
border:1px solid var(--line);border-radius:6px;min-width:180px;}
input[type=text]:focus{outline:none;border-color:var(--acc);box-shadow:0 0 0 3px #2a5db022;}
input[type=text]:disabled{background:#f0eeea;color:var(--mut)}
label.na{font-size:13px;color:var(--mut);display:flex;align-items:center;gap:5px;cursor:pointer}
.done{border-color:var(--ok)}
.foot{position:fixed;left:0;right:0;bottom:0;background:var(--card);
border-top:1px solid var(--line);padding:12px 28px;display:flex;gap:12px;align-items:center;}
.foot .sp{flex:1;font-size:13px;color:var(--mut);}
button.go{background:var(--acc);color:#fff;border:none;border-radius:8px;
padding:10px 18px;font-size:14px;cursor:pointer;}
</style>
<header>
<h1>Currency re-check — what is the complete printed number?</h1>
<div class="sub">Last time you compared each fragment on its own. That can't catch a lost
decimal point: <b>2.500</b> and <b>00</b> each look fine, but the page prints
<b>2,500.00</b>. So this time, for each fragment, type the <b>whole number it belongs to</b>,
exactly as printed.</div>
</header>
<div class="wrap">
<div class="note">
If several fragments belong to one printed number, <b>give that same number for each of
them</b> — that is how I learn they were one number split apart.<br>
If a fragment corresponds to nothing on the page, tick <b>not on the page</b>. You already
found two of those.<br>
Red fragments are ones you previously marked misread; grey ones you previously passed.
</div>
<div class="bar"><i id="pb"></i></div>
<div class="tot" id="tot"></div>
<div id="list"></div>
</div>
<div class="foot"><div class="sp" id="status"></div>
<button class="go" id="exp">Export re-check</button></div>
<script>
const DATA=__DATA__;
const KEY="kendra-currency-recheck:"+DATA.run_id;
let ans=JSON.parse(localStorage.getItem(KEY)||"{}");
const save=()=>localStorage.setItem(KEY,JSON.stringify(ans));
function esc(s){return String(s).replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));}
function filled(i){const a=ans[i];return a&&(a.absent||(a.printed||"").trim());}
function paint(){
  const n=DATA.rows.filter((_,i)=>filled(i)).length,t=DATA.rows.length;
  document.getElementById("pb").style.width=(100*n/t)+"%";
  document.getElementById("tot").textContent=n+" of "+t+" fragments answered";
  document.getElementById("status").textContent=n===t?"Complete — export below.":"Saves as you type.";
}
const list=document.getElementById("list"),groups={};
DATA.rows.forEach((r,i)=>{(groups[r.physical_page+"|"+r.line]=groups[r.physical_page+"|"+r.line]||[]).push([r,i]);});
let page=null;
Object.keys(groups).forEach(k=>{
  const g=groups[k],r0=g[0][0];
  if(r0.physical_page!==page){page=r0.physical_page;
    const h=document.createElement("h2");h.textContent="Physical page "+page;list.appendChild(h);}
  const blk=document.createElement("div");blk.className="lineblk";
  blk.innerHTML="<div class='lno'>line "+r0.line+"</div><div class='ctx'>"+esc(r0.line_context)+"</div>";
  g.forEach(([r,i])=>{
    const row=document.createElement("div");row.className="frag";
    const sub=r.reviewer_verdict==="substitution"?" sub":"";
    row.innerHTML="<code class='"+sub.trim()+"'>"+esc(r.surface_form)+"</code>"+
      "<span class='arrow'>belongs to</span>"+
      "<input type='text' placeholder='whole number as printed'>"+
      "<label class='na'><input type='checkbox'> not on the page</label>";
    const inp=row.querySelector("input[type=text]"),cb=row.querySelector("input[type=checkbox]");
    const a=ans[i]||{};inp.value=a.printed||"";cb.checked=!!a.absent;inp.disabled=cb.checked;
    const upd=()=>{ans[i]={printed:inp.value,absent:cb.checked};inp.disabled=cb.checked;
      save();blk.className="lineblk"+(g.every(([,j])=>filled(j))?" done":"");paint();};
    inp.oninput=upd;cb.onchange=upd;
    blk.appendChild(row);
  });
  if(g.every(([,j])=>filled(j)))blk.className="lineblk done";
  list.appendChild(blk);
});
document.getElementById("exp").onclick=()=>{
  const out={run_id:DATA.run_id,purpose:"EXP-07 currency re-check: printed-number truth for currency-line fragments",
    exported_at:new Date().toISOString(),
    rows:DATA.rows.map((r,i)=>({...r,printed_number:(ans[i]||{}).printed||"",absent_from_page:!!(ans[i]||{}).absent})),
    answered:DATA.rows.filter((_,i)=>filled(i)).length,total:DATA.rows.length};
  const a=document.createElement("a");
  a.href=URL.createObjectURL(new Blob([JSON.stringify(out,null,2)],{type:"application/json"}));
  a.download="ocr-currency-recheck.json";a.click();
};
paint();
</script>
"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--results", required=True, type=pathlib.Path)
    ap.add_argument("--out", required=True, type=pathlib.Path)
    args = ap.parse_args()

    data = json.loads(args.results.read_text(encoding="utf-8"))
    sel = [r for r in data["rows"] if _is_at_risk(r)]
    sel.sort(key=lambda r: (r["physical_page"], r["line"]))
    payload = {"run_id": data["run_id"], "rows": sel}
    blob = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    args.out.write_text(PAGE.replace("__DATA__", blob), encoding="utf-8")
    lines = len({(r["physical_page"], r["line"]) for r in sel})
    verdicts = collections.Counter(r["reviewer_verdict"] for r in sel)
    print(f"wrote {args.out}")
    print(f"  {len(sel)} fragments across {lines} lines")
    print(f"  prior verdicts: {dict(verdicts)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
