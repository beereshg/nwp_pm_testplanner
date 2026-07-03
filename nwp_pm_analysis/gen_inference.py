import json,pathlib,re
tcs=json.loads(pathlib.Path('nwp_pm_analysis/cstate_tcs.json').read_text(encoding='utf-8'))
if isinstance(tcs,dict): tcs=[tcs]
print('TCs:',len(tcs))
KB=pathlib.Path('KB/pm_tc_kb/fv'); KB.mkdir(parents=True,exist_ok=True)
slug=lambda t: re.sub(r'[^a-z0-9]+','_',t.lower())[:55].strip('_')
strip=lambda h: re.sub(r'<[^>]+>','',h or '').replace('&nbsp;',' ').replace('&gt;','>').replace('&lt;','<').replace('&amp;','&').strip()
def xs(desc,label):
    m=re.search(r'>'+re.escape(label)+r'[^<]*</div>(.*?)(?=<div style|$)',desc,re.IGNORECASE|re.DOTALL)
    return strip(m.group(1))[:600] if m else ''
created=0
for tc in tcs:
    tid=str(tc.get('tc_id',''))
    title=tc.get('tc_title','')
    desc=tc.get('desc','') or ''
    cmd=tc.get('cmd','') or ''
    env=tc.get('val_env','') or ''
    tpf=tc.get('tpf_title','').replace('[NWP PM] ','')
    tcd=tc.get('tcd_title','')
    fn='HSD_'+tid+'_'+slug(title)+'.inference.md'
    fp=KB/fn
    if fp.exists(): print('SKIP',fn); continue
    sc=xs(desc,'Validation Scope'); pr=xs(desc,'Preconditions'); st=xs(desc,'Test Steps'); hc=xs(desc,'Health Check'); po=xs(desc,'Post-Process'); rf=xs(desc,'HAS Reference')
    body=['# Deep Analysis: '+title,'','| Field | Value |','|-------|-------|','| **HSD ID** | '+tid+' |','| **Title** | '+title+' |','| **Date** | 2026-07-03 |','| **Target Program** | NWP (Newport) |','| **Segment** | FV |','| **TPF** | '+tpf+' |','| **TCD** | '+tcd+' |','| **Status** | '+tc.get('status','')+' |','| **Val Environment** | '+env+' |','| **Automation** | '+cmd+' |','','---','','## Section A: NWP Disposition','','**Disposition: Runnable_On_NWP**','','Core C-states are fully supported on NWP (PantherCove PNC). NWP uses 2 CBBs (48 cores each). PkgC6 is ZBB. Adapt CBB loops: range(4)->range(2), core loops: range(64)->range(48).','']
    if sc: body+=['### Validation Scope','',sc,'']
    if pr: body+=['### Pre-Conditions','',pr,'']
    body+=['---','','## Section B: NWP Test Procedure','']
    if st: body+=['### Test Steps','',st,'']
    if hc: body+=['### Health Checks','',hc,'']
    if po: body+=['### Post-Process','',po,'']
    body+=['---','','## Section C: NWP Delta','','| Aspect | DMR | NWP | Impact |','|--------|-----|-----|--------|','| CBB count | Up to 4 | **2** | range(4)->range(2) |','| Cores/CBB | 64 | **48** | range(64)->range(48) |','| PkgC6 | Supported | **ZBB** | PC6 residency must stay 0 |','','---','','## Section F: References','']
    if rf: body+=[rf,'']
    body+=['- HSD TC: https://hsdes.intel.com/appstore/article-one/#/'+tid]
    fp.write_text('\n'.join(body),encoding='utf-8')
    created+=1
print('Created:',created,'  Total:',len(list(KB.glob('HSD_*.inference.md'))))
