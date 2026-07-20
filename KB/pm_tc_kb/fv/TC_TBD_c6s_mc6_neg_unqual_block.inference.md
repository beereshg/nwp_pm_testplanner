# Deep Analysis: C6S MC6 negative unqualified block

| Field | Value |
|-------|-------|
| **HSD ID** | 16031170170 |
| **Title** | C6S MC6 negative unqualified block |
| **Segment** | FV/PSS |
| **Parent TP** | 15019478558 |
| **Parent TCD** | [16031170164](https://hsdes.intel.com/appstore/article-one/#/16031170164) |
| **Status** | open |

## Test Case Intent

Verify MC6 does not increment when all-core qualification is intentionally broken.

## Test Steps

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Hold one core active in module. | Qualification is broken. |
| 2 | Drive remaining cores to C6S. | Partial C6S achieved. |
| 3 | Poll `MSR 0x664`. | No increment while one core remains active. |

## Pass / Fail Criteria

- PASS: `0x664` remains unchanged during unqualified window.
- FAIL: `0x664` increments while qualification is broken.
