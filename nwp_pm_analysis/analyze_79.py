import json,re,pathlib,html as H,sys,time,difflib
sys.path.insert(0,'.')
from hsd_utils.session import get_session,HSD_URL
from hsd_utils.queries import get_article
from collections import Counter
S=get_session()
tcs=json.loads(pathlib.Path('nwp_pm_analysis/proposal_tcs.json').read_text(encoding='utf-8'))
if isinstance(tcs,dict): tcs=[tcs]
print(f'Processing {len(tcs)} TCs...')
def xc(d):
    if not d: return []
    codes=re.findall(r'<code[^>]*>([^<]{3,})</code>',d,re.IGNORECASE)
    skip=('0x','IA32','MSR','BIOS','test_case','fw_fuses','socket_rapl','PCU_CR','B2P','CCP_','ENERGY','PERF_CTL','HWP_CAP')
    return [c.strip() for c in codes if not any(c.strip().startswith(s) for s in skip)]
def sim(a,b):
    if not a or not b: return 0
    a2=a.lower().split()[0]; b2=b.lower().split()[0]
    if a.lower()==b.lower(): return 3
    if a2==b2: return 2
    if a2 in b.lower() or b2 in a.lower(): return 1
    return difflib.SequenceMatcher(None,a.lower(),b.lower()).ratio()
def bst(codes,cmd):
    if not codes or not cmd: return ('',0)
    return max(((c,sim(c,cmd)) for c in codes),key=lambda x:x[1])
results=[]
for i,tc in enumerate(tcs):
    tid=str(tc.get('nwp_tc_id',''))
    art=get_article(tid,'id,title,description',session=S)
    desc=art.get('description','') or ''
    codes=xc(desc)
    nc=tc.get('nwp_cmd','').strip()
    dc=tc.get('dmr_cmd','').strip()
    ad=(tc.get('all_dmr_cmds','') or '').strip()
    bn=bst(codes,nc); bd=bst(codes,dc)
    for alt in ad.split(' | '):
        a=alt.strip()
        if a:
            s2=bst(codes,a)
            if isinstance(s2[1],float) and isinstance(bd[1],float): chk=s2[1]>bd[1]
            elif isinstance(s2[1],float): chk=False
            elif isinstance(bd[1],float): chk=True
            else: chk=s2[1]>bd[1]
            if chk: bd=s2
    results.append({'tc_id':tid,'title':tc.get('nwp_title',''),'tp':tc.get('tp_title',''),
        'tcd':tc.get('tcd_title',''),'ve':tc.get('val_env',''),
        'nc':nc,'dc':dc,'ad':ad,'codes':codes,'bn':bn,'bd':bd,
        'tr':tc.get('tr_count',''),'dt':tc.get('dmr_tr_date','')})
    if (i+1)%10==0: print(f'  {i+1}/{len(tcs)}')
    time.sleep(0.18)
print('Writing HTML...')
def e(s): return H.escape(str(s or ''))
def lnk(id): return ('<a href="'+HSD_URL.format(id)+'" target="_blank" class="hl">'+e(id)+'</a>') if id else ''
def sbm(tup):
    s=tup[1]
    if isinstance(s,float):
        if s>=0.95: return '<span class="b3">EXACT</span>'
        if s>=0.5: return '<span class="b2">SCRIPT</span>'
        if s>0.3: return '<span class="b1">SIM '+str(int(s*100))+'%</span>'
        return '<span class="b0">NONE</span>'
    if s>=3: return '<span class="b3">EXACT</span>'
    if s>=2: return '<span class="b2">SCRIPT</span>'
    if s>=1: return '<span class="b1">PARTIAL</span>'
    return '<span class="b0">NONE</span>'
sm=Counter(); hrows=''
for r in sorted(results,key=lambda x:(x['tp'],x['tcd'])):
    ns=r['bn'][1]; ds=r['bd'][1]
    ov=max(ns if isinstance(ns,(int,float)) else 0, ds if isinstance(ds,(int,float)) else 0)
    iv=int(ov) if not isinstance(ov,float) else 0
    fv=ov if isinstance(ov,float) else 0.0
    if iv>=3: cat='EXACT'
    elif iv>=2: cat='SCRIPT'
    elif iv>=1 or fv>0.3: cat='PARTIAL'
    else: cat='NONE'
    sm[cat]+=1
    rc={'EXACT':'#f0fdf4','SCRIPT':'#fefce8','PARTIAL':'#fff7ed','NONE':'#fff1f2'}.get(cat,'#fff')
    ch=''.join('<div class="dc">'+e(c)+'</div>' for c in r['codes'][:5]) or '<em class="na">none extracted</em>'
    ah=''.join('<div class="alt">'+e(a.strip())+'</div>' for a in r['ad'].split(' | ') if a.strip() and a.strip()!=r['dc'])
    hrows+=('<tr style="background:'+rc+'">'+
        '<td><span class="tpt">'+e(r['tp'].replace('[NWP PM] ','')[:30])+'</span><br/><span class="f9">'+e(r['tcd'][:40])+'</span></td>'+
        '<td>'+lnk(r['tc_id'])+'<br/><span class="f10">'+e(r['title'][:50])+'</span></td>'+
        '<td class="f10">'+e(r['ve'])+'</td>'+
        '<td class="cmd">'+ch+'</td>'+
        '<td class="cmd">'+(e(r['nc']) or '<em class=na>-</em>')+'</td>'+
        '<td class="cmd">'+(e(r['dc']) or '<em class=na>-</em>')+ah+'<br/><span class="f9 dt">'+e(r['dt'])+' ('+e(r['tr'])+' TRs)</span></td>'+
        '<td style="text-align:center">'+sbm(r['bn'])+'<br/><span class="f9">'+e(r['bn'][0][:28])+'</span></td>'+
        '<td style="text-align:center">'+sbm(r['bd'])+'<br/><span class="f9">'+e(r['bd'][0][:28])+'</span></td>'+
        '</tr>')
st=''.join('<tr><td>'+e(k)+'</td><td style="text-align:center;font-weight:700">'+str(v)+'</td></tr>' for k,v in sorted(sm.items()))
n=len(results)
legend='<div style="font-size:11px;display:flex;flex-direction:column;gap:3px;padding:0 12px"><div><span class="b3">EXACT</span> same script found in test steps</div><div><span class="b2">SCRIPT</span> same script name, diff args</div><div><span class="b1">PARTIAL/SIM</span> keyword or similarity match</div><div><span class="b0">NONE</span> description does not mention this script</div></div>'
css='*{box-sizing:border-box;margin:0;padding:0}body{font-family:Segoe UI,Arial,sans-serif;background:#f0f4f9;font-size:12px;color:#1f2937}.hdr{background:#0f4c81;color:#fff;padding:14px 28px}.hdr h1{font-size:18px;font-weight:600}.hdr .sub{font-size:11px;opacity:.8;margin-top:3px}.ctrl{padding:8px 16px;background:#fff;border-bottom:1px solid #d9e2ec;display:flex;gap:10px;align-items:center}.ctrl input{padding:5px 9px;border:1px solid #cbd5e0;border-radius:5px;font-size:12px;width:240px}.ctrl select{padding:5px 9px;border:1px solid #cbd5e0;border-radius:5px;font-size:12px}.wrap{padding:10px 16px 40px}.top{display:flex;gap:14px;margin-bottom:12px}.smry{border-collapse:collapse;font-size:11px}.smry th{background:#374151;color:#fff;padding:4px 10px}.smry td{padding:4px 10px;border:1px solid #d1d5db}table.mt{width:100%;border-collapse:collapse}th{background:#1e3a8a;color:#fff;padding:6px 8px;text-align:left;font-size:11px;position:sticky;top:0;z-index:5}td{padding:5px 7px;border-bottom:1px solid #e2e8f0;vertical-align:top}tr:hover td{filter:brightness(.97)}.tpt{background:#e0e7ff;color:#3730a3;padding:1px 5px;border-radius:5px;font-size:10px;font-weight:600;white-space:nowrap}.cmd{max-width:175px;word-break:break-all;font-family:Consolas,monospace;font-size:10px}.dc{background:#f1f5f9;padding:2px 4px;margin:2px 0;border-radius:3px;font-size:10px}.alt{font-size:9px;color:#6b7280;margin-top:1px}.f9{font-size:9px}.f10{font-size:10px}.na{color:#d1d5db;font-size:10px}.dt{color:#9ca3af}.hl{color:#1a56db;text-decoration:none;font-family:Consolas,monospace;font-size:11px}.hl:hover{text-decoration:underline}.b3{background:#16a34a;color:#fff;padding:1px 7px;border-radius:8px;font-size:10px;font-weight:600}.b2{background:#ca8a04;color:#fff;padding:1px 7px;border-radius:8px;font-size:10px;font-weight:600}.b1{background:#ea580c;color:#fff;padding:1px 7px;border-radius:8px;font-size:10px;font-weight:600}.b0{background:#dc2626;color:#fff;padding:1px 7px;border-radius:8px;font-size:10px;font-weight:600}'
out=pathlib.Path('nwp_pm_analysis/nwp_79tc_step_cmd_match.html')
pg=('<!DOCTYPE html><html lang=en><head><meta charset=UTF-8><title>Test Step vs Cmd</title><style>'+css+'</style></head><body>'
    '<div class=hdr><h1>NWP TC: Description Test Steps vs Command Line Match</h1>'
    '<div class=sub>'+str(n)+' candidates | Description code-tags vs NWP free_tag_2 vs DMR TR cmd | 2026-07-03 | PROPOSAL ONLY - no HSD update</div></div>'
    '<div class=ctrl><input type=text id=q placeholder="Search TC, command..." oninput="filt()">'
    '<select id=mt onchange="filt()"><option value="">All</option><option>EXACT</option><option>SCRIPT</option><option>PARTIAL</option><option>NONE</option></select>'
    '<span style="margin-left:auto;font-size:11px;color:#718096" id=sb></span></div>'
    '<div class=wrap><div class=top><table class=smry><tr><th>Match</th><th>Count</th></tr>'+st+'</table>'+legend+'</div>'
    '<table class=mt id=T><thead><tr><th>TP / TCD</th><th>NWP TC</th><th>Val Env</th>'
    '<th>Commands in Description<br/><span style="font-weight:400;font-size:9px">code tags from test steps</span></th>'
    '<th>NWP free_tag_2<br/><span style="font-weight:400;font-size:9px">current</span></th>'
    '<th>DMR TR cmd<br/><span style="font-weight:400;font-size:9px">latest + all variants</span></th>'
    '<th>Desc = NWP?</th><th>Desc = DMR?</th></tr></thead>'
    '<tbody id=TB>'+hrows+'</tbody></table></div>'
    '<script>function filt(){var q=document.getElementById("q").value.toLowerCase(),mt=document.getElementById("mt").value.toLowerCase(),rows=document.querySelectorAll("#TB tr"),shown=0;rows.forEach(function(r){var txt=r.textContent.toLowerCase();var ok=(!q||txt.includes(q))&&(!mt||txt.includes(mt));r.style.display=ok?"":"none";if(ok)shown++});document.getElementById("sb").textContent="Showing "+shown+"/'+str(n)+'"}</script>'
    '</body></html>')
out.write_bytes(pg.encode('utf-8'))
print('HTML:',out,'(',out.stat().st_size,'bytes)')
print('Summary:',dict(sm))