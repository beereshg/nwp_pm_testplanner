import re, sys
sys.path.insert(0, '.')
from hsd_utils import get_session

TCS = [
    ("22022060649", "Power-RAPL_Socket_RAPL"),
    ("22022060651", "Power-RAPL_Socket_RAPL"),
    ("22022060654", "Power-RAPL_Memory_PM"),
]
s = get_session()
for hsd_id, slug in TCS:
    html = open(f"tc_description_output/HSD_{hsd_id}_{slug}_tc_desc.html", encoding="utf-8").read()
    m = re.search(r'id="tc" class="panel active tc-content"(.*?)\n  </div>', html, re.DOTALL)
    content = m.group(1).strip() if m else html
    r = s.put(f"https://hsdes-api.intel.com/rest/article/{hsd_id}",
        json={"subject": "test_case", "tenant": "server",
              "fieldValues": [{"description": content}, {"send_mail": "false"}]})
    print(f"{hsd_id}: HTTP {r.status_code} len={len(content)}")
