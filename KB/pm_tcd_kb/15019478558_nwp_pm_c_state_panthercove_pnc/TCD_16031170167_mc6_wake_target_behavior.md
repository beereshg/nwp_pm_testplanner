# TCD: MC6 Wake Target Behavior

<!-- NEW 2026-07-19: Split from TCD 22022421260 per Co-Design T2 ingest.
     Separate wake-target correctness from MC6 residency accounting. -->

| Field | Value |
|-------|-------|
| **TCD ID** | [16031170167](https://hsdes.intel.com/appstore/article-one/#/16031170167) |
| **Title** | MC6 Wake Target Behavior |
| **Status** | open |
| **Owner** | bg3 |
| **Parent TPF** | [15019478562 - Module C-States (Core-Module)](https://hsdes.intel.com/appstore/article-one/#/15019478562) |
| **Parent TCD (split-from)** | [22022421260 - CStates MC6 residency counter](https://hsdes.intel.com/appstore/article-one/#/22022421260) |
| **Validation Phase** | Alpha / Beta / PRQ |
| **Feature** | Core C-States (MC6 wake routing/targeting) |
| **Child TCs** | [16031170175](https://hsdes.intel.com/appstore/article-one/#/16031170175) — MC6 wake target single source<br>[16031170176](https://hsdes.intel.com/appstore/article-one/#/16031170176) — MC6 wake target concurrent sources |
| **KB last updated** | 2026-07-19 |

---

## Section 1: Architecture / Micro-architecture and Functionality

This TCD validates that MC6 wake behavior targets and ordering are correct when wake events occur.
It owns wake-target routing correctness and serialization behavior, not residency accumulation.

Owned behavior:
- first-wake handling from module deep-idle
- target routing correctness for wake source
- serialization/ordering consistency across repeated wake scenarios

## Section 5: Pass/Fail Bar

- Wake from MC6 targets the correct domain/core path per wake source and policy.
- Signal ordering follows expected wake protocol: `WAKE_REQ` assertion, `DMN_ACTIVE` transition, then `DMN_IN_C3C6` clear.
- Wake ordering and serialization are consistent across equivalent scenarios.
- No dropped wake, duplicate wake, or wrong-target wake event.

FAIL if any of the following occur:
- wake directed to wrong target
- wake ordering inversion under equivalent stimulus
- wake event loss, duplicate handling, or hang

## Section 6: TC Coverage Map

| TC | Tier | Scope | Expected Result (PASS) | Status |
|----|------|-------|------------------------|--------|
| [16031170175](https://hsdes.intel.com/appstore/article-one/#/16031170175) | FV/PSS | MC6 first-wake target correctness | wake routes to expected target and follows `WAKE_REQ -> DMN_ACTIVE -> DMN_IN_C3C6 clear` | planned |
| [16031170176](https://hsdes.intel.com/appstore/article-one/#/16031170176) | FV/PSS | Concurrent wake source ordering/serialization | serialization order stays deterministic; no dropped or duplicate wake events | planned |

## Section 8: References

| Reference | Link |
|-----------|------|
| Core C-States HAS | [dmr_core_state.html](https://docs.intel.com/documents/pm_doc/src/server/dmr/pm%20features/dmr_core_state.html) |
| Split source | [22022421260](https://hsdes.intel.com/appstore/article-one/#/22022421260) |
