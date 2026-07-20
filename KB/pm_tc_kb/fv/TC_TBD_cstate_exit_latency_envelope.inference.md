# Deep Analysis: C-state exit latency envelope

| Field | Value |
|-------|-------|
| **HSD ID** | 16031170173 |
| **Title** | C-state exit latency envelope |
| **Segment** | FV/PSS/PV |
| **Parent TP** | 15019478558 |
| **Parent TCD** | [16031170166](https://hsdes.intel.com/appstore/article-one/#/16031170166) |
| **Status** | open |

## Test Case Intent

Measure C6A/C6S/MC6 exit latency and verify envelope limits.

## Test Steps

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Run controlled wake tests per state. | Valid latency samples collected. |
| 2 | Compute max latency by state. | C6A <= 200 us, C6S <= 500 us, MC6 <= 1000 us. |

## Pass / Fail Criteria

- PASS: all targeted states stay within envelope.
- FAIL: any targeted state exceeds envelope.
