# NWP PSS Analysis

## Metadata
- HSD ID: 22022146212
- Title: Sideband Harasser
- Feature: Power/RAPL
- Sub Feature: Sideband
- Script: nwp_pss_scripts/nwp_sb_harasser.py
- HSD Script: (none)
- TC Owner: jscanlo1
- TR Owner: N/A
- Validation Environment: emulation.hsle
- Test Cycle: Newport Product.trunk.pss_1p0.pss.val.NWP_MCP-HSLE
- NWP Scope: Runnable_On_N-1

## HSD Hierarchy
- Test Plan: [22022146207 - Sideband Access](https://hsdes.intel.com/appstore/article/#/22022146207)
- Test Case Definition: [22022146208 - Sideband Harasser](https://hsdes.intel.com/appstore/article/#/22022146208)
- Test Case: [22022146212 - Sideband Harasser](https://hsdes.intel.com/appstore/article/#/22022146212)

## KB References
- KB Article: [KB/pm_features/power_rapl/sideband.md](../../../KB/pm_features/power_rapl/sideband.md)

## Model Response

## Refined Intent
Sideband harasser stress test: inject continuous sideband register accesses to stress sideband fabric. Verify no hangs, MCA errors, or register corruption under sustained sideband traffic.

## Refined Test Steps
Pre-Conditions:
  - Platform booted and stable
  - Sideband fabric accessible via PythonSV

Step 1 — Configure harasser:
  Set up sideband register read/write sweep targeting PM registers.
  Configure iteration count and parallelism.

Step 2 — Run harasser:
  Execute continuous sideband accesses for N iterations.
  Monitor for timeouts, hangs, or errors.

Step 3 — Post-run checks:
  Verify no MCA errors generated.
  Verify platform still responsive.
  Read key PM registers — verify no corruption.

Pass/Fail Criteria:
  PASS: No hangs, errors, or corruption after sustained sideband stress
  FAIL: MCA error, hang, or register corruption

HAS/MAS References:
  - DMR SoC PM HAS — Sideband / Register Access: https://docs.intel.com/documents/pm_doc/src/server/DMR/SOC_PM_HAS/DMR_SOC_PM_HAS.html

### NWP Project Relevance
**Test Classification:** Regression (DMR-inherited)
**Feature Status:** Expected to work
**Test Purpose:** Sideband harasser stress test: inject continuous sideband register accesses to stress sideband fabric. Verify no hangs, MCA errors, or register corruption under sustained sideband traffic.
**Negative Test Aspect:** None
**NWP Delta:** Topology differences from DMR (2 CBB + 1 NIO); same Power/RAPL behavior expected

## Section A: Critical Execution Path
1. Step 1 — Configure harasser:
2. Step 2 — Run harasser:
3. Step 3 — Post-run checks:

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