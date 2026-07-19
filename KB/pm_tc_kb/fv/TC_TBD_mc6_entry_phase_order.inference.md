# Deep Analysis: MC6 entry phase order

| Field | Value |
|-------|-------|
| **HSD ID** | 16031170171 |
| **Title** | MC6 entry phase order |
| **Segment** | FV/PSS |
| **Parent TP** | 15019478558 |
| **Parent TCD** | [16031170165](https://hsdes.intel.com/appstore/article-one/#/16031170165) |
| **Status** | open |

## Test Case Intent

Verify module entry phases occur in-order: qualification, policy/flush gate, module electrical entry.

## Test Steps

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Drive module into qualification-ready state. | Qualification achieved. |
| 2 | Observe sequence checkpoints. | Ordered transition is preserved. |
| 3 | Poll `MSR 0x664` after completion. | Increment occurs only after full sequence. |

## Pass / Fail Criteria

- PASS: no phase reorder and no premature `0x664` increment.
- FAIL: out-of-order phase or early `0x664` increment.
