"""
Regenerate C-State inference.md files with correct section headings
by reading the structured HSD descriptions and converting to markdown.
"""
import json,re,pathlib,html,sys,time
sys.path.insert(0,'.')
from hsd_utils.session import get_session
from hsd_utils.queries import get_article

S=get_session()
KB=pathlib.Path('KB/pm_tc_kb/core_c_states/fv')
tcs=json.loads(pathlib.Path('nwp_pm_analysis/cstate_tcs.json').read_text(encoding='utf-8'))
if isinstance(tcs,dict): tcs=[tcs]
print(f'Processing {len(tcs)} TCs...')

def h2t(h):
    """Convert HTML section to clean text."""
    if not h: return ''
    t=re.sub(r'<br\s*/?>', '\n', h, flags=re.IGNORECASE)
    t=re.sub(r'<li[^>]*>', '\n- ', t, flags=re.IGNORECASE)
    t=re.sub(r'<tr[^>]*>', '\n', t, flags=re.IGNORECASE)
    t=re.sub(r'<td[^>]*>(.*?)</td>', lambda m: m.group(1).strip()+'  |  ', t, flags=re.IGNORECASE|re.DOTALL)
    t=re.sub(r'<th[^>]*>(.*?)</th>', lambda m: '**'+m.group(1).strip()+'**  |  ', t, flags=re.IGNORECASE|re.DOTALL)
    t=re.sub(r'<code[^>]*>(.*?)</code>', lambda m: '`'+m.group(1).strip()+'`', t, flags=re.IGNORECASE|re.DOTALL)
    t=re.sub(r'<strong[^>]*>(.*?)</strong>', lambda m: '**'+m.group(1).strip()+'**', t, flags=re.IGNORECASE|re.DOTALL)
    t=re.sub(r'<[^>]+>', '', t)
    t=html.unescape(t)
    t=re.sub(r'\n{3,}', '\n\n', t)
    return t.strip()

def xs(desc,label):
    """Extract section after a blue-header div with given label."""
    pat=r'background:#cce4f7[^>]*>[^<]*'+re.escape(label)+r'[^<]*</div>(.*?)(?=<div style="background:#cce4f7|$)'
    m=re.search(pat,desc,re.IGNORECASE|re.DOTALL)
    return h2t(m.group(1)) if m else ''

def slug(t): return re.sub(r'[^a-z0-9]+','_',t.lower())[:55].strip('_')

ok=0; fail=0
for tc in tcs:
    tid=str(tc.get('tc_id',''))
    title=tc.get('tc_title','')
    fn='HSD_'+tid+'_'+slug(title)+'.inference.md'
    fp=KB/fn

    # Fetch fresh description from HSD
    art=get_article(tid,'id,title,description,status,test_case.free_tag_2,test_case.val_environment,test_case.owner_team',session=S)
    desc=art.get('description','') or ''
    cmd=art.get('test_case.free_tag_2','') or tc.get('cmd','') or ''
    env=art.get('test_case.val_environment','') or tc.get('val_env','') or ''
    status=art.get('status','') or tc.get('status','')
    owner_team=art.get('test_case.owner_team','') or ''

    # Extract structured sections from HSD description
    scope_raw = xs(desc,'Validation Scope')
    prec_raw  = xs(desc,'Preconditions')
    steps_raw = xs(desc,'Test Steps')
    health_raw= xs(desc,'Health Check')
    post_raw  = xs(desc,'Post-Process')
    ref_raw   = xs(desc,'HAS Reference')

    # Build pre-conditions as markdown table
    prec_md=''
    if prec_raw:
        rows=[l for l in prec_raw.splitlines() if '|' in l and l.strip()]
        if rows:
            prec_md='| Item | Requirement |\n|------|-------------|\n'
            for row in rows:
                cells=[c.strip() for c in row.split('|') if c.strip() and c.strip() not in ('**Item**','**Requirement**','Item','Requirement','---')]
                if len(cells)>=2:
                    prec_md+=f'| {cells[0]} | {cells[1]} |\n'
        else:
            prec_md=prec_raw

    # Build test steps as numbered list or table from raw
    steps_md=steps_raw

    # Fallback: use inline desc text when sections are empty
    if not scope_raw:
        plain=re.sub(r'<[^>]+>','',desc or '').replace('&nbsp;',' ').strip()
        scope_raw=plain[:600] if plain else 'See HSD TC description.'

    intent=scope_raw or f'Validate {title} on NWP silicon/emulation.'
    tpf=tc.get('tpf_title','').replace('[NWP PM] ','')
    tcd=tc.get('tcd_title','')

    content=f'# Deep Analysis: {title}\n\n'
    content+=f'| Field | Value |\n|-------|-------|\n'
    content+=f'| **HSD ID** | {tid} |\n'
    content+=f'| **Title** | {title} |\n'
    content+=f'| **Date** | 2026-07-03 |\n'
    content+=f'| **Target Program** | NWP (Newport) |\n'
    content+=f'| **Segment** | FV |\n'
    content+=f'| **TPF** | {tpf} |\n'
    content+=f'| **TCD** | {tcd} |\n'
    content+=f'| **Status** | {status} |\n'
    content+=f'| **Val Environment** | {env} |\n'
    content+=f'| **Owner Team** | {owner_team} |\n'
    content+=f'| **Automation** | {cmd} |\n\n'
    content+='---\n\n'

    content+='## Test Case Intent\n\n'
    content+=intent+'\n\n'
    content+='---\n\n'

    content+='## Section A: NWP Disposition\n\n'
    content+='**Disposition: Runnable_On_NWP**\n\n'
    content+=f'Core C-states are fully supported on NWP (PantherCove PNC). This TC validates {title}. '
    content+='NWP has 2 CBBs × 48 cores (vs DMR up to 4 CBBs × 64 cores). PkgC6 is ZBB on NWP — PC6 residency must stay at 0.\n\n'
    content+='---\n\n'

    content+='## Section B: NWP Test Procedure\n\n'
    if prec_md:
        content+='### Pre-Conditions\n\n'+prec_md+'\n\n'
    if steps_md:
        content+='### Test Steps\n\n'+steps_md+'\n\n'
    if health_raw:
        content+='### Health Checks\n\n'+health_raw+'\n\n'
    if post_raw:
        content+='### Post-Process\n\n'+post_raw+'\n\n'

    content+='---\n\n'
    content+='## Section C: NWP Delta Impact\n\n'
    content+='| Aspect | DMR | NWP | Impact |\n|--------|-----|-----|--------|\n'
    content+='| CBB count | Up to 4 | **2** | Loop: range(4)→range(2) |\n'
    content+='| Cores per CBB | 64 | **48** | Loop: range(64)→range(48) |\n'
    content+='| PkgC6 | Supported | **ZBB** | PC6 residency must stay 0 |\n\n'
    content+='---\n\n'

    content+='### References\n\n'
    if ref_raw:
        content+=ref_raw+'\n'
    content+=f'- HSD TC: https://hsdes.intel.com/appstore/article-one/#/{tid}\n'
    content+='- Core C-state HAS, ACP PM HAS, Intel SDM\n'

    fp.write_text(content,encoding='utf-8')
    ok+=1
    if ok%10==0: print(f'  {ok}/{len(tcs)} done')
    time.sleep(0.18)

print(f'Regenerated: {ok}  Failed: {fail}')