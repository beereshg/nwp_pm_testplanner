# TCD TBD-ERR -- DLCP - Error Handling / Conflict

| Field | Value |
|-------|-------|
| **TCD ID** | TBD-ERR (TBD -- HSD article not yet created) |
| **Title** | DLCP - Error Handling / Conflict |
| **Status** | Gap/TBD -- HSD creation pending |
| **Owner** | bg3 |
| **Parent TPF** | [16031169314 -- NWP PM DLCP](https://hsdes.intel.com/appstore/article-one/#/16031169314) |
| **Source** | Co-Design T1 gap audit, 2026-07-18 |
| **KB last updated** | 2026-07-18 |

---

## Section 1: Architecture / Micro-architecture and Functionality

Validates DLCP-specific error conditions: BIOS SST_CLOS_ASSOC conflict with SST_TF_INFO_10 fuse mask, ERROR_TYPE reporting for unsupported/conflicting feature-control combinations in DLCP mode.

> **Architecture overview:** See [TPF 16031169314](https://hsdes.intel.com/appstore/article-one/#/16031169314) for DLCP architecture.

---

## Section 5: Operational Behavior

### TC Coverage Map

| Tier | WHAT (scenario + bar) | TC |
|------|----------------------|----|
| PSS/FV | BIOS-vs-fuse mask conflict: BIOS programs SST_CLOS_ASSOC inconsistent with SST_TF_INFO_10 mask; expected rejection/override behavior validated | CLOS state must not reflect incorrect assignment | *(TC TBD)* |
| PSS/FV | ERROR_TYPE reporting: invalid runtime feature-control combinations in DLCP mode produce correct SST_CP_STATUS.ERROR_TYPE; error cleared on valid write | *(TC TBD)* |

---

## Section 6: Corner Cases and Error Handling

*(TBD -- to be filled during TCD review)*

---

## Section 8: References

- [PCT HAS](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/PCT.html)
- [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html)
- [TPMI HAS](https://docs.intel.com/documents/pm_doc/src/server/arch_common/tpmi/tpmi.html)
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html)
- SST_CP_STATUS.ERROR_TYPE: SST HAS
BIOS CLOS programming vs fuse mask: PCT HAS
Co-Design T1 findings #6/#12 (2026-07-18)
