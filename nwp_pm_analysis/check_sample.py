import json,re,pathlib,sys
sys.path.insert(0,'.')
from hsd_utils.session import get_session
from hsd_utils.queries import get_article
S=get_session()
tcs=json.loads(pathlib.Path('nwp_pm_analysis/proposal_tcs.json').read_text(encoding='utf-8'))
if isinstance(tcs,dict): tcs=[tcs]
for tc in tcs[:5]:
    tid=str(tc.get('nwp_tc_id',''))
    art=get_article(tid,'id,title,description',session=S)
    desc=art.get('description','') or ''
    codes=re.findall(r'<code[^>]*>([^<]{3,})</code>',desc,re.IGNORECASE)
    nc=tc.get('nwp_cmd',''); dc=tc.get('dmr_cmd','')
    print(f'TC {tid}:')
    print(f'  nwp_cmd = {nc[:50]}')
    print(f'  dmr_cmd = {dc[:50]}')
    print(f'  desc codes = {codes[:6]}')
    print()
