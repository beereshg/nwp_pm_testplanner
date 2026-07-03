import json,re,pathlib,html as H,sys,time,difflib
sys.path.insert(0,'.')
from hsd_utils.session import get_session,HSD_URL
from hsd_utils.queries import get_article
from collections import Counter
S=get_session()
tcs=json.loads(pathlib.Path('nwp_pm_analysis/proposal_tcs.json').read_text(encoding='utf-8'))
if isinstance(tcs,dict): tcs=[tcs]
print(f'Processing {len(tcs)} TCs...')

def extract_automation_cmd(desc):
    # 1. Try "Automation command" row in Preconditions table
    m=re.search(r'Automation command[^<]*</td>\s*<td[^>]*>(.*?)</td>',desc,re.IGNORECASE|re.DOTALL)
    if m:
        cell=m.group(1)
        code=re.findall(r'<code[^>]*>([^<]+)</code>',cell)
        if code: return code[0].strip()
        plain=re.sub(r'<[^>]+>','',cell).strip()
        if plain and len(plain)>3: return plain
    # 2. Try any code tag that looks like a script (contains .py, solar, runPmx, flexcon)
    all_codes=re.findall(r'<code[^>]*>([^<]{4,})</code>',desc,re.IGNORECASE)
    script_kw=('.py','runPmx','solar','flexcon','turbo_check','hwp_','svid.','pmax_','cstate','ccf_')
    for c in all_codes:
        if any(k in c.lower() for k in script_kw): return c.strip()
    # 3. Search description text for known script names
    scripts=['thermalManagement','cstate_focus','runPmx','flexcon','solar','pmax_pmx','svid','ccf_gv',
             'cbb_ccf_pm','hwp_knobs','hwpm_pmx','turbo_check','HWP_Interrupt','hwp_fuses','mem_thermals',
             'memhot_dfx','itd.py','fine_level_plr','pmon.py']
    for sc in scripts:
        if sc.lower() in desc.lower():
            m2=re.search(r'([\w./\\-]*'+re.escape(sc)+r'[\w./\\-]*)',desc,re.IGNORECASE)
            if m2: return m2.group(1).strip()
    return ''

def script_name(cmd):
    if not cmd: return ''
    parts=cmd.replace('\\','/').split('/')
    last=parts[-1].split()[0]
    return last.lower()

def match_level(a,b):
    if not a or not b: return 0,'no cmd'
    an=script_name(a); bn=script_name(b)
    if a.lower()==b.lower(): return 3,'exact'
    if an and bn and an==bn: return 2,'same script'
    if an and bn and (an in b.lower() or bn in a.lower()): return 1,'partial'
    return 0,'diff'

results=[]
for i,tc in enumerate(tcs):
    tid=str(tc.get('nwp_tc_id',''))
    art=get_article(tid,'id,title,description',session=S)
    desc=art.get('description','') or ''
    desc_cmd=extract_automation_cmd(desc)
    nc=tc.get('nwp_cmd','').strip()
    dc=tc.get('dmr_cmd','').strip()
    ad=(tc.get('all_dmr_cmds','') or '').strip()
    lv_dn,lb_dn=match_level(desc_cmd,nc)
    lv_dd,lb_dd=match_level(desc_cmd,dc)
    lv_nd,lb_nd=match_level(nc,dc)
    # Recommendation
    if lv_nd>=2:
        rec='OK - NWP and DMR agree'
        rec_cls='ok'
    elif lv_dd>=2:
        rec='Desc aligns with DMR - update free_tag_2 to DMR cmd'
        rec_cls='upd_tag'
    elif lv_dn>=2:
        rec='Desc aligns with NWP - intentional difference from DMR'
        rec_cls='rev'
    else:
        rec='MISMATCH - desc, NWP, DMR all differ - review needed'
        rec_cls='mis'
    results.append({'tc_id':tid,'title':tc.get('nwp_title',''),'tp':tc.get('tp_title',''),
        'tcd':tc.get('tcd_title',''),'ve':tc.get('val_env',''),
        'desc_cmd':desc_cmd,'nc':nc,'dc':dc,'ad':ad,
        'lv_dn':lv_dn,'lb_dn':lb_dn,'lv_dd':lv_dd,'lb_dd':lb_dd,
        'lv_nd':lv_nd,'lb_nd':lb_nd,'rec':rec,'rec_cls':rec_cls,
        'tr':tc.get('tr_count',''),'dt':tc.get('dmr_tr_date','')})
    if (i+1)%10==0: print(f'  {i+1}/{len(tcs)}')
    time.sleep(0.18)

print('Writing HTML...')
def e(s): return H.escape(str(s or ''))
def lnk(id): return ('<a href="'+HSD_URL.format(id)+'" target="_blank" class="hl">'+e(id)+'</a>') if id else ''
def mb(lv,lb):
    cols={3:'#16a34a',2:'#ca8a04',1:'#ea580c',0:'#dc2626'}
    lbs={3:'EXACT',2:'SCRIPT',1:'PARTIAL',0:'NONE'}
    c=cols.get(lv,'#dc2626'); t=lbs.get(lv,'NONE')
    return '<span class="b" style="background:'+c+'">'+t+'</span><br/><span class="f9">'+e(lb)+'</span>'
def rec_badge(cls,txt):
    cols={'ok':'#166534','upd_tag':'#1d4ed8','rev':'#92400e','mis':'#9b1c1c'}
    bgs={'ok':'#dcfce7','upd_tag':'#dbeafe','rev':'#fef3c7','mis':'#fee2e2'}
    c=cols.get(cls,'#374151'); bg=bgs.get(cls,'#f9fafb')
    return '<div style="background:'+bg+';color:'+c+';padding:3px 6px;border-radius:4px;font-size:10px;font-weight:600">'+e(txt)+'</div>'

sm=Counter(); hrows=''
for r in sorted(results,key=lambda x:(x['tp'],x['tcd'])):
    sm[r['rec_cls']]+=1
    rc={'ok':'#f0fdf4','upd_tag':'#eff6ff','rev':'#fffbeb','mis':'#fff1f2'}.get(r['rec_cls'],'#fff')
    nd_eq='<span class="b" style="background:#16a34a">YES</span>' if r['lv_nd']>=2 else '<span class="b" style="background:#dc2626">NO</span>'
    alts=''.join('<div class="alt">'+e(a.strip())+'</div>' for a in r['ad'].split(' | ') if a.strip() and a.strip()!=r['dc'])
    hrows+=('<tr style="background:'+rc+'">'
        '<td><span class="tpt">'+e(r['tp'].replace('[NWP PM] ','')[:28])+'</span><br/><span class="f9">'+e(r['tcd'][:38])+'</span></td>'
        '<td>'+lnk(r['tc_id'])+'<br/><span class="f10">'+e(r['title'][:48])+'</span></td>'
        '<td class="cmd">'+(('<code class="dc">'+e(r['desc_cmd'])+'</code>') if r['desc_cmd'] else '<em class="na">not found in desc</em>')+'</td>'
        '<td class="cmd"><code class="nc">'+e(r['nc'])+'</code></td>'
        '<td class="cmd"><code class="dc2">'+e(r['dc'])+'</code>'+alts+'<br/><span class="f9 dt">'+e(r['dt'])+' ('+e(r['tr'])+' TRs)</span></td>'
        '<td style="text-align:center">'+nd_eq+'</td>'
        '<td style="text-align:center">'+mb(r['lv_dn'],r['lb_dn'])+'</td>'
        '<td style="text-align:center">'+mb(r['lv_dd'],r['lb_dd'])+'</td>'
        '<td>'+rec_badge(r['rec_cls'],r['rec'])+'</td>'
        '</tr>')

rec_labels={'ok':'NWP=DMR (no change needed)','upd_tag':'Desc aligns DMR (update free_tag_2)','rev':'Desc aligns NWP (intentional diff)','mis':'All differ (review)'}
st=''.join('<tr><td>'+e(rec_labels.get(k,k))+'</td><td style="text-align:center;font-weight:700">'+str(v)+'</td></tr>' for k,v in sorted(sm.items()))
n=len(results)
css='*{box-sizing:border-box;margin:0;padding:0}body{font-family:Segoe UI,Arial,sans-serif;background:#f0f4f9;font-size:12px;color:#1f2937}.hdr{background:#0f4c81;color:#fff;padding:14px 28px}.hdr h1{font-size:18px;font-weight:600}.hdr .sub{font-size:11px;opacity:.8;margin-top:3px}.ctrl{padding:8px 16px;background:#fff;border-bottom:1px solid #d9e2ec;display:flex;gap:10px;align-items:center}.ctrl input{padding:5px 9px;border:1px solid #cbd5e0;border-radius:5px;font-size:12px;width:240px}.ctrl select{padding:5px 9px;border:1px solid #cbd5e0;border-radius:5px;font-size:12px}.wrap{padding:10px 16px 40px}.top{display:flex;gap:14px;margin-bottom:12px;align-items:flex-start}.smry{border-collapse:collapse;font-size:11px;min-width:320px}.smry th{background:#374151;color:#fff;padding:5px 10px}.smry td{padding:5px 10px;border:1px solid #d1d5db}table.mt{width:100%;border-collapse:collapse}th{background:#1e3a8a;color:#fff;padding:6px 8px;text-align:left;font-size:11px;position:sticky;top:0;z-index:5}td{padding:5px 7px;border-bottom:1px solid #e2e8f0;vertical-align:top}tr:hover td{filter:brightness(.97)}.tpt{background:#e0e7ff;color:#3730a3;padding:1px 5px;border-radius:5px;font-size:10px;font-weight:600;white-space:nowrap}.cmd{max-width:170px;word-break:break-all;font-family:Consolas,monospace;font-size:10px}.nc{background:#dbeafe;padding:2px 4px;border-radius:3px;display:block}.dc{background:#dcfce7;padding:2px 4px;border-radius:3px;display:block}.dc2{background:#fef9c3;padding:2px 4px;border-radius:3px;display:block}.alt{font-size:9px;color:#6b7280}.f9{font-size:9px}.f10{font-size:10px}.na{color:#d1d5db;font-size:10px}.dt{color:#9ca3af}.hl{color:#1a56db;text-decoration:none;font-family:Consolas,monospace;font-size:11px}.hl:hover{text-decoration:underline}.b{color:#fff;padding:1px 7px;border-radius:8px;font-size:10px;font-weight:600}'
legend='<div style="font-size:11px;display:flex;flex-direction:column;gap:4px;padding:0 12px"><b>Row colours:</b><div style="background:#f0fdf4;padding:3px 6px;border-radius:4px">Green = NWP and DMR agree</div><div style="background:#eff6ff;padding:3px 6px;border-radius:4px">Blue = Desc aligns with DMR cmd</div><div style="background:#fffbeb;padding:3px 6px;border-radius:4px">Amber = Desc aligns with NWP cmd</div><div style="background:#fff1f2;padding:3px 6px;border-radius:4px">Red = All three differ</div><br/><b>Columns:</b><div>NWP=DMR: do the two reference commands match?</div><div>Desc=NWP: does description mention NWP cmd?</div><div>Desc=DMR: does description mention DMR cmd?</div></div>'
out=pathlib.Path('nwp_pm_analysis/nwp_79tc_3way_match.html')
pg=('<!DOCTYPE html><html lang=en><head><meta charset=UTF-8><title>3-Way Cmd Match '+str(n)+' TCs</title><style>'+css+'</style></head><body>'
    '<div class=hdr><h1>NWP TC - 3-Way Command Alignment: Description | NWP free_tag_2 | DMR TR</h1>'
    '<div class=sub>'+str(n)+' proposed update candidates | 2026-07-03 | PROPOSAL ONLY - no HSD update | Desc cmd extracted from Preconditions/test steps</div></div>'
    '<div class=ctrl><input type=text id=q placeholder="Search TC, command..." oninput="filt()">'
    '<select id=mt onchange="filt()"><option value="">All</option><option value="ok">NWP=DMR</option><option value="upd_tag">Update free_tag_2</option><option value="rev">Review NWP</option><option value="mis">Mismatch</option></select>'
    '<span style="margin-left:auto;font-size:11px;color:#718096" id=sb></span></div>'
    '<div class=wrap><div class=top><table class=smry><tr><th>Recommendation Category</th><th>Count</th></tr>'+st+'</table>'+legend+'</div>'
    '<table class=mt id=T><thead><tr>'
    '<th>TP / TCD</th><th>NWP TC</th>'
    '<th>Desc Automation Cmd<br/><span style="font-weight:400;font-size:9px">from Preconditions / test steps</span></th>'
    '<th>NWP free_tag_2<br/><span style="font-weight:400;font-size:9px;background:#dbeafe;padding:1px 3px">blue</span></th>'
    '<th>DMR TR cmd<br/><span style="font-weight:400;font-size:9px;background:#fef9c3;padding:1px 3px">yellow</span></th>'
    '<th>NWP = DMR?</th><th>Desc = NWP?</th><th>Desc = DMR?</th>'
    '<th>Recommendation</th></tr></thead>'
    '<tbody id=TB>'+hrows+'</tbody></table></div>'
    '<script>function filt(){var q=document.getElementById("q").value.toLowerCase(),mt=document.getElementById("mt").value,rows=document.querySelectorAll("#TB tr"),shown=0;rows.forEach(function(r){var txt=r.textContent.toLowerCase();var cls=r.getAttribute("data-cls")||"";var ok=(!q||txt.includes(q))&&(!mt||r.style.background.includes(mt)||txt.includes(mt));r.style.display=ok?"":"none";if(ok)shown++});document.getElementById("sb").textContent="Showing "+shown+"/'+str(n)+'"}</script>'
    '</body></html>')
out.write_bytes(pg.encode('utf-8'))
print('HTML:',out,'(',out.stat().st_size,'bytes)')
print('Summary:',{rec_labels.get(k,k):v for k,v in sorted(sm.items())})