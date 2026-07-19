# TCD: C-State Exit Latency Class Validation

<!-- NEW 2026-07-19: Split from TCD 22022421253 per Co-Design T2 ingest.
     Separate latency-class bar from wake-order correctness bar. -->

| Field | Value |
|-------|-------|
| **TCD ID** | [16031170166](https://hsdes.intel.com/appstore/article-one/#/16031170166) |
| **Title** | C-State Exit Latency Class Validation |
| **Status** | open |
| **Owner** | bg3 |
| **Parent TPF** | [15019478559 - Core C1/C6 (Entry/Exit/Residency)](https://hsdes.intel.com/appstore/article-one/#/15019478559) |
| **Parent TCD (split-from)** | [22022421253 - CState exit actions](https://hsdes.intel.com/appstore/article-one/#/22022421253) |
| **Validation Phase** | Alpha / Beta / PRQ |
| **Feature** | Core C-States (exit latency envelope) |
| **Child TCs** | [16031170173](https://hsdes.intel.com/appstore/article-one/#/16031170173) — C-state exit latency envelope<br>[16031170174](https://hsdes.intel.com/appstore/article-one/#/16031170174) — C-state exit latency stability |
| **KB last updated** | 2026-07-19 |

---

## Section 1: Architecture / Micro-architecture and Functionality

This TCD validates state-specific exit latency classes as a measurable bar independent of wake ordering.
It owns timing-envelope checks for supported target states in current NWP scope.

Out of scope:
- wake sequence ordering correctness (owned by TCD 22022421253)
- stress methodology ownership (owned by framework TCDs)

## Section 5: Pass/Fail Bar

- Measured exit latency remains within program envelopes for targeted states:
     - C6A <= 200 us
     - C6S <= 500 us
     - MC6 <= 1000 us
- For each state, `p95` and max latency stay within envelope across repeated controlled windows.
- Latency class is stable under equivalent stimulus and configuration.

FAIL if any of the following occur:
- envelope breach for any targeted state
- unstable latency class across equivalent runs
- systematic regression after policy or configuration toggles

## Section 6: TC Coverage Map

| TC | Tier | Scope | Expected Result (PASS) | Status |
|----|------|-------|------------------------|--------|
| [16031170173](https://hsdes.intel.com/appstore/article-one/#/16031170173) | FV/PSS/PV | C6A/C6S/MC6 exit latency envelope measurement | C6A <= 200 us, C6S <= 500 us, MC6 <= 1000 us | planned |
| [16031170174](https://hsdes.intel.com/appstore/article-one/#/16031170174) | FV/PSS/PV | Repeated-run latency stability and percentile checks | per-state `p95` and max latency remain within envelope across repeated windows | planned |

## Section 8: References

| Reference | Link |
|-----------|------|
| Core C-States HAS | [dmr_core_state.html](https://docs.intel.com/documents/pm_doc/src/server/dmr/pm%20features/dmr_core_state.html) |
| Split source | [22022421253](https://hsdes.intel.com/appstore/article-one/#/22022421253) |
