# Deep Analysis: MC6 wake target single source

| Field | Value |
|-------|-------|
| **HSD ID** | 16031170175 |
| **Title** | MC6 wake target single source |
| **Segment** | FV/PSS |
| **Parent TP** | 15019478558 |
| **Parent TCD** | [16031170167](https://hsdes.intel.com/appstore/article-one/#/16031170167) |
| **Status** | open |

## Test Case Intent

Verify single-source wake routes to correct target and preserves required wake signal order.

## Test Steps

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Enter MC6 on target module. | Module reaches deep-idle state. |
| 2 | Trigger one wake source. | Wake targets expected core/domain. |
| 3 | Observe signal order. | `WAKE_REQ -> DMN_ACTIVE -> DMN_IN_C3C6 clear`. |

## Pass / Fail Criteria

- PASS: correct target plus correct signal order.
- FAIL: wrong target or signal-order violation.
