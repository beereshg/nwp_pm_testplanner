# TCD TBD-NEG -- DLCP - Negative / Absent Path

| Field | Value |
|-------|-------|
| **TCD ID** | TBD-NEG (TBD -- HSD article not yet created) |
| **Title** | DLCP - Negative / Absent Path |
| **Status** | Gap/TBD -- HSD creation pending |
| **Owner** | bg3 |
| **Parent TPF** | [16031169314 -- NWP PM DLCP](https://hsdes.intel.com/appstore/article-one/#/16031169314) |
| **Source** | Co-Design T1 gap audit, 2026-07-18 |
| **KB last updated** | 2026-07-18 |

---

## Section 1: Architecture / Micro-architecture and Functionality

Validates the full DLCP-absent path (PCT_Module_Mask=0, Scenario B): no DLCP qualification in TPMI or OS, correct BIOS fallback to MADT/APIC-ID-based PCT, and that BIOS override attempt when fuse mask is absent is correctly handled.

> **Architecture overview:** See [TPF 16031169314](https://hsdes.intel.com/appstore/article-one/#/16031169314) for DLCP architecture.

---

## Section 5: Operational Behavior

### TC Coverage Map

| Tier | WHAT (scenario + bar) | TC |
|------|----------------------|----|
| PSS/FV/PV | Scenario B completeness: SST_TF_INFO_10=0; SST_TF_INFO_101.QUALIFIED_MODULE_MASK=0; HWP_CAPABILITIES uniform; no DLCP-specific capability visible anywhere | *(TC TBD)* |
| PSS/FV | Fuse-absent + BIOS override attempt: when PCT_Module_Mask=0 and BIOS attempts to set HP positions via knob, BIOS MADT/APIC-ID path is correctly used (DLCP path bypassed) | *(TC TBD)* |
| PV | Scenario B OS/tool: no DLCP topology from intel-speed-select; HWP_CAPABILITIES not differentiated; tool sees standard PCT (BIOS-computed) or no PCT if disabled | *(TC TBD)* |

---

## Section 6: Corner Cases and Error Handling

*(TBD -- to be filled during TCD review)*

---

## Section 8: References

- [PCT HAS](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/PCT.html)
- [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html)
- [TPMI HAS](https://docs.intel.com/documents/pm_doc/src/server/arch_common/tpmi/tpmi.html)
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html)
- PCT_Module_Mask OTP fuse: PCT HAS
SST_TF_INFO_10 (Scenario B = 0): PCT HAS
Co-Design T1 findings #4/#5/#13/#14 (2026-07-18)
