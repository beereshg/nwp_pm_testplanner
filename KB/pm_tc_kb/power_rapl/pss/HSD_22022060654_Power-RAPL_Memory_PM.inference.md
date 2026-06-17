# NWP PSS Analysis

## Metadata
- HSD ID: 22022060654
- Title: Memory PM ZBB Negative Checks
- Feature: Power/RAPL
- Sub Feature: Memory PM
- Script: nwp_pss_scripts/pss_memory_pm_zbb.py
- HSD Script: (none)
- TC Owner: jscanlo1
- TR Owner: bg3
- Validation Environment: emulation.hsle
- Test Cycle: Newport Product.trunk.pss_1p0.pss.val.NWP_MCP-HSLE
- NWP Scope: Runnable_On_N-1

## HSD Hierarchy
- Test Case Definition: [22022060621 - NWP ZBB Negative Validation](https://hsdes.intel.com/appstore/article/#/22022060621)
- Test Case: [22022060654 - Memory PM ZBB Negative Checks](https://hsdes.intel.com/appstore/article/#/22022060654)
- Test Result: [22022060666 - [PSS][MEMORY] Memory PM ZBB Negative Checks](https://hsdes.intel.com/appstore/article/#/22022060666)

## KB References
- KB Article: [KB/pm_features/power_rapl/memory_pm.md](../../../KB/pm_features/power_rapl/memory_pm.md)

## Model Response

## Refined Intent
NWP ZBB negative validation: verify Memory PM features (MemClos, DRC, APD/PPD/LPM/SSR/SR) are inaccessible on NWP. Note: CLTT with MR4 is supported on NWP and is NOT ZBB'd.

## Refined Test Steps
Pre-Conditions:
  - NWP platform booted

Step 1 — Check DRC_Header.DRC_FEATURE_AVAILABLE = 0.

Step 2 — Attempt MemClos configuration — expect no effect.

Step 3 — Verify memory power states (APD/PPD/LPM/SSR/SR) not supported.

Note: CLTT with MR4 IS supported on NWP — do NOT validate CLTT as ZBB'd.

Pass/Fail Criteria:
  PASS: MemClos, DRC, and memory power states inaccessible on NWP
  FAIL: Any of those features accessible

HAS/MAS References:
  - NWP PM MAS — Memory PM ZBB scope: https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html
  - DMR DDR5/MCR HAS — MR4 CLTT (supported): https://docs.intel.com/documents/pm_doc/src/server/DMR/IP_PM_Features/DMR_DDR5_MCR.html#mr4-based-cltt

### NWP Project Relevance
**Test Classification:** Regression (DMR-inherited)
**Feature Status:** Expected to work
**Test Purpose:** NWP ZBB negative validation: verify Memory PM features (MemClos, DRC, APD/PPD/LPM/SSR/SR) are inaccessible on NWP. Note: CLTT with MR4 is supported on NWP and is NOT ZBB'd.
**Negative Test Aspect:** None
**NWP Delta:** Topology differences from DMR (2 CBB + 1 NIO); same Power/RAPL behavior expected

## Section A: Critical Execution Path
1. Step 1 — Check DRC_Header.DRC_FEATURE_AVAILABLE = 0.
2. Step 2 — Attempt MemClos configuration — expect no effect.
3. Step 3 — Verify memory power states (APD/PPD/LPM/SSR/SR) not supported.

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
| Fuse | Yes | Primary interface |
| TPMI_IB | Yes | Primary interface |

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