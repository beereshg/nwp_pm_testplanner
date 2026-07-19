# Deep Analysis: MC6 entry negative phase guard

| Field | Value |
|-------|-------|
| **HSD ID** | 16031170172 |
| **Title** | MC6 entry negative phase guard |
| **Segment** | FV/PSS |
| **Parent TP** | 15019478558 |
| **Parent TCD** | [16031170165](https://hsdes.intel.com/appstore/article-one/#/16031170165) |
| **Status** | open |

## Test Case Intent

Verify invalid precondition perturbations do not allow illegal phase advance.

## Test Steps

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Inject precondition perturbation. | Guard path is engaged. |
| 2 | Attempt entry progression. | Invalid phase advance is blocked. |
| 3 | Read `MSR 0x664`. | No premature increment. |

## Pass / Fail Criteria

- PASS: guard blocks invalid progression and `0x664` stays unchanged.
- FAIL: illegal phase advance or early `0x664` increment.
