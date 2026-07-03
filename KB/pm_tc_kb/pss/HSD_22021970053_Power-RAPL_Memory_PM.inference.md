# NWP PSS Analysis

## Metadata
- HSD ID: 22021970053
- Title: Mclos0 Throttling Status
- Feature: Power/RAPL
- Sub Feature: Memory PM
- Script: nwp_pss_scripts/nwp_memory_pm.py
- HSD Script: newport\pm\pss\memory\memclos.py
- TC Owner: isaxena
- TR Owner: bg3
- Validation Environment: emulation.hsle
- Test Cycle: Newport Product.trunk.pss_0p8.pss.val.NWP_NIO-HSLE
- NWP Scope: Runnable_On_N-1

## HSD Hierarchy
- Test Case Definition: [22021969895 - MClos Throttling](https://hsdes.intel.com/appstore/article/#/22021969895)
- Test Case: [22021970053 - Mclos0 Throttling Status](https://hsdes.intel.com/appstore/article/#/22021970053)
- Test Result: [22022320851 - [PSS][MEMORY] Mclos0 Throttling Status](https://hsdes.intel.com/appstore/article/#/22022320851)

## KB References
- KB Article: [KB/pm_features/power_rapl/memory_pm.md](../../../KB/pm_features/power_rapl/memory_pm.md)

## Model Response

## Refined Intent
Verify MClos throttling behavior. Configure MClos for throttling (min=0, max=255), assign all CLOS to this MClos. NWP: MemClos/DRC is ZBB'd — expect no throttling effect.

## Refined Test Steps
Pre-Conditions:
  - NWP: MemClos/DRC ZBB'd — negative validation

Step 1 — Check DRC availability:
  Read DRC_Header.DRC_FEATURE_AVAILABLE — on NWP expect 0.

Step 2 — Attempt MClos configuration:
  Set MClos min=0, max=255.
  Assign all CLOS to this MClos.
  On NWP: expect configuration has no effect.

Step 3 — Run memory workload:
  Verify no MClos throttling engages on NWP.

Pass/Fail Criteria:
  PASS (NWP): MClos has no effect (ZBB'd)
  FAIL: MClos throttling engages on NWP

HAS/MAS References:
  - NWP PM MAS — MemClos/DRC ZBB: https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html

### NWP Project Relevance
**Test Classification:** Regression (DMR-inherited)
**Feature Status:** Expected to work
**Test Purpose:** Verify MClos throttling behavior. Configure MClos for throttling (min=0, max=255), assign all CLOS to this MClos. NWP: MemClos/DRC is ZBB'd — expect no throttling effect.
**Negative Test Aspect:** None
**NWP Delta:** Topology differences from DMR (2 CBB + 1 NIO); same Power/RAPL behavior expected

## Section A: Critical Execution Path
1. Step 1 — Check DRC availability:
2. Step 2 — Attempt MClos configuration:
3. Step 3 — Run memory workload:

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
| TPMI: DRC_Header.DRC_FEATURE_AVAILABLE | Yes | TPMI interface |

## Section D: NWP Specification References
- **NWP PM HAS**: [NWP HAS - PM Features](https://docs.intel.com/documents/custom-xeon/newport-docs/has/Overview/NWP_HAS.html#pm-features)
- **NWP PM MAS**: [NWP IMH SoC PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html)
- **DMR PM HAS**: [DMR SoC PM HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/SOC_PM_HAS/DMR_SOC_PM_HAS.html)
- **Feature HAS**: [PNC PM HAS §7 - RAPL](https://docs.intel.com/documents/pm_doc/src/server/GNR/Features/LNC/GNR_LNC_RAPL.html)
- **DMR CBB HAS**: [DMR CBB PM HAS - RAPL](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/IP%20Integration/PM%20HAS/cbb_pm_has.html#rapl)
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