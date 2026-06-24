import re, sys, glob, pathlib
sys.path.insert(0, '.')
from hsd_utils import get_session

IDS = [
    ("16030715676", "pss_pct_all_hp_cores_in_c6"),
    ("16030715678", "pss_pct_bios_menu"),
    ("16030715680", "pss_pct_bios_negative_validation"),
    ("16030715684", "pss_pct_default_disabled"),
    ("16030715686", "pss_pct_default_hp_core_selection"),
    ("16030715682", "pss_pct_dq_rules_flexconpm"),
    ("16030715694", "pss_pct_enable_disable"),
    ("16030715690", "pss_pct_tpmi_register_check"),
    ("16030715692", "pss_pct_turbo_frequency_check"),
]

s = get_session()
results = []
for hsd_id, slug in IDS:
    html_path = f"tc_description_output/HSD_{hsd_id}_{slug}_tc_desc.html"
    html = open(html_path, encoding="utf-8").read()
    m = re.search(r'id="tc" class="panel active tc-content"(.*?)\n  </div>', html, re.DOTALL)
    content = m.group(1).strip() if m else html
    r = s.put(f"https://hsdes-api.intel.com/rest/article/{hsd_id}",
        json={"subject": "test_case", "tenant": "server",
              "fieldValues": [{"description": content}, {"send_mail": "false"}]})
    results.append((hsd_id, r.status_code, len(content)))
    print(f"{hsd_id}: HTTP {r.status_code} len={len(content)}")

ok = sum(1 for _,s,_ in results if s == 200)
print(f"\nSummary: {ok}/{len(IDS)} pushed OK")
