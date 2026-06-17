"""Batch HSD operations for fetch, hierarchy traversal, and analysis."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, Iterable, List, Optional

import requests

from .queries import get_article, get_children
from .session import get_session


_FIELDS_DEFAULT = "id,title,status,owner,parent_id"
_FIELDS_TCS = "id,title,status,owner,parent_id,test_case.val_environment,test_case.val_framework"


def _safe_children(
    parent_id: str,
    child_subject: str,
    fields: str,
    session: requests.Session,
    max_results: int = 1000,
) -> list[dict[str, Any]]:
    """Fetch children for a specific subject and normalize None -> empty list."""
    children = get_children(
        parent_id,
        child_subject=child_subject,
        fields=fields,
        max_results=max_results,
        session=session,
    )
    return children or []


def _iter_tcds_under_tpv(
    tpv_id: str,
    session: requests.Session,
) -> Iterable[dict[str, Any]]:
    """Yield TCDs directly under TPV and under nested TPFs (one level)."""
    # Direct TCDs under TPV
    for tcd in _safe_children(tpv_id, "test_case_definition", _FIELDS_DEFAULT, session):
        yield tcd

    # Nested TPFs under TPV and their TCDs
    nested_tpfs = _safe_children(tpv_id, "test_plan", _FIELDS_DEFAULT, session)
    for nested_tpf in nested_tpfs:
        nested_tpf_id = str(nested_tpf.get("id", ""))
        if not nested_tpf_id:
            continue
        for tcd in _safe_children(nested_tpf_id, "test_case_definition", _FIELDS_DEFAULT, session):
            yield tcd


def fetch_batch(
    ids: List[str],
    session: Optional[requests.Session] = None,
) -> Dict[str, Dict[str, Any]]:
    """Fetch multiple HSD articles. Returns a dict keyed by article ID."""
    active_session = session or get_session()
    results: Dict[str, Dict[str, Any]] = {}
    for art_id in ids:
        article = get_article(art_id, session=active_session)
        if article:
            results[str(art_id)] = article
    return results


def traverse_hierarchy(
    root_id: str,
    depth: str = "full",
    session: Optional[requests.Session] = None,
) -> Dict[str, Any]:
    """Traverse TP -> TPF -> TCD -> TC hierarchy for a given root ID.

    Depth options:
      - ``TP+TPV``: returns root + direct TPFs under TP
      - ``TP+TPV+TCD``: includes TCDs under each TPF
      - ``full``: includes TCs under each TCD
    """
    active_session = session or get_session()
    root = get_article(root_id, session=active_session)
    if not root:
        return {}

    result: Dict[str, Any] = {"root": root, "tpvs": [], "tcds": [], "tcs": []}

    if depth in ["TP+TPV", "TP+TPV+TCD", "full"]:
        tpvs = _safe_children(
            str(root_id),
            child_subject="test_plan",
            fields=_FIELDS_DEFAULT,
            session=active_session,
        )
        result["tpvs"] = tpvs

        if depth in ["TP+TPV+TCD", "full"]:
            for tpv in result["tpvs"]:
                tpv_id = str(tpv.get("id", ""))
                if not tpv_id:
                    continue

                tcds = list(_iter_tcds_under_tpv(tpv_id, active_session))
                result["tcds"].extend(tcds)

                if depth == "full":
                    for tcd in tcds:
                        tcd_id = str(tcd.get("id", ""))
                        if not tcd_id:
                            continue
                        tcs = _safe_children(
                            tcd_id,
                            child_subject="test_case",
                            fields=_FIELDS_TCS,
                            session=active_session,
                        )
                        result["tcs"].extend(tcs)

    return result


def analyze_batch(
    articles: List[Dict[str, Any]],
    group_by: Optional[List[str]] = None,
) -> Dict[str, Dict[str, int]]:
    """Group article counts by one or more fields."""
    fields = group_by or ["status"]
    grouped = {field: defaultdict(int) for field in fields}

    for article in articles:
        for field in fields:
            key = str(article.get(field, "unknown"))
            grouped[field][key] += 1

    return {field: dict(values) for field, values in grouped.items()}


def compare_tps(
    tp_id_1: str,
    tp_id_2: str,
    key: str = "title",
    session: Optional[requests.Session] = None,
) -> Dict[str, Any]:
    """Compare two TP hierarchies by a chosen TC field."""
    active_session = session or get_session()
    hierarchy_1 = traverse_hierarchy(tp_id_1, depth="full", session=active_session)
    hierarchy_2 = traverse_hierarchy(tp_id_2, depth="full", session=active_session)

    set_1 = {article.get(key) for article in hierarchy_1.get("tcs", []) if article.get(key)}
    set_2 = {article.get(key) for article in hierarchy_2.get("tcs", []) if article.get(key)}

    return {
        "tp1_only": sorted(set_1 - set_2),
        "tp2_only": sorted(set_2 - set_1),
        "overlap": sorted(set_1 & set_2),
        "tp1_count": len(set_1),
        "tp2_count": len(set_2),
        "overlap_count": len(set_1 & set_2),
    }


def filter_batch(articles: List[Dict[str, Any]], **kwargs: Any) -> List[Dict[str, Any]]:
    """Filter articles by exact field-value matches."""
    filtered = articles
    for field, value in kwargs.items():
        filtered = [article for article in filtered if str(article.get(field)) == str(value)]
    return filtered


def status_report(hierarchy: Dict[str, Any]) -> str:
    """Generate a compact text status report for a hierarchy."""
    root = hierarchy.get("root", {})
    tpvs = hierarchy.get("tpvs", [])
    tcds = hierarchy.get("tcds", [])
    tcs = hierarchy.get("tcs", [])

    tc_by_status: Dict[str, int] = defaultdict(int)
    for tc in tcs:
        tc_by_status[str(tc.get("status", "unknown"))] += 1

    lines = [
        f"TP {root.get('id')} - {root.get('title')}",
        f"  TPVs: {len(tpvs)}, TCDs: {len(tcds)}, TCs: {len(tcs)}",
    ]

    if tcs:
        lines.append("  TC Status:")
        for status in sorted(tc_by_status.keys()):
            count = tc_by_status[status]
            pct = int(count * 100 / len(tcs)) if tcs else 0
            lines.append(f"    {status}: {count} ({pct}%)")

    return "\n".join(lines)