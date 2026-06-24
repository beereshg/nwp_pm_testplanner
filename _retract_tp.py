import sys, re, time
sys.path.insert(0, '.')
from hsd_utils import get_session, get_children

BASE = 'https://hsdes-api.intel.com/rest'
TP   = '16030762839'
RETRACTION = '<p>[retracted by author]</p>'

s = get_session()

def is_grading(desc):
    text = re.sub(r'<[^>]+>', ' ', desc or '')
    text = re.sub(r'\s+', ' ', text).strip()
    return bool(re.match(r'TC\s+Grad', text, re.I))

retracted = []
skipped   = []
errors    = []

# Walk TP -> TPF -> TCD -> TC
tpfs = get_children(TP, 'test_plan', fields='id,title', session=s)
print(f'TPFs: {len(tpfs)}')

for tpf in tpfs:
    tcds = get_children(tpf['id'], 'test_case_definition', fields='id,title', session=s)
    for tcd in tcds:
        tcs = get_children(tcd['id'], 'test_case', fields='id,title,status', session=s)
        for tc in tcs:
            if 'rejected' in tc.get('status','').lower():
                continue
            tc_id = tc['id']
            comments = get_children(tc_id, 'comment',
                fields='id,owner,description', max_results=30, session=s)
            for c in comments:
                if is_grading(c.get('description','')):
                    r = s.put(f'{BASE}/article/{c["id"]}', json={
                        'tenant': 'server', 'subject': 'comments',
                        'fieldValues': [{'description': RETRACTION}, {'send_mail': 'false'}]
                    }, timeout=30)
                    if r.status_code == 200:
                        retracted.append((tc_id, c['id']))
                        print(f'  RETRACTED tc={tc_id} comment={c["id"]}')
                    else:
                        errors.append((tc_id, c['id'], r.status_code))
                        print(f'  ERROR     tc={tc_id} comment={c["id"]} HTTP {r.status_code}')
                    time.sleep(0.3)
            time.sleep(0.05)

print(f'\nDone. Retracted: {len(retracted)}  Errors: {len(errors)}')
