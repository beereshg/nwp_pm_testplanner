"""
Read-only HSD REST API helpers: article fetch, children listing, EQL query.

All functions accept an optional ``session`` argument.  When omitted a fresh
Kerberos session is created automatically (useful for one-off calls in scripts
that already have their own session lifecycle).
"""
from __future__ import annotations
from typing import Any

import requests

from .session import BASE, TENANT, get_session

_DEFAULT_FIELDS = "id,title,owner,status"


def get_article(
    art_id: str | int,
    fields: str = "id,title,owner,status,parent_id",
    session: requests.Session | None = None,
) -> dict[str, Any]:
    """Fetch a single article by ID.

    Returns the first data element or an empty dict on failure.
    """
    s = session or get_session()
    r = s.get(
        f"{BASE}/article/{art_id}",
        params={"fields": fields, "tenant": TENANT},
    )
    if r.ok:
        data = r.json().get("data", [{}])
        return data[0] if data else {}
    return {}


def get_children(
    parent_id: str | int,
    child_subject: str,
    fields: str = _DEFAULT_FIELDS,
    max_results: int = 500,
    session: requests.Session | None = None,
) -> list[dict[str, Any]]:
    """Return all direct children of *parent_id* with the given subject type.

    Examples::

        get_children("22022534050", "test_plan")          # domain TPs
        get_children(tp_id, "test_case_definition")       # TCDs under a TP
        get_children(tcd_id, "test_case")                 # TCs under a TCD
    """
    s = session or get_session()
    r = s.get(
        f"{BASE}/article/{parent_id}/children",
        params={
            "child_subject": child_subject,
            "tenant": TENANT,
            "fields": fields,
            "max_results": max_results,
        },
    )
    return r.json().get("data", []) if r.ok else []


def query_driven(
    q: str,
    session: requests.Session | None = None,
) -> list[dict[str, Any]]:
    """Execute an EQL driven-query and return the data list.

    Example::

        query_driven("select id,title from server.test_plan where parent_id='22022534050'")
    """
    s = session or get_session()
    r = s.get(f"{BASE}/query/driven", params={"q": q})
    return r.json().get("data", []) if r.ok else []
