"""
hsd_utils — shared HSD REST API helpers for NWP testplan scripts.

Quick-start
-----------
::

    from hsd_utils import get_session, get_article, get_children
    from hsd_utils import move_tcd, move_and_verify, set_field, create_article
    from hsd_utils import classify_tcd
    from hsd_utils import walk_hierarchy
    from hsd_utils import generate_fv_html, generate_pss_html
    
    # NEW: Batch operations for multi-TC analysis
    from hsd_utils.batch_ops import fetch_batch, traverse_hierarchy
    from hsd_utils.batch_ops import compare_tps, analyze_batch, status_report

Module summary
--------------
session.py    — get_session(), BASE, TENANT, HSD_URL
queries.py    — get_article(), get_children(), query_driven()
operations.py — move_tcd(), move_and_verify(), set_field(), set_owner(),
                append_tag(), set_planning_fields(), create_article(),
                classify_tcd(), get_parent()
hierarchy.py  — walk_hierarchy()
html_gen.py   — generate_fv_html(), generate_pss_html()
batch_ops.py  — fetch_batch(), traverse_hierarchy(), compare_tps(),
                analyze_batch(), filter_batch(), status_report()
"""
from .session    import BASE, TENANT, HSD_URL, get_session
from .queries    import get_article, get_children, query_driven
from .operations import (
    get_parent,
    move_tcd,
    move_and_verify,
    run_move_plan,
    set_field,
    set_owner,
    get_tag,
    append_tag,
    set_planning_fields,
    create_article,
    classify_tcd,
)
from .hierarchy  import walk_hierarchy, save_cache, load_cache
from .html_gen   import generate_fv_html, generate_pss_html
from .batch_ops  import fetch_batch, traverse_hierarchy, compare_tps, analyze_batch, filter_batch, status_report

__all__ = [
    # constants
    "BASE", "TENANT", "HSD_URL",
    # session
    "get_session",
    # queries
    "get_article", "get_children", "query_driven",
    # operations
    "get_parent", "move_tcd", "move_and_verify", "run_move_plan",
    "set_field", "set_owner",
    "get_tag", "append_tag",
    "set_planning_fields",
    "create_article",
    "classify_tcd",
    # hierarchy
    "walk_hierarchy", "save_cache", "load_cache",
    # html
    "generate_fv_html", "generate_pss_html",
    # batch_ops — NEW
    "fetch_batch", "traverse_hierarchy", "compare_tps",
    "analyze_batch", "filter_batch", "status_report",
]
