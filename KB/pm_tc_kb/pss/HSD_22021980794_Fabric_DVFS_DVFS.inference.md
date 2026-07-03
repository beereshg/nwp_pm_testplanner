# NWP PSS Analysis

## Metadata
- HSD ID: 22021980794
- Title: BIOS Configurations of DVFS settings
- Feature: Fabric DVFS
- Sub Feature: DVFS
- Script: nwp_pss_scripts/nwp_dvfs.py
- HSD Script: pm\pss\dvfs\dvfs.py
- TC Owner: jscanlo1
- TR Owner: akurathi
- Validation Environment: emulation.hsle
- Test Cycle: Newport Product.trunk.pss_0p5.pss.val.NWP_MCP-HSLE
- NWP Scope: Runnable_On_N-1

## HSD Hierarchy
- Test Case Definition: [22021969939 - Fabric GV Control](https://hsdes.intel.com/appstore/article/#/22021969939)
- Test Case: [22021980794 - BIOS Configurations of DVFS settings](https://hsdes.intel.com/appstore/article/#/22021980794)
- Test Result: [22022027572 - [PSS][DVFS] BIOS Configurations](https://hsdes.intel.com/appstore/article/#/22022027572)

## KB References
- KB Article: [KB/pm_features/fabric_dvfs/dvfs.md](../../../KB/pm_features/fabric_dvfs/dvfs.md)

## Model Response

## Refined Intent
Verify available BIOS configurations for DVFS settings. NWP: Fabric DVFS/UFS is entirely ZBB'd — mesh/CAB fixed at 2 GHz. Verify DVFS BIOS knobs are not configurable and mesh frequency is fixed.

## Refined Test Steps
Pre-Conditions:
  - NWP: Fabric DVFS ZBB'd — negative validation

Step 1 — Check DVFS BIOS knobs:
  On NWP: verify DVFS disable methods are default/irrelevant.
  DVFS BIOS knobs should not allow frequency changes.

Step 2 — Verify mesh/CAB frequency:
  Read UFS TPMI registers — expect fixed 2 GHz or registers not present.

Pass/Fail Criteria:
  PASS (NWP): DVFS not configurable, mesh/CAB fixed at 2 GHz
  FAIL: DVFS configuration available on NWP

HAS/MAS References:
  - NWP PM MAS — Fabric DVFS ZBB (mesh/CAB fixed 2 GHz): https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html

### NWP Project Relevance
**Test Classification:** Regression (DMR-inherited)
**Feature Status:** Expected to work
**Test Purpose:** Verify available BIOS configurations for DVFS settings. NWP: Fabric DVFS/UFS is entirely ZBB'd — mesh/CAB fixed at 2 GHz. Verify DVFS BIOS knobs are not configurable and mesh frequency is fixed.
**Negative Test Aspect:** None
**NWP Delta:** Topology differences from DMR (2 CBB + 1 NIO); same Fabric DVFS behavior expected

## Section A: Critical Execution Path
1. Step 1 — Check DVFS BIOS knobs:
2. Step 2 — Verify mesh/CAB frequency:

## Section B: Component Interaction Diagram
```mermaid
sequenceDiagram
    participant OS as Host OS
    participant FW as PCode/OCode
    participant HW as Hardware

    OS->>FW: Send command via interface
    FW->>HW: Configure registers
    HW-->>FW: Acknowledge
    FW-->>OS: Return status
```

## Section C: Interface Coverage Assessment
| Interface | Covered | Notes |
| --------- | ------- | ----- |
| B2P | Yes | Primary interface |
| CSR | Yes | Primary interface |
| TPMI_IB | Yes | Primary interface |

## Section D: NWP Specification References
- **NWP PM HAS**: [NWP HAS - PM Features](https://docs.intel.com/documents/custom-xeon/newport-docs/has/Overview/NWP_HAS.html#pm-features)
- **NWP PM MAS**: [NWP IMH SoC PM MAS - Fabric DVFS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html#fabric-dvfs)
- **DMR PM HAS**: [DMR SoC PM HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/SOC_PM_HAS/DMR_SOC_PM_HAS.html)
- **Feature HAS**: [DMR Fabric DVFS HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/Features/FabricDVFS/DMR_FabricDVFS.html)
- **Intel® 64 and IA-32 SDM**: MSR definitions, CPUID enumeration

## Section E: NWP Risk Assessment
| Risk | Likelihood | Impact | Mitigation |
| ---- | ---------- | ------ | ---------- |
| Topology change | Medium | Medium | Verify on multi-die config |
| Interface delta | Low | Low | Compare with DMR baseline |
| Timing sensitivity | Low | Medium | Allow tolerance margins |

## Section F: Recommendations
1. Verify test works on NWP multi-die topology
2. Check for any interface changes from DMR
3. Update HAS references to NWP specifications
4. Add negative test coverage if missing
5. Consider additional stress test variants

---
*Generated from metadata on 2026-05-28 23:20:51*