# Deep Analysis: C-state exit latency stability

| Field | Value |
|-------|-------|
| **HSD ID** | 16031170174 |
| **Title** | C-state exit latency stability |
| **Segment** | FV/PSS/PV |
| **Parent TP** | 15019478558 |
| **Parent TCD** | [16031170166](https://hsdes.intel.com/appstore/article-one/#/16031170166) |
| **Status** | open |

## Test Case Intent

Verify repeated-run stability for state latency distributions.

## Test Steps

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Execute repeated wake trials per state. | Stable sample sets generated. |
| 2 | Compute p95 and max by state. | Values remain within defined envelope across runs. |

## Pass / Fail Criteria

- PASS: p95 and max remain stable and in-range.
- FAIL: unstable drift or out-of-range tails.
