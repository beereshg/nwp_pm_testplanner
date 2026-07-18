# TCD TBD-OT -- DLCP - Ordered Throttle Interaction

| Field | Value |
|-------|-------|
| **TCD ID** | TBD-OT (TBD -- HSD article not yet created) |
| **Title** | DLCP - Ordered Throttle Interaction |
| **Status** | Gap/TBD -- HSD creation pending |
| **Owner** | bg3 |
| **Parent TPF** | [16031169314 -- NWP PM DLCP](https://hsdes.intel.com/appstore/article-one/#/16031169314) |
| **Source** | Co-Design T1 gap audit, 2026-07-18 |
| **KB last updated** | 2026-07-18 |

---

## Section 1: Architecture / Micro-architecture and Functionality

Validates that when DLCP is active and PL1 is exceeded, ordered throttle (Phase A/B/C, SST_CP_PRIORITY_TYPE=1) applies correctly to fuse-designated HP cores rather than BIOS-computed HP cores, confirming DLCP-assigned HP set is throttled last.

> **Architecture overview:** See [TPF 16031169314](https://hsdes.intel.com/appstore/article-one/#/16031169314) for DLCP architecture.

---

## Section 5: Operational Behavior

### TC Coverage Map

| Tier | WHAT (scenario + bar) | TC |
|------|----------------------|----|
| FV/PSS | PL1 stress with DLCP active: ordered throttle applies LP cores first (Phase A/B), fuse-designated HP cores maintained longest (Phase C last resort) | CLOS enforcement uses fuse-derived HP set | *(TC TBD)* |
| PSS | VP: ordered throttle sequencing with DLCP fuse mask programmed (HSLE with CBB RTL preferred) | *(TC TBD)* |

---

## Section 6: Corner Cases and Error Handling

*(TBD -- to be filled during TCD review)*

---

## Section 8: References

- [PCT HAS](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/PCT.html)
- [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html)
- [TPMI HAS](https://docs.intel.com/documents/pm_doc/src/server/arch_common/tpmi/tpmi.html)
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html)
- SST-TF ordered throttle: SST HAS (SST_CP_PRIORITY_TYPE=1, Phase A/B/C)
DLCP CLOS derivation from fuse: PCT HAS
Co-Design T1 finding #9 (2026-07-18)
