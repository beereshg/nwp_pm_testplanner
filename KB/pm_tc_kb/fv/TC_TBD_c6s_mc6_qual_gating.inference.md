# Deep Analysis: C6S MC6 qualification gating

| Field | Value |
|-------|-------|
| **HSD ID** | 16031170169 |
| **Title** | C6S MC6 qualification gating |
| **Segment** | FV/PSS |
| **Parent TP** | 15019478558 |
| **Parent TCD** | [16031170164](https://hsdes.intel.com/appstore/article-one/#/16031170164) |
| **Status** | open |

## Test Case Intent

Verify MC6 residency increments only after all-core module qualification during C6S flow.

## Pre-Conditions

- C6S enabled on target module.
- One module selected for focused checks.
- MSR read access available for 0x664 and 0x3F9.

## Test Steps

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Drive all module cores to C6S. | C6S path is active. |
| 2 | Poll `MSR 0x664`. | Counter starts incrementing only after qualification. |
| 3 | Poll `MSR 0x3F9`. | Stays 0 in NWP scope. |

## Pass / Fail Criteria

- PASS: `0x664` increments only after qualification and `0x3F9` stays 0.
- FAIL: premature `0x664` increment or non-zero `0x3F9`.
