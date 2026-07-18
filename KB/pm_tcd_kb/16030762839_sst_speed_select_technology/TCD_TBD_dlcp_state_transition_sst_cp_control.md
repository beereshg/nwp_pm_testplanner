# TCD TBD-ST -- DLCP - State Transition / SST-CP Control

| Field | Value |
|-------|-------|
| **TCD ID** | TBD-ST (TBD -- HSD article not yet created) |
| **Title** | DLCP - State Transition / SST-CP Control |
| **Status** | Gap/TBD -- HSD creation pending |
| **Owner** | bg3 |
| **Parent TPF** | [16031169314 -- NWP PM DLCP](https://hsdes.intel.com/appstore/article-one/#/16031169314) |
| **Source** | Co-Design T1 gap audit, 2026-07-18 |
| **KB last updated** | 2026-07-18 |

---

## Section 1: Architecture / Micro-architecture and Functionality

Validates runtime SST-CP enable/disable behavior when DLCP fuse is active: DLCP does not remove the dynamic SST-CP control path. Includes HANDSHAKE/LAST_HANDSHAKE confirmation writes.

> **Architecture overview:** See [TPF 16031169314](https://hsdes.intel.com/appstore/article-one/#/16031169314) for DLCP architecture.

---

## Section 5: Operational Behavior

### TC Coverage Map

| Tier | WHAT (scenario + bar) | TC |
|------|----------------------|----|
| PSS/FV | SST-CP enable -> disable -> re-enable with DLCP fuse active: fuse-derived HP assignment persists correctly after re-enable; no stale or incorrect HP set after toggle | *(TC TBD)* |
| PSS/FV | HANDSHAKE verification: SST_CP_CONTROL.HANDSHAKE written; SST_CP_STATUS.LAST_HANDSHAKE matches on each enable/disable transition in DLCP mode | *(TC TBD)* |
| PV | PV path: OS/tool observes correct DLCP HP topology after SST-CP re-enable | *(TC TBD)* |

---

## Section 6: Corner Cases and Error Handling

*(TBD -- to be filled during TCD review)*

---

## Section 8: References

- [PCT HAS](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/PCT.html)
- [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html)
- [TPMI HAS](https://docs.intel.com/documents/pm_doc/src/server/arch_common/tpmi/tpmi.html)
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html)
- SST_CP_CONTROL.HANDSHAKE / SST_CP_STATUS.LAST_HANDSHAKE: SST HAS
Runtime SST-CP enable/disable: SST HAS
Co-Design T1 findings #10/#11 (2026-07-18)
