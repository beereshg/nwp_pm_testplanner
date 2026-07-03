import sys,json,csv,time,pathlib,html as H
sys.path.insert(0,'.')
from hsd_utils.session import get_session, HSD_URL
from hsd_utils.queries import get_children, get_article
from collections import Counter
NWP_ROOT='22022534050'; SKIP={'22022561851'}
CACHE=pathlib.Path('nwp_pm_analysis/nwp_all_tc_raw.json')
CSV_OUT=pathlib.Path('nwp_pm_analysis/nwp_all_tc_cmdline_map.csv')
HTML_OUT=pathlib.Path('nwp_pm_analysis/nwp_all_tc_cmdline_map.html')
TC_F='id,title,status,from_id,test_case.free_tag_2,test_case.val_environment,test_case.automation,test_case.owner_team'
TR_F='id,title,status,updated_date,test_result.free_tag_2'
S=get_session()

def collect(force=False):
    if CACHE.exists() and not force:
        print('Cache hit'); d=json.loads(CACHE.read_text(encoding='utf-8')); return d['tcs']
    print('Walking NWP hierarchy...')
    tps=[tp for tp in get_children(NWP_ROOT,'test_plan','id,title,status',session=S) if str(tp.get('id','')) not in SKIP]
    print(f'  TPs: {len(tps)}')
    all_tcs=[]
    for tp in sorted(tps,key=lambda x:str(x.get('id',''))):
        tp_id=str(tp['id']); tp_t=tp.get('title','')
        print(f'  TP {tp_id}: {tp_t[:55]}')
        for tpf in get_children(tp_id,'test_plan','id,title',session=S):
            tpf_id=str(tpf['id']); tpf_t=tpf.get('title','')
            for tcd in get_children(tpf_id,'test_case_definition','id,title',session=S):
                tcd_id=str(tcd['id']); tcd_t=tcd.get('title','')
                for tc in get_children(tcd_id,'test_case',TC_F,session=S):
                    all_tcs.append({'nwp_tc_id':str(tc.get('id','')),'nwp_title':tc.get('title',''),'status':tc.get('status',''),
                        'tp_title':tp_t,'tpf_title':tpf_t,'tcd_title':tcd_t,
                        'from_id':str(tc.get('from_id','')) if tc.get('from_id') else '',
                        'nwp_cmd':tc.get('test_case.free_tag_2','') or '',
                        'val_env':tc.get('test_case.val_environment','') or '',
                        'automation':tc.get('test_case.automation','') or '',
                        'owner_team':tc.get('test_case.owner_team','') or ''})
                time.sleep(0.12)
            time.sleep(0.08)
        for tcd in get_children(tp_id,'test_case_definition','id,title',session=S):
            tcd_id=str(tcd['id']); tcd_t=tcd.get('title','')
            for tc in get_children(tcd_id,'test_case',TC_F,session=S):
                all_tcs.append({'nwp_tc_id':str(tc.get('id','')),'nwp_title':tc.get('title',''),'status':tc.get('status',''),
                    'tp_title':tp_t,'tpf_title':'(direct)','tcd_title':tcd_t,
                    'from_id':str(tc.get('from_id','')) if tc.get('from_id') else '',
                    'nwp_cmd':tc.get('test_case.free_tag_2','') or '',
                    'val_env':tc.get('test_case.val_environment','') or '',
                    'automation':tc.get('test_case.automation','') or '',
                    'owner_team':tc.get('test_case.owner_team','') or ''})
            time.sleep(0.12)
        print(f'    -> {len(all_tcs)} TCs so far')
    CACHE.write_text(json.dumps({'tcs':all_tcs},indent=2,ensure_ascii=False),encoding='utf-8')
    print(f'Cached {len(all_tcs)} TCs')
    return all_tcs

def enrich(tcs):
    print(f'Enriching {len(tcs)} TCs with DMR TR commands...')
    rows=[]
    for i,tc in enumerate(tcs):
        row=dict(tc); row.update({'dmr_tc_id':'','dmr_tc_title':'','tr_count':0,'dmr_tr_id':'','dmr_tr_date':'','dmr_cmd':'','all_dmr_cmds':'','match_type':'no-from-id'})
        fid=tc.get('from_id','')
        if fid:
            m=get_article(fid,'id,title',session=S)
            row['dmr_tc_id']=fid; row['dmr_tc_title']=m.get('title','') if m else ''
            trs=get_children(fid,'test_result',TR_F,session=S)
            if trs:
                ts=sorted(trs,key=lambda x:x.get('updated_date',''),reverse=True)
                row['tr_count']=len(ts); lat=ts[0]
                row['dmr_tr_id']=str(lat.get('id','')); row['dmr_tr_date']=(lat.get('updated_date','') or '')[:10]
                row['dmr_cmd']=lat.get('test_result.free_tag_2','') or ''
                cmds=sorted(set(t.get('test_result.free_tag_2','') for t in ts if t.get('test_result.free_tag_2','')))
                row['all_dmr_cmds']=' | '.join(cmds); row['match_type']='direct'
            else:
                row['match_type']='direct-no-tr'
            time.sleep(0.22)
        rows.append(row)
        if (i+1)%20==0: print(f'  {i+1}/{len(tcs)}')
    return rows

def write_csv(rows):
    cols=['tp_title','tpf_title','tcd_title','nwp_tc_id','nwp_title','status','val_env','automation','owner_team','nwp_cmd','from_id','dmr_tc_id','dmr_tc_title','tr_count','dmr_tr_id','dmr_tr_date','dmr_cmd','all_dmr_cmds','match_type']
    with open(CSV_OUT,'w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=cols,extrasaction='ignore'); w.writeheader(); w.writerows(rows)
    print(f'CSV: {CSV_OUT} ({len(rows)} rows)')

def write_html(rows):
    def e(s): return H.escape(str(s or ''))
    def lnk(id,lbl=None):
        if not id: return ''
        return f'<a href="{HSD_URL.format(id)}" target="_blank" class="hl">{e(lbl or id)}</a>'
    def badge(txt,c): return f'<span class="badge" style="background:{c}">{e(txt)}</span>'
    def mbadge(mt):
        return {'direct':badge('direct','#16a34a'),'direct-no-tr':badge('no-TR','#d97706'),'no-from-id':badge('no-link','#dc2626')}.get(mt,badge(mt,'#6b7280'))
    def cmd(c,all):
        if not c: return "<em style='color:#999'>-</em>"
        out=f'<code style="font-size:10px;word-break:break-all">{e(c)}</code>'
        if all:
            for x in all.split(' | '):
                if x and x!=c: out+=f'<div style="font-size:9px;color:#718096">* {e(x)}</div>'
        return out
    mc=Counter(r['match_type'] for r in rows); tpts=Counter(r['tp_title'] for r in rows)
    hrows=''.join(f'<tr data-tp="{e(r["tp_title"])}" data-mt="{e(r["match_type"])}"><td><span class="tpt">{e(r["tp_title"][:40])}</span></td><td style="font-size:10px">{e(r["tcd_title"][:45])}</td><td>{lnk(r["nwp_tc_id"])}<br/><span style="font-size:10px">{e(r["nwp_title"][:55])}</span></td><td style="font-size:10px">{e(r["val_env"])}</td><td class="cmd">{cmd(r["nwp_cmd"],"")}</td><td>{lnk(r["dmr_tc_id"])}{("<br/><span style=font-size:9px;color:#718096>"+e(r["dmr_tc_title"][:50])+"</span>") if r["dmr_tc_id"] else ""}</td><td>{lnk(r["dmr_tr_id"])}<br/><span style="font-size:9px;color:#718096">{e(r["dmr_tr_date"])}</span>{(" <b>"+str(r["tr_count"])+"TR</b>") if r["tr_count"] else ""}</td><td class="cmd">{cmd(r["dmr_cmd"],r["all_dmr_cmds"])}</td><td>{mbadge(r["match_type"])}</td></tr>' for r in rows)
    st_m=''.join(f'<tr><td>{e(k)}</td><td>{v}</td></tr>' for k,v in sorted(mc.items()))
    st_t=''.join(f'<tr><td>{e(k[:55])}</td><td>{v}</td></tr>' for k,v in sorted(tpts.items(),key=lambda x:-x[1]))
    tp_o=''.join(f'<option value="{e(t)}">{e(t[:55])}</option>' for t in sorted(tpts))
    mt_o=''.join(f'<option value="{e(k)}">{e(k)}</option>' for k in sorted(mc))
    page=f"""<!DOCTYPE html><html lang=en><head><meta charset=UTF-8><title>NWP PM TC Command Map</title>
<style>*{{box-sizing:border-box;margin:0;padding:0}}body{{font-family:"Segoe UI",Arial,sans-serif;background:#f0f4f9;font-size:12px;color:#1f2937}}
.hdr{{background:#0f4c81;color:#fff;padding:14px 28px}}.hdr h1{{font-size:18px;font-weight:600}}.hdr .sub{{font-size:11px;opacity:.8;margin-top:3px}}
.ctrl{{padding:10px 18px;background:#fff;border-bottom:1px solid #d9e2ec;display:flex;gap:10px;align-items:center;flex-wrap:wrap}}
.ctrl input,.ctrl select{{padding:5px 9px;border:1px solid #cbd5e0;border-radius:5px;font-size:12px}}.ctrl input{{width:280px}}
.wrap{{padding:10px 18px 40px}}.sg{{display:flex;gap:14px;margin-bottom:12px;flex-wrap:wrap}}
.sg table{{border-collapse:collapse;font-size:11px}}.sg th{{background:#374151;color:#fff;padding:4px 10px}}.sg td{{padding:4px 10px;border:1px solid #d1d5db}}
table.mt{{width:100%;border-collapse:collapse}}.mt th{{background:#1e3a8a;color:#fff;padding:6px 8px;text-align:left;font-size:11px;position:sticky;top:0;z-index:5}}
.mt td{{padding:5px 7px;border-bottom:1px solid #e2e8f0;vertical-align:top}}.mt tr:hover td{{background:#eff6ff}}
.tpt{{background:#e0e7ff;color:#3730a3;padding:1px 5px;border-radius:6px;font-size:10px;font-weight:600;white-space:nowrap}}
.cmd{{max-width:200px;word-break:break-all;font-family:Consolas,monospace;font-size:10px;background:#fafafa}}
.hl{{color:#1a56db;text-decoration:none;font-family:Consolas,monospace;font-size:11px}}.hl:hover{{text-decoration:underline}}
.badge{{color:#fff;padding:1px 7px;border-radius:8px;font-size:10px;font-weight:600}}</style></head>
<body><div class=hdr><h1>NWP PM - Full TC to DMR TR Command Line Mapping</h1>
<div class=sub>Root:{NWP_ROOT} &bull; {len(rows)} NWP TCs across {len(tpts)} TPs &bull; from_id chain to DMR TRs &bull; 2026-07-02</div></div>
<div class=ctrl><input type=text id=q placeholder="Search TC ID, title, command..." oninput=doFilter()>
<select id=tp onchange=doFilter()><option value="">All TPs</option>{tp_o}</select>
<select id=mt onchange=doFilter()><option value="">All match types</option>{mt_o}</select>
<label><input type=checkbox id=cmd onchange=doFilter()> Has DMR command</label>
<span style="margin-left:auto;font-size:11px;color:#718096" id=sb></span></div>
<div class=wrap><div class=sg><table><tr><th>Match</th><th>Count</th></tr>{st_m}</table>
<table><tr><th>TP</th><th>TCs</th></tr>{st_t}</table></div>
<table class=mt id=T><thead><tr><th>TP</th><th>TCD</th><th>NWP TC</th><th>Val Env</th><th>NWP Cmd</th><th>DMR TC</th><th>DMR TR</th><th>DMR Cmd</th><th>Match</th></tr></thead>
<tbody id=TB>{hrows}</tbody></table></div>
<script>function doFilter(){{var q=document.getElementById('q').value.toLowerCase(),tp=document.getElementById('tp').value,mt=document.getElementById('mt').value,cmdOnly=document.getElementById('cmd').checked,rows=document.querySelectorAll('#TB tr'),shown=0;rows.forEach(function(r){{var txt=r.textContent.toLowerCase(),rtp=r.getAttribute('data-tp'),rmt=r.getAttribute('data-mt'),hasDmr=r.querySelector('td:nth-child(8) code')!==null;var ok=(!q||txt.includes(q))&&(!tp||rtp===tp)&&(!mt||rmt===mt)&&(!cmdOnly||hasDmr);r.style.display=ok?'':'none';if(ok)shown++}});document.getElementById('sb').textContent='Showing '+shown+'/'+rows.length+' TCs'}}window.addEventListener('load',doFilter)</script>
</body></html>"""
    HTML_OUT.write_bytes(page.encode('utf-8'))
    print(f'HTML: {HTML_OUT} ({HTML_OUT.stat().st_size} bytes)')

if __name__=='__main__':
    import sys
    force='--refresh' in sys.argv
    tcs=collect(force)
    print(f'Total NWP TCs: {len(tcs)}')
    rows=enrich(tcs)
    mc=Counter(r['match_type'] for r in rows)
    print('Match summary:',dict(mc))
    write_csv(rows); write_html(rows)
    print('Done.')
