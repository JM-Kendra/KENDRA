#!/usr/bin/env python3
"""Render a truth-entry form for the substitutions found by the OCR sweep.

EXP-07 cannot be frozen until the reviewer records what each substituted token
actually reads in the rendered original. This builds a local, self-contained form
covering exactly those rows -- the ones verdicted `substitution` -- and nothing else.

Rows verdicted `faithful` already have their truth (the baseline surface form).
Rows verdicted `unreadable_in_original` are excluded from the truth set by
EXP-07 Section 4 and are deliberately absent here.

No external assets, so it opens from disk with networking off, per ADR-001.
Output goes under evaluation/runs/ which is gitignored. Do not commit its output.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

PAGE = """<!doctype html>
<meta charset="utf-8">
<title>OCR truth entry</title>
<style>
:root{--bg:#faf9f7;--fg:#1a1a1a;--mut:#6b6b6b;--line:#e0ddd8;--card:#fff;
--bad:#b3261e;--badbg:#fbeae9;--ok:#1f7a4d;--acc:#2a5db0;}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);
font:16px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;}
header{background:var(--card);border-bottom:1px solid var(--line);padding:14px 28px;}
h1{margin:0 0 6px;font-size:20px;}
.sub{color:var(--mut);font-size:14px;max-width:78ch;}
.wrap{max-width:960px;margin:0 auto;padding:16px 28px 80px;}
.bar{height:8px;background:var(--line);border-radius:99px;overflow:hidden;margin:14px 0 4px;}
.bar>i{display:block;height:100%;background:var(--ok);width:0;transition:width .2s;}
.tot{font-size:13px;color:var(--mut);margin-bottom:14px;}
h2{font-size:15px;margin:26px 0 10px;color:var(--mut);
border-bottom:1px solid var(--line);padding-bottom:6px;}
.row{background:var(--card);border:1px solid var(--line);border-radius:10px;
padding:14px 16px;margin-bottom:10px;}
.row.filled{border-color:var(--ok);}
.meta{font-size:12.5px;color:var(--mut);margin-bottom:8px;}
.read{display:flex;align-items:center;gap:10px;flex-wrap:wrap;}
.lbl{font-size:12.5px;color:var(--mut);min-width:150px;}
code{font:15px/1.4 ui-monospace,SFMono-Regular,Menlo,monospace;background:var(--badbg);
padding:3px 9px;border-radius:5px;border:1px solid var(--bad);color:var(--bad);}
.ctx{color:var(--mut);font-size:12.5px;margin:8px 0 10px;
font-family:ui-monospace,Menlo,monospace;white-space:pre-wrap;word-break:break-word;}
input[type=text]{font:15px ui-monospace,Menlo,monospace;padding:8px 11px;
border:1px solid var(--line);border-radius:6px;min-width:220px;background:#fff;}
input[type=text]:focus{outline:none;border-color:var(--acc);box-shadow:0 0 0 3px #2a5db022;}
.foot{position:fixed;left:0;right:0;bottom:0;background:var(--card);
border-top:1px solid var(--line);padding:12px 28px;display:flex;gap:12px;align-items:center;}
.foot .sp{flex:1;font-size:13px;color:var(--mut);}
button.go{background:var(--acc);color:#fff;border:none;border-radius:8px;
padding:10px 18px;font-size:14px;cursor:pointer;}
.note{background:#fff8e6;border:1px solid #eadfb8;border-radius:8px;
padding:12px 16px;margin:12px 0;font-size:14px;line-height:1.6;}
</style>
<header>
<h1>What do these actually say?</h1>
<div class="sub">These are the <b>__N__</b> numbers you marked as misread. For each one, look at
the rendered original and type what it <b>really</b> says. This becomes the answer key the new
OCR settings are scored against.</div>
</header>
<div class="wrap">
<div class="note">
Type it <b>exactly as printed</b>, including commas and decimal points — <code
style="background:#f0eeea;border-color:#e0ddd8;color:#1a1a1a">3,214.28</code>, not
<code style="background:#f0eeea;border-color:#e0ddd8;color:#1a1a1a">3214.28</code>.
If you find you can't read it after all, leave it blank and tell me — it moves to the excluded
set rather than being guessed.
</div>
<div class="bar"><i id="pb"></i></div>
<div class="tot" id="tot"></div>
<div id="list"></div>
</div>
<div class="foot"><div class="sp" id="status"></div>
<button class="go" id="exp">Export answer key</button></div>
<script>
const DATA = __DATA__;
const KEY = "kendra-ocr-truth:" + DATA.run_id;
let truth = JSON.parse(localStorage.getItem(KEY) || "{}");
const save=()=>localStorage.setItem(KEY,JSON.stringify(truth));
function esc(s){return String(s).replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));}
function paint(){
  const done=Object.values(truth).filter(v=>v&&v.trim()).length, tot=DATA.rows.length;
  document.getElementById("pb").style.width=(100*done/tot)+"%";
  document.getElementById("tot").textContent=done+" of "+tot+" recorded";
  document.getElementById("status").textContent=
    done===tot?"All recorded — export the answer key.":"Saves as you type.";
}
const list=document.getElementById("list");
let page=null;
DATA.rows.forEach((r,i)=>{
  if(r.physical_page!==page){page=r.physical_page;
    const h=document.createElement("h2");h.textContent="Physical page "+page;list.appendChild(h);}
  const d=document.createElement("div");
  d.className="row"+((truth[i]||"").trim()?" filled":"");
  d.innerHTML="<div class='meta'>line "+r.line+"</div>"+
    "<div class='read'><span class='lbl'>Computer read it as</span><code>"+esc(r.surface_form)+"</code></div>"+
    "<div class='ctx'>"+esc(r.line_context)+"</div>"+
    "<div class='read'><span class='lbl'>The original actually says</span>"+
    "<input type='text' value='"+esc(truth[i]||"")+"' placeholder='type exactly as printed'></div>";
  const inp=d.querySelector("input");
  inp.oninput=()=>{truth[i]=inp.value;save();
    d.className="row"+(inp.value.trim()?" filled":"");paint();};
  list.appendChild(d);
});
document.getElementById("exp").onclick=()=>{
  const out={run_id:DATA.run_id,purpose:"EXP-07 truth set: reviewer readings for substituted tokens",
    exported_at:new Date().toISOString(),
    rows:DATA.rows.map((r,i)=>({...r,truth_surface_form:(truth[i]||"").trim()})),
    recorded:Object.values(truth).filter(v=>v&&v.trim()).length,total:DATA.rows.length};
  const a=document.createElement("a");
  a.href=URL.createObjectURL(new Blob([JSON.stringify(out,null,2)],{type:"application/json"}));
  a.download="ocr-truth-set.json";a.click();
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
    subs = [r for r in data["rows"] if r.get("reviewer_verdict") == "substitution"]
    subs.sort(key=lambda r: (r["physical_page"], r["line"]))
    payload = {"run_id": data["run_id"], "rows": subs}
    blob = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    args.out.write_text(
        PAGE.replace("__DATA__", blob).replace("__N__", str(len(subs))), encoding="utf-8"
    )
    print(f"wrote {args.out} ({len(subs)} substituted tokens to transcribe)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
