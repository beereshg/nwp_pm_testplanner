# TCD TBD-PV -- DLCP - PV Discovery / Topology

| Field | Value |
|-------|-------|
| **TCD ID** | TBD-PV (TBD -- HSD article not yet created) |
| **Title** | DLCP - PV Discovery / Topology |
| **Status** | Gap/TBD -- HSD creation pending |
| **Owner** | bg3 |
| **Parent TPF** | [16031169314 -- NWP PM DLCP](https://hsdes.intel.com/appstore/article-one/#/16031169314) |
| **Source** | Co-Design T1 gap audit, 2026-07-18 |
| **KB last updated** | 2026-07-18 |

---

## Section 1: Architecture / Micro-architecture and Functionality

Validates OS/tool-layer DLCP discovery: SST_TF_INFO_101.QUALIFIED_MODULE_MASK visibility, intel-speed-select DLCP topology reporting, and per-core IA32_HWP_CAPABILITIES.highest_perf differentiation (HP=P0max, LP=LP_CLIP) in DLCP mode. Requires booted Ubuntu on NWP silicon.

> **Architecture overview:** See [TPF 16031169314](https://hsdes.intel.com/appstore/article-one/#/16031169314) for DLCP architecture.

---

## Section 5: Operational Behavior

### TC Coverage Map

| Tier | WHAT (scenario + bar) | TC |
|------|----------------------|----|
| PV | SST_TF_INFO_101.QUALIFIED_MODULE_MASK visible to OS via TPMI read | intel-speed-select reports DLCP-active topology | HP cores show P0max; LP cores show LP_CLIP in HWP_CAPABILITIES | *(TC TBD)* |
| PV | Tool/topology reporting: intel-speed-select or equivalent reports DLCP capability when SST_TF_INFO_10 != 0 | *(TC TBD)* |
| PV | Scenario B (fuse=0): SST_TF_INFO_101.QUALIFIED_MODULE_MASK = 0; no DLCP capability reported; HWP_CAPABILITIES uniform | *(TC TBD)* |

---

## Section 6: Corner Cases and Error Handling

*(TBD -- to be filled during TCD review)*

---

## Section 8: References

- [PCT HAS](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/PCT.html)
- [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html)
- [TPMI HAS](https://docs.intel.com/documents/pm_doc/src/server/arch_common/tpmi/tpmi.html)
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html)
- SST_TF_INFO_101.QUALIFIED_MODULE_MASK: TPMI HAS (NWP-specific)
IA32_HWP_CAPABILITIES.highest_perf per-core: TPMI HAS
Co-Design T1 findings #1/#2/#3/#13/#14 (2026-07-18)
