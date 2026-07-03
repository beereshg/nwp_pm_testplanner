import pathlib, json, time, sys
sys.path.insert(0, ".")
from hsd_utils.session import get_session, TENANT
from hsd_utils.queries import get_article
from hsd_utils.operations import set_field, create_article

tc_dir = pathlib.Path("tc_description_output")
tcs    = json.loads(pathlib.Path("nwp_pm_analysis/cstate_tcs.json").read_text())
ids    = [str(x["tc_id"]) for x in tcs]
TODAY  = time.strftime("%Y-%m-%d")
print(f"TCs to push: {len(ids)}")

sess = get_session()

def extract_desc(html_path):
    html = html_path.read_text(encoding="utf-8")
    si = html.index("<div style=\"font-family")
    i, depth = si, 0
    while i < len(html):
        if html[i:i+4] == "<div": depth += 1; i += 4
        elif html[i:i+6] == "</div>":
            depth -= 1
            if depth == 0: return html[si:i+6]
            i += 6
        else: i += 1
    return html[si:]

ok = err = skip = 0
results = []

for tid in ids:
    matches = list(tc_dir.glob(f"HSD_{tid}_*.html"))
    if not matches:
        print(f"  SKIP {tid}: no HTML")
        skip += 1; results.append({"id":tid,"status":"skip"}); continue
    html_path = matches[0]
    try:
        new_desc   = extract_desc(html_path)
        orig       = get_article(tid, fields="description,title", session=sess)
        orig_desc  = orig.get("description","") or "(empty)"
        orig_title = orig.get("title", tid)
        # Backup original as comment
        comment_fv = [
            {"parent_id": int(tid)},
            {"title": f"[val_agent {TODAY}] original description backup"},
            {"description": orig_desc},
            {"send_mail": "false"},
        ]
        create_article("comments", comment_fv, session=sess)
        # Update description
        code = set_field(tid, "test_case", "description", new_desc, session=sess)
        if code in (200, 201):
            ok += 1
            print(f"  OK [{ok:2d}] {tid}: {orig_title[:70]}")
            results.append({"id":tid,"status":"ok","title":orig_title,"http":code})
        else:
            raise RuntimeError(f"PUT returned HTTP {code}")
        time.sleep(0.4)
    except Exception as e:
        err += 1
        print(f"  ERR {tid}: {e}")
        results.append({"id":tid,"status":"error","msg":str(e)})

print(f"\nSummary: {ok} updated | {skip} skipped | {err} errors")
pathlib.Path("nwp_pm_analysis/cstate_hsd_push_results.json").write_text(
    json.dumps(results, indent=2), encoding="utf-8")