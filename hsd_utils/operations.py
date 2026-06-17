"""
Write operations against the HSD REST API: move, field-update, create, tag.

All functions return the HTTP status code so callers can decide how to handle
failures.  A status code of 200 or 201 means success; anything else is an error.

Planning-field quirk: ``planning_status`` and ``drive_to_date`` on
``server.test_case`` require *two separate PUT calls* — a combined PUT returns
400.  Use ``set_field`` twice or call ``set_planning_fields`` which handles
the two-shot pattern automatically.
"""
from __future__ import annotations
from typing import Any

import requests

from .session import BASE, TENANT, get_session
from .queries import get_article


# ── Low-level helpers ─────────────────────────────────────────────────────────

def get_parent(art_id: str | int, session: requests.Session | None = None) -> str | None:
    """Return the ``parent_id`` field of an article, or None on failure."""
    a = get_article(art_id, fields="id,parent_id", session=session)
    return str(a["parent_id"]) if a.get("parent_id") else None


def set_field(
    art_id: str | int,
    subject: str,
    field: str,
    value: Any,
    session: requests.Session | None = None,
) -> int:
    """PUT a single field update on an article.  Returns HTTP status code.

    ``send_mail: false`` is included in fieldValues to suppress email
    notifications.  Note: send_mail as a *top-level* body key causes HTTP 400;
    it must be inside fieldValues.
    """
    s = session or get_session()
    body = {
        "subject": subject,
        "tenant": TENANT,
        "fieldValues": [{field: value}, {"send_mail": "false"}],
    }
    r = s.put(f"{BASE}/article/{art_id}", json=body)
    return r.status_code


# ── TCD movement ──────────────────────────────────────────────────────────────

def move_tcd(
    tcd_id: str | int,
    target_tpf_id: str | int,
    session: requests.Session | None = None,
) -> int:
    """Move a test_case_definition to a different parent TPF.  Returns HTTP status code."""
    return set_field(tcd_id, "test_case_definition", "parent_id", str(target_tpf_id), session)


def move_and_verify(
    tcd_id: str | int,
    target_tpf_id: str | int,
    session: requests.Session | None = None,
) -> bool:
    """Move a TCD and verify the parent changed.  Returns True on success."""
    s = session or get_session()
    tcd_id = str(tcd_id)
    target = str(target_tpf_id)
    status = move_tcd(tcd_id, target, s)
    if status not in (200, 201):
        print(f"    ❌ {tcd_id} → {target}: HTTP {status}")
        return False
    actual = get_parent(tcd_id, s)
    if actual == target:
        print(f"    ✅ {tcd_id} → {target}")
        return True
    print(f"    ⚠️  {tcd_id}: HTTP 200 but parent is {actual!r} (expected {target!r})")
    return False


# ── Ownership & tagging ───────────────────────────────────────────────────────

def set_owner(
    art_id: str | int,
    subject: str,
    owner: str,
    session: requests.Session | None = None,
) -> int:
    """Set the owner field on an article."""
    return set_field(art_id, subject, "owner", owner, session)


def get_tag(art_id: str | int, session: requests.Session | None = None) -> str:
    """Return the current space-separated tag string for an article."""
    a = get_article(art_id, fields="id,tag", session=session)
    return str(a.get("tag") or "")


def append_tag(
    art_id: str | int,
    subject: str,
    tag: str,
    session: requests.Session | None = None,
) -> int:
    """Append *tag* to an article's existing tags (no-op if already present).

    Returns HTTP status code (200 = success or already present).
    """
    existing = get_tag(art_id, session)
    existing_tags = set(existing.split()) if existing.strip() else set()
    if tag in existing_tags:
        return 200  # already tagged — nothing to do
    new_tag = " ".join(sorted(existing_tags | {tag}))
    return set_field(art_id, subject, "tag", new_tag, session)


# ── Planning fields (two-shot pattern) ───────────────────────────────────────

def set_planning_fields(
    tc_id: str | int,
    planning_status: str,
    drive_to_date: str,
    session: requests.Session | None = None,
) -> tuple[int, int]:
    """Set both planning_status and drive_to_date on a test_case.

    Must be sent as two separate PUTs — a combined PUT returns 400.
    Do NOT include send_mail in the body (HSD returns 400 if it is present).

    Returns (planning_status_code, drive_to_date_code).
    """
    s = session or get_session()
    c1 = set_field(tc_id, "test_case", "planning_status", planning_status, s)
    c2 = set_field(tc_id, "test_case", "drive_to_date", drive_to_date, s)
    return c1, c2


# ── Article creation ─────────────────────────────────────────────────────────

def create_article(
    subject: str,
    field_values: list[dict[str, Any]],
    dry_run: bool = False,
    session: requests.Session | None = None,
) -> str | None:
    """POST a new article and return its new ID (str), or None on failure.

    When *dry_run* is True the call is skipped and the title is printed instead.
    """
    if dry_run:
        title = next(
            (fv.get("title") for fv in field_values if "title" in fv), "?"
        )
        print(f"  [DRY RUN] Would create {subject}: {title}")
        return None
    s = session or get_session()
    payload = {
        "subject": subject,
        "tenant": TENANT,
        "fieldValues": field_values,
    }
    r = s.post(f"{BASE}/article", params={"tenant": TENANT}, json=payload)
    if r.status_code in (200, 201):
        return str(r.json().get("new_id") or r.json().get("id") or "")
    print(f"  FAILED HTTP {r.status_code}: {r.text[:200]}")
    return None

def run_move_plan(
    move_plan: dict[str, dict],
    session: requests.Session | None = None,
    verify: bool = True,
) -> tuple[int, int]:
    """Execute a standard MOVE_PLAN dict and optionally verify each move.

    *move_plan* format (same layout used across all move_* scripts)::

        {
            "<tpf_id>": {
                "name": "<human label>",
                "tcds": {"<tcd_id>": "<tcd_title>", ...}  # dict form
                # OR
                "tcds": ["<tcd_id>", ...]                  # list form
            },
            ...
        }

    Returns ``(ok, fail)`` counts.
    """
    s = session or get_session()
    total = sum(
        len(info["tcds"]) for info in move_plan.values()
    )
    print(f"=== Moving {total} TCDs ===\n")
    ok = fail = 0

    for tpf_id, info in move_plan.items():
        print(f"▶ {info['name']} [{tpf_id}]")
        tcds = info["tcds"]
        # Support both dict {tcd_id: title} and list [tcd_id]
        items = tcds.items() if isinstance(tcds, dict) else ((t, t) for t in tcds)
        for tcd_id, tcd_title in items:
            code = move_tcd(tcd_id, tpf_id, s)
            sym = "✅" if code == 200 else "❌"
            print(f"  {sym} {tcd_id}: {tcd_title}  (HTTP {code})")
            if code == 200:
                ok += 1
            else:
                fail += 1
        print()

    print(f"=== Summary: {ok}/{total} moved OK, {fail} failed ===\n")

    if verify:
        print("=== Verification ===")
        all_ok = True
        for tpf_id, info in move_plan.items():
            tcds = info["tcds"]
            ids = list(tcds.keys()) if isinstance(tcds, dict) else tcds
            for tcd_id in ids:
                actual = get_parent(tcd_id, s)
                match = str(actual) == str(tpf_id)
                sym = "✅" if match else "❌"
                print(f"  {sym} {tcd_id}: parent={actual} (expected {tpf_id})")
                if not match:
                    all_ok = False
        print(f"\n{'✅ All moves verified!' if all_ok else '❌ Some moves failed verification'}")

    return ok, fail


def classify_tcd(
    title: str,
    keyword_map: list[tuple[list[str], str]],
    default: str,
) -> str:
    """Return the target TPF ID based on keywords found in *title*.

    *keyword_map* is an ordered list of ``(keywords, tpf_id)`` pairs; the first
    matching entry wins.  *default* is returned when nothing matches.

    Example::

        KEYWORD_MAP = [
            (["demotion", "undemotion"], "15019478561"),
            (["fast c1e", "fast_c1e"],  "15019478560"),
            (["module", "mc6"],          "15019478562"),
        ]
        classify_tcd(tcd_title, KEYWORD_MAP, default="15019478559")
    """
    tl = title.lower()
    for keywords, tpf_id in keyword_map:
        if any(k.lower() in tl for k in keywords):
            return tpf_id
    return default
