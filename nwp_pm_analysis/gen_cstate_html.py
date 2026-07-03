import json,pathlib,html as H,re
from collections import defaultdict

tcs=json.loads(pathlib.Path('nwp_pm_analysis/cstate_tcs.json').read_text(encoding='utf-8'))
if isinstance(tcs,dict): tcs=[tcs]
HSD_URL='https://hsdes.intel.com/appstore/article-one/#/{}'
OUT=pathlib.Path('nwp_pm_analysis/cstate_tc_descriptions.html')

# Group by TPF > TCD
grouped=defaultdict(lambda:defaultdict(list))
tpf_order=[]; tcd_order={}
for tc in tcs:
    k=(tc.get('tpf_id',''),tc.get('tpf_title',''))
    k2=(tc.get('tcd_id',''),tc.get('tcd_title',''))
    if k not in tpf_order: tpf_order.append(k)
    if k not in tcd_order: tcd_order[k]=[]
    if k2 not in tcd_order[k]: tcd_order[k].append(k2)
    grouped[k][k2].append(tc)

def e(s): return H.escape(str(s or ''))
def lnk(id,lbl=None,cls='hl'): return f'<a href="{HSD_URL.format(id)}" target="_blank" class="{cls}">{e(lbl or id)}</a>' if id else ''
def status_badge(s):
    c={'open':'#dcfce7;color:#166534','rejected':'#fee2e2;color:#991b1b'}.get(str(s).split('.')[0],'#f3f4f6;color:#374151')
    return f'<span style="background:{c};padding:1px 7px;border-radius:8px;font-size:10px;font-weight:600">{e(s)}</span>'

body=''
for i_tpf,(tpf_id,tpf_title) in enumerate(tpf_order):
    tc_count=sum(len(grouped[(tpf_id,tpf_title)][k]) for k in grouped[(tpf_id,tpf_title)])
    body+=(f'<details class="tpf" open>'
           f'<summary class="tpf-hdr"><span class="tpf-tag">TPF</span> {lnk(tpf_id,tpf_title,"tpf-lnk")} '
           f'<span class="cnt">{tc_count} TCs</span></summary>')
    for j_tcd,(tcd_id,tcd_title) in enumerate(tcd_order[(tpf_id,tpf_title)]):
        tcs_in=grouped[(tpf_id,tpf_title)][(tcd_id,tcd_title)]
        body+=(f'<details class="tcd" open>'
               f'<summary class="tcd-hdr"><span class="tcd-tag">TCD</span> {lnk(tcd_id,tcd_title,"tcd-lnk")} '
               f'<span class="cnt">{len(tcs_in)} TCs</span></summary>')
        for tc in sorted(tcs_in,key=lambda x:str(x.get('tc_id',''))):
            desc=tc.get('desc','') or ''
            cmd=tc.get('cmd','') or ''
            env=tc.get('env','') or ''
            status=tc.get('status','')
            has_blue='background:#cce4f7' in desc
            if not desc.strip():
                desc_html='<div class="no-desc">No description yet</div>'
            elif not has_blue:
                desc_html='<div class="old-desc">'+desc+'</div>'
            else:
                desc_html=desc
            body+=(f'<div class="tc-card" id="tc-{e(tc.get(chr(116)+chr(99)+chr(95)+chr(105)+chr(100),chr(48)))}">'
                   f'<div class="tc-hdr">'
                   f'<span class="tc-tag">TC</span> {lnk(str(tc.get("tc_id","")),None,"tc-lnk")}'
                   f'<span class="tc-title">{e(tc.get("tc_title",""))}</span>'
                   f'{status_badge(status)}'
                   f'{"<span class=new-fmt>new format</span>" if has_blue else "<span class=old-fmt>old format</span>"}'
                   f'</div>'
                   f'<div class="tc-meta">'
                   f'<span>Env: <code>{e(env)}</code></span>'
                   f'{"<span>Cmd: <code class=cmd>"+e(cmd)+"</code></span>" if cmd else ""}'
                   f'</div>'
                   f'<div class="tc-desc">{desc_html}</div>'
                   f'</div>')
        body+='</details>'
    body+='</details>'

stats_open=sum(1 for tc in tcs if tc.get('status','')=='open')
stats_new=sum(1 for tc in tcs if 'background:#cce4f7' in (tc.get('desc','') or ''))
css='''*{box-sizing:border-box;margin:0;padding:0}
body{font-family:Segoe UI,Arial,sans-serif;background:#f0f4f9;color:#1f2937;font-size:13px}
.hdr{background:linear-gradient(135deg,#0f4c81,#1a73e8);color:#fff;padding:18px 28px}
.hdr h1{font-size:20px;font-weight:700;margin-bottom:4px}
.hdr .sub{font-size:11px;opacity:.85}
.ctrl{padding:10px 18px;background:#fff;border-bottom:1px solid #d9e2ec;display:flex;gap:10px;align-items:center;flex-wrap:wrap;position:sticky;top:0;z-index:100}
.ctrl input{padding:6px 10px;border:1px solid #cbd5e0;border-radius:5px;font-size:12px;width:260px}
.ctrl select{padding:6px 9px;border:1px solid #cbd5e0;border-radius:5px;font-size:12px}
.ctrl button{padding:5px 12px;border:1px solid #cbd5e0;border-radius:5px;background:#fff;cursor:pointer;font-size:12px}
.ctrl button:hover{background:#e8f0fe}
.stats{display:flex;gap:12px;padding:10px 18px;background:#fff;border-bottom:1px solid #d9e2ec;flex-wrap:wrap}
.stat{text-align:center;padding:6px 14px;border-radius:8px;font-weight:700;font-size:11px}
.wrap{max-width:1300px;margin:14px auto;padding:0 16px 50px}
details.tpf{background:#fff;border:1px solid #c7d2fe;border-radius:8px;margin-bottom:16px;overflow:hidden}
.tpf-hdr{background:#eef2ff;padding:12px 16px;cursor:pointer;display:flex;align-items:center;gap:8px;font-weight:700;font-size:14px;list-style:none}
.tpf-hdr::-webkit-details-marker{display:none}
.tpf-hdr::before{content:"▶";font-size:10px;transition:transform .2s}
details[open].tpf > .tpf-hdr::before{transform:rotate(90deg)}
details.tcd{margin:10px 16px 10px 16px;border:1px solid #d9e2ec;border-radius:6px;overflow:hidden}
.tcd-hdr{background:#f8faff;padding:10px 14px;cursor:pointer;display:flex;align-items:center;gap:8px;font-weight:600;font-size:13px;list-style:none}
.tcd-hdr::-webkit-details-marker{display:none}
.tcd-hdr::before{content:"▶";font-size:10px;transition:transform .2s}
details[open].tcd > .tcd-hdr::before{transform:rotate(90deg)}
.tc-card{margin:8px 12px;border:1px solid #e2e8f0;border-radius:6px;overflow:hidden;background:#fff}
.tc-hdr{background:#f0f4f9;padding:8px 14px;display:flex;align-items:center;gap:8px;border-bottom:1px solid #e2e8f0;flex-wrap:wrap}
.tc-meta{padding:6px 14px;background:#fafafa;border-bottom:1px solid #e2e8f0;font-size:11px;display:flex;gap:14px;flex-wrap:wrap}
.tc-meta code{font-family:Consolas,monospace;font-size:10px;background:#e8f0fe;padding:1px 5px;border-radius:3px}
.tc-meta .cmd{background:#dcfce7;color:#166534}
.tc-desc{padding:12px 14px;font-size:12px}
.tc-tag{background:#0f4c81;color:#fff;padding:1px 7px;border-radius:8px;font-size:10px;font-weight:700}
.tcd-tag{background:#166534;color:#fff;padding:1px 7px;border-radius:8px;font-size:10px;font-weight:700}
.tpf-tag{background:#4f46e5;color:#fff;padding:1px 7px;border-radius:8px;font-size:10px;font-weight:700}
.tc-title{font-weight:600;font-size:13px;flex:1}
.tpf-lnk,.tcd-lnk,.tc-lnk{color:#1a56db;text-decoration:none;font-family:Consolas,monospace;font-size:11px}
.tpf-lnk{color:#3730a3;font-size:13px;font-family:inherit;font-weight:700}
.tcd-lnk{color:#166534;font-size:12px;font-family:inherit;font-weight:600}
.tpf-lnk:hover,.tcd-lnk:hover,.tc-lnk:hover{text-decoration:underline}
.cnt{margin-left:auto;font-size:11px;color:#6b7280;font-weight:400}
.new-fmt{background:#dcfce7;color:#166534;padding:1px 7px;border-radius:8px;font-size:9px;font-weight:600}
.old-fmt{background:#fee2e2;color:#991b1b;padding:1px 7px;border-radius:8px;font-size:9px;font-weight:600}
.no-desc{background:#f9fafb;border:1px dashed #d1d5db;padding:12px;color:#9ca3af;font-style:italic;border-radius:4px}
.old-desc{background:#fffbeb;border-left:3px solid #f59e0b;padding:12px;font-size:12px;line-height:1.6}
.tc-card.hidden{display:none}'''
js='''function doFilter(){
  var q=document.getElementById("q").value.toLowerCase();
  var st=document.getElementById("sf").value;
  var fmt=document.getElementById("ff").value;
  var cards=document.querySelectorAll(".tc-card");
  var shown=0;
  cards.forEach(function(c){
    var txt=c.textContent.toLowerCase();
    var s_ok=!st||(st==="open"&&c.querySelector(".tc-hdr span[style*='dcfce7']"))||(st==="rejected"&&c.querySelector(".tc-hdr span[style*='fee2e2']"));
    var f_ok=!fmt||(fmt==="new"&&c.querySelector(".new-fmt"))||(fmt==="old"&&c.querySelector(".old-fmt"));
    var q_ok=!q||txt.includes(q);
    var ok=q_ok&&s_ok&&f_ok;
    c.style.display=ok?"":"none";
    if(ok)shown++;
  });
  document.getElementById("sb").textContent="Showing "+shown+" / "+cards.length+" TCs";
}
function expandAll(){document.querySelectorAll("details").forEach(function(d){d.open=true})}
function collapseAll(){document.querySelectorAll("details").forEach(function(d){d.open=false})}
'''
pg=(f'<!DOCTYPE html><html lang=en><head><meta charset=UTF-8><meta name="viewport" content="width=device-width,initial-scale=1">'
    f'<title>[NWP PM] C-State TC Descriptions</title><style>{css}</style></head><body>'
    f'<div class=hdr><h1>[NWP PM] C-State (PantherCove PNC) — TC Descriptions</h1>'
    f'<div class=sub>TP: 15019478558 &bull; {len(tcs)} TCs across 5 TPFs &bull; Generated 2026-07-03</div></div>'
    f'<div class=stats>'
    f'<div class=stat style="background:#dbeafe;color:#1e40af"><div style="font-size:24px">{len(tcs)}</div>Total TCs</div>'
    f'<div class=stat style="background:#dcfce7;color:#166534"><div style="font-size:24px">{stats_open}</div>Open</div>'
    f'<div class=stat style="background:#fef9c3;color:#854d0e"><div style="font-size:24px">{stats_new}</div>New Format</div>'
    f'<div class=stat style="background:#fee2e2;color:#991b1b"><div style="font-size:24px">{len(tcs)-stats_new}</div>Old/No Format</div>'
    f'</div>'
    f'<div class=ctrl>'
    f'<input type=text id=q placeholder="Search TC, TCD, command..." oninput="doFilter()">'
    f'<select id=sf onchange="doFilter()"><option value="">All status</option><option value="open">Open</option><option value="rejected">Rejected</option></select>'
    f'<select id=ff onchange="doFilter()"><option value="">All formats</option><option value="new">New format</option><option value="old">Old/no format</option></select>'
    f'<button onclick="expandAll()">Expand All</button>'
    f'<button onclick="collapseAll()">Collapse All</button>'
    f'<span style="margin-left:auto;font-size:11px;color:#718096" id=sb></span>'
    f'</div>'
    f'<div class=wrap>{body}</div>'
    f'<script>{js}window.addEventListener("load",doFilter)</script>'
    f'</body></html>')
OUT.write_bytes(pg.encode('utf-8'))
print(f'HTML: {OUT} ({OUT.stat().st_size//1024} KB)')