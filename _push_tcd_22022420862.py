import re, sys
sys.path.insert(0, '.')
from hsd_utils import get_session
html = open('tcd_description_output/TCD_22022420862_pct_fuse_preview.html', encoding='utf-8').read()
m = re.search(r'<div class="desc-box">(.*?)</div>\s*</div>\s*</body>', html, re.DOTALL)
content = m.group(1).strip() if m else html
print('content len:', len(content))
s = get_session()
r = s.put('https://hsdes-api.intel.com/rest/article/22022420862',
    json={'subject': 'test_case_definition', 'tenant': 'server',
          'fieldValues': [{'description': content}, {'send_mail': 'false'}]})
print('HTTP', r.status_code)
if r.status_code != 200:
    print(r.text[:300])
