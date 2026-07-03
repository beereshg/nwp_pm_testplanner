import pathlib, json, time, re, sys
sys.path.insert(0,".")
from hsd_utils.session import get_session, TENANT
from hsd_utils.queries import get_article
from hsd_utils.operations import set_field, create_article

sess = get_session()
TODAY = time.strftime("%Y-%m-%d")
out   = pathlib.Path("tcd_description_output")

TCD_IDS = [
    "22022421247","22022421250","22022421253","22022421257",
    "22022421276","22022421287","22022421266","22022421260",
    "22022421289","22022421293","22022421307"
]
print(f"TCDs to push: {len(TCD_IDS)}")

def extract_desc_box(html_path):
    html = html_path.read_text(encoding="utf-8")
    # Greedy match: everything inside <div class="desc-box">...</div>
    m = re.search(r'<div class="desc-box">(.*)</div>\s*</div>\s*</body>', html, re.DOTALL)
    if m:
        return m.group(1).strip()
    raise ValueError(f"desc-box not found in {html_path.name}")

ok = err = skip = 0
results = []

for tid in TCD_IDS:
    matches = list(out.glob(f"TCD_{tid}_*.html"))
    if not matches:
        print(f"  SKIP {tid}: no preview HTML")
        skip += 1; results.append({"id":tid,"status":"skip"}); continue
    html_path = matches[0]
    try:
        new_desc   = extract_desc_box(html_path)
        orig       = get_article(tid, fields="description,title", session=sess)
        orig_title = orig.get("title", tid)
        orig_desc  = orig.get("description","") or "(empty)"
        # Backup original as comment
        comment_fv = [
            {"parent_id": int(tid)},
            {"title": f"[val_agent {TODAY}] original description backup"},
            {"description": orig_desc},
            {"send_mail": "false"},
        ]
        create_article("comments", comment_fv, session=sess)
        # Update TCD description (subject = test_case_definition)
        code = set_field(tid, "test_case_definition", "description", new_desc, session=sess)
        if code in (200, 201):
            ok += 1
            print(f"  OK [{ok:2d}] {tid}: {orig_title[:70]}  (HTTP {code})")
            results.append({"id":tid,"status":"ok","title":orig_title,"http":code})
        else:
            raise RuntimeError(f"PUT returned HTTP {code}")
        time.sleep(0.5)
    except Exception as e:
        err += 1
        print(f"  ERR {tid}: {e}")
        results.append({"id":tid,"status":"error","msg":str(e)})

print(f"\nSummary: {ok} updated | {skip} skipped | {err} errors")
pathlib.Path("nwp_pm_analysis/cstate_tcd_hsd_push_results.json").write_text(
    json.dumps(results, indent=2), encoding="utf-8")