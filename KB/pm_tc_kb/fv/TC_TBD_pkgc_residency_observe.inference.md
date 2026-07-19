# Deep Analysis: PKGC residency observe

| Field | Value |
|-------|-------|
| **HSD ID** | 16031170183 |
| **Title** | PKGC residency observe |
| **Segment** | FV/PSS |
| **Parent TP** | 15019478558 |
| **Parent TCD** | [16031170168](https://hsdes.intel.com/appstore/article-one/#/16031170168) |
| **Status** | parked |

## Test Case Intent

When enabled by scope, validate package C6 residency observability contract.

## Test Steps

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Apply package deep-idle stimulus. | Package path is active. |
| 2 | Poll `MSR 0x3F9`. | Behavior matches enabled architecture contract. |

## Pass / Fail Criteria

- PASS: `0x3F9` behavior matches enabled contract.
- FAIL: mismatch versus expected package-residency behavior.
