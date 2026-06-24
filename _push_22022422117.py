import re, sys
sys.path.insert(0, '.')
from hsd_utils import get_session
html = open('tc_description_output/HSD_22022422117_pct_verify_tdp_convergence_tc_desc.html', encoding='utf-8').read()
m = re.search(r'id="tc" class="panel active tc-content"(.*?)\n  </div>', html, re.DOTALL)
content = m.group(1).strip() if m else html
print('len:', len(content))
s = get_session()
r = s.put('https://hsdes-api.intel.com/rest/article/22022422117',
    json={'subject': 'test_case', 'tenant': 'server',
          'fieldValues': [{'description': content}, {'send_mail': 'false'}]})
print('HTTP', r.status_code)
