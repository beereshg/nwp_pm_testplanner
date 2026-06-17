"""
Recursive hierarchy walker: TP → TPF → TCD → TC.

Returns structured data (plain dicts) that can be passed directly to
``hsd_utils.html_gen`` or processed by any other consumer.

Cache helpers
-------------
Use ``save_cache(path, root_id, root_info, hierarchy, tc_stats)`` to persist
a fetched hierarchy to a JSON file, and ``load_cache(path)`` to restore it.
This separates the slow HSD network fetch from fast HTML re-renders.
"""
from __future__ import annotations
import json
import os
from datetime import datetime, timezone
from typing import Any

import requests

from .queries import get_article, get_children
from .session import get_session

# Type alias for the nested node dict
HierarchyNode = dict[str, Any]


# ── Cache helpers ─────────────────────────────────────────────────────────────

def save_cache(
    path: str,
    root_id: str,
    root_info: HierarchyNode,
    hierarchy: list[HierarchyNode],
    tc_stats: list[tuple[str, str]],
) -> None:
    """Persist hierarchy data to a JSON file.

    The cache stores a timestamp so callers can display how fresh the data is.
    """
    payload = {
        "_meta": {
            "root_id":   root_id,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        },
        "root_info": root_info,
        "hierarchy": hierarchy,
        "tc_stats":  tc_stats,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    print(f"Cache saved: {path}")


def load_cache(
    path: str,
) -> tuple[str, HierarchyNode, list[HierarchyNode], list[tuple[str, str]], str]:
    """Load hierarchy data from a JSON cache file.

    Returns ``(root_id, root_info, hierarchy, tc_stats, fetched_at)``.
    Raises ``FileNotFoundError`` if the cache does not exist.
    """
    with open(path, encoding="utf-8") as f:
        payload = json.load(f)
    meta        = payload["_meta"]
    root_id     = meta["root_id"]
    fetched_at  = meta.get("fetched_at", "unknown")
    root_info   = payload["root_info"]
    hierarchy   = payload["hierarchy"]
    tc_stats    = [tuple(x) for x in payload["tc_stats"]]
    return root_id, root_info, hierarchy, tc_stats, fetched_at


def walk_hierarchy(
    root_id: str | int,
    skip_ids: set[str] | None = None,
    session: requests.Session | None = None,
    verbose: bool = True,
) -> tuple[HierarchyNode, list[HierarchyNode], list[tuple[str, str]]]:
    """Walk the TP → TPF → TCD → TC hierarchy under *root_id*.

    Parameters
    ----------
    root_id:
        HSD article ID of the root folder / parent TP.
    skip_ids:
        Optional set of article ID strings to exclude at the TP level
        (e.g. deprecated nodes).
    session:
        Reuse an existing requests.Session.  A new Kerberos session is
        created when omitted.
    verbose:
        Print progress lines to stdout.

    Returns
    -------
    root_info : dict
        Article metadata for *root_id* (id, title, owner, status).
    hierarchy : list[dict]
        One entry per TP; each entry has keys:
        ``id, title, owner, status, tpfs, direct_tcds``
        where *tpfs* is a list of TPF dicts (each with ``tcds`` list)
        and *direct_tcds* holds TCDs hanging directly on the TP.
    tc_stats : list[tuple[str, str]]
        Flat list of ``(owner, status)`` for every TC encountered;
        useful for summary statistics.
    """
    s = session or get_session()
    skip = {str(x) for x in (skip_ids or set())}
    tc_stats: list[tuple[str, str]] = []

    if verbose:
        print(f"Fetching hierarchy from root {root_id}...")

    root_info = get_article(root_id, session=s)

    raw_tps = [
        tp for tp in get_children(root_id, "test_plan", session=s)
        if str(tp.get("id", "")) not in skip
    ]
    if verbose:
        excl = f" ({len(skip)} excluded)" if skip else ""
        print(f"  TPs: {len(raw_tps)}{excl}")

    hierarchy: list[HierarchyNode] = []
    for tp in sorted(raw_tps, key=lambda x: int(x["id"])):
        tp_node = _make_node(tp)
        if verbose:
            print(f"  TP {tp_node['id']}: {tp_node['title']}")

        for tpf in sorted(get_children(tp_node["id"], "test_plan", session=s),
                          key=lambda x: int(x["id"])):
            tpf_node = _make_node(tpf)
            if verbose:
                print(f"    TPF {tpf_node['id']}: {tpf_node['title']}")

            for tcd in sorted(get_children(tpf_node["id"], "test_case_definition", session=s),
                               key=lambda x: int(x["id"])):
                tcd_node = _make_node(tcd)
                _attach_tcs(tcd_node, tc_stats, s)
                tpf_node["tcds"].append(tcd_node)

            tp_node["tpfs"].append(tpf_node)

        # TCDs attached directly on the TP (no intervening TPF)
        for tcd in sorted(get_children(tp_node["id"], "test_case_definition", session=s),
                           key=lambda x: int(x["id"])):
            tcd_node = _make_node(tcd)
            _attach_tcs(tcd_node, tc_stats, s)
            tp_node["direct_tcds"].append(tcd_node)

        hierarchy.append(tp_node)

    if verbose:
        print(f"\nTotal TCs collected: {len(tc_stats)}")

    return root_info, hierarchy, tc_stats


# ── Internal helpers ──────────────────────────────────────────────────────────

def _make_node(raw: dict[str, Any]) -> HierarchyNode:
    return {
        "id":     str(raw.get("id", "?")),
        "title":  raw.get("title", "?"),
        "owner":  raw.get("owner", "?"),
        "status": raw.get("status", "?"),
        "tpfs":        [],   # populated for TP nodes
        "tcds":        [],   # populated for TPF nodes
        "tcs":         [],   # populated for TCD nodes
        "direct_tcds": [],   # populated for TP nodes (TCDs without a TPF)
    }


def _attach_tcs(
    tcd_node: HierarchyNode,
    tc_stats: list[tuple[str, str]],
    session: requests.Session,
) -> None:
    for tc in sorted(
        get_children(tcd_node["id"], "test_case",
                     fields="id,title,owner,status,test_case.val_framework",
                     session=session),
        key=lambda x: int(x["id"]),
    ):
        owner  = str(tc.get("owner",  "?"))
        status = str(tc.get("status", "?"))
        tcd_node["tcs"].append({
            "id":            str(tc.get("id", "?")),
            "title":         tc.get("title", "?"),
            "owner":         owner,
            "status":        status,
            "val_framework": tc.get("test_case.val_framework") or "",
        })
        tc_stats.append((owner, status))
