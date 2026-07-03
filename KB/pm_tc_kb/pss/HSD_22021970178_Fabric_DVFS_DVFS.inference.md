# NWP PSS Analysis

## Metadata
- HSD ID: 22021970178
- Title: TPMI-driven FabricGV
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
- Test Case: [22021970178 - TPMI-driven FabricGV](https://hsdes.intel.com/appstore/article/#/22021970178)
- Test Result: [22022027662 - [PSS][DVFS] TPMI-driven FabricGV](https://hsdes.intel.com/appstore/article/#/22022027662)

## KB References
- KB Article: [KB/pm_features/fabric_dvfs/dvfs.md](../../../KB/pm_features/fabric_dvfs/dvfs.md)

## Model Response

## Refined Intent
Verify TPMI-driven fabric GV transitions. NWP: UFS/FabricGV is ZBB'd — mesh/CAB fixed at 2 GHz. TPMI FabricGV writes should have no effect.

## Refined Test Steps
Pre-Conditions:
  - NWP: FabricGV ZBB'd — negative validation

Step 1 — Write UFS TPMI registers to request GV transition.

Step 2 — On NWP: expect no mesh frequency change.

Step 3 — Verify mesh stays at 2 GHz.

Pass/Fail Criteria:
  PASS (NWP): TPMI FabricGV has no effect — mesh stays at 2 GHz (ZBB'd)
  FAIL: Mesh frequency changes

HAS/MAS References:
  - TPMI HAS — UFS / FabricGV: https://docs.intel.com/documents/pm_doc/src/server/arch_common/TPMI/TPMI.html
  - NWP PM MAS — UFS ZBB: https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html

### NWP Project Relevance
**Test Classification:** Regression (DMR-inherited)
**Feature Status:** Expected to work
**Test Purpose:** Verify TPMI-driven fabric GV transitions. NWP: UFS/FabricGV is ZBB'd — mesh/CAB fixed at 2 GHz. TPMI FabricGV writes should have no effect.
**Negative Test Aspect:** None
**NWP Delta:** Topology differences from DMR (2 CBB + 1 NIO); same Fabric DVFS behavior expected

## Section A: Critical Execution Path
1. Step 1 — Write UFS TPMI registers to request GV transition.
2. Step 2 — On NWP: expect no mesh frequency change.
3. Step 3 — Verify mesh stays at 2 GHz.

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