"""
Generate hierarchical HTML for the NWP PM PSS test plan hierarchy.
Root folder: 22021969825 (Phoenix PM folder, family=Newport).

Usage
-----
    python tools/hierarchy/gen_pss_hierarchy_html.py
    python tools/hierarchy/gen_pss_hierarchy_html.py --fetch

Outputs now live under nwp_pm_analysis/hierarchy/.
"""
import argparse
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from hsd_utils import walk_hierarchy, save_cache, load_cache, generate_pss_html

ROOT        = "22021969825"
PHOENIX_URL = (
    "https://hsdes.intel.com/appstore/phoenix/my-items"
    "?wf=22011658183&wfs=22011658203&gn=1&gn=0"
    "&v=server.test_plan&family=Newport&family_group=NEWPORT"
    "&scope=product&folder=Base&projectId=22020919772"
    "&role=2&uFolder=22021969825"
)
OUTPUT_DIR  = REPO_ROOT / "nwp_pm_analysis" / "hierarchy"
CACHE_FILE  = OUTPUT_DIR / "nwp_pm_pss_cache.json"
OUTPUT      = OUTPUT_DIR / "nwp_pm_pss_hierarchy.html"

def main():
    ap = argparse.ArgumentParser(description="Generate NWP PM PSS hierarchy HTML")
    ap.add_argument("--fetch", action="store_true",
                    help="Force a fresh HSD fetch and update the JSON cache")
    ap.add_argument("--cache", default=CACHE_FILE, metavar="PATH",
                    help=f"JSON cache file (default: {CACHE_FILE})")
    ap.add_argument("--output", default=OUTPUT, metavar="PATH",
                    help=f"Output HTML file (default: {OUTPUT})")
    args = ap.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    cache_path = args.cache

    if not args.fetch and os.path.exists(cache_path):
        print(f"Loading cached hierarchy from {cache_path}")
        root_id, root_info, hierarchy, tc_stats, fetched_at = load_cache(cache_path)
        print(f"  (fetched: {fetched_at},  TCs: {len(tc_stats)})")
    else:
        if not args.fetch and not os.path.exists(cache_path):
            print(f"No cache found at {cache_path} -- fetching from HSD...")
        else:
            print("--fetch flag set -- fetching fresh data from HSD...")
        root_info, hierarchy, tc_stats = walk_hierarchy(ROOT)
        save_cache(cache_path, ROOT, root_info, hierarchy, tc_stats)

    generate_pss_html(ROOT, root_info, hierarchy, tc_stats,
                      output_path=args.output,
                      phoenix_url=PHOENIX_URL)

if __name__ == "__main__":
    main()
