# NWP PSS Analysis

## Metadata
- HSD ID: 22022023843
- Title: PLR Status registers Check for Thermal Events
- Feature: SoC Thermal
- Sub Feature: EMTTM
- Script: nwp_pss_scripts/nwp_plr_mailbox.py
- HSD Script: (none)
- TC Owner: jinwengo
- TR Owner: mps
- Validation Environment: emulation.hsle,xos
- Test Cycle: Newport Product.trunk.pss_0p8.pss.val.NWP_MCP HSLE XOS
- NWP Scope: Runnable_On_N-1

## HSD Hierarchy
- Test Case Definition: [22021969872 - EMTTM](https://hsdes.intel.com/appstore/article/#/22021969872)
- Test Case: [22022023843 - PLR Status registers Check for Thermal Events](https://hsdes.intel.com/appstore/article/#/22022023843)
- Test Result: [22022027690 - [PSS][EMTTM] PLR Status registers Check for Thermal Events](https://hsdes.intel.com/appstore/article/#/22022027690)

## KB References
- KB Article: [KB/pm_features/soc_thermal/emttm.md](../../../KB/pm_features/soc_thermal/emttm.md)

## Model Response

## Refined Intent
Validate PLR bit set/unset for coarse- and fine-grained thermal bits once thermal throttling is engaged/disengaged. Induce thermal throttling one source at a time (IMH uncore DTSes, CBB ring DTSes, CBB core DTSes) and verify PLR status bits reflect throttle state.

## Refined Test Steps
Pre-Conditions:
  - VF curve fuses programmed
  - Pmin set for all ratios
  - Model: MCP IC HSLE (uncores), MCP IC XOS (cores)

Step 1 — Induce thermal throttling via IMH uncore DTSes:
  Inject high temperature in IMH uncore DTSes.
  Check uncore/IO/Mem ratios throttled to lowest ratios.
  Check THERMAL PLR status bit SET via mailbox read.

Step 2 — Induce thermal throttling via CBB ring DTSes:
  Inject high temperature in CBB ring DTSes.
  Check for thermal throttle engagement.
  Check THERMAL PLR status bit SET.

Step 3 — Induce thermal throttling via CBB core DTSes:
  Inject high temperature in CBB core DTSes.
  Check core ratios drop to Pmin.
  Check Thermal Status bits in punit.throttle.
  Check THERMAL PLR status bit SET via mailbox.

Step 4 — Release thermal injection and verify recovery:
  Uninject all DTS overrides.
  Verify ratios recover from Pmin.
  Verify THERMAL PLR status bits CLEAR.

Pass/Fail Criteria:
  PASS: PLR thermal bits correctly set during each throttle source and cleared after de-assertion
  FAIL: PLR bits not reflecting thermal throttle state, or bits stuck after recovery

HAS/MAS References:
  - DMR Thermal HAS — Thermal PLR: https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/Thermals/DMR_Thermal.html
  - Perf Limit Reasons HAS — Thermal bits: https://docs.intel.com/documents/pm_doc/src/server/GNR/Features/perf_limit_reasons/perf_limit_reasons_has.html
  - Socket Thermal Mgmt HAS: https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Socket_Thermal_Mgmt/Socket_Thermal_Mgmt_HAS.html

### NWP Project Relevance
**Test Classification:** Regression (DMR-inherited)
**Feature Status:** Expected to work
**Test Purpose:** Validate PLR bit set/unset for coarse- and fine-grained thermal bits once thermal throttling is engaged/disengaged. Induce thermal throttling one source at a time (IMH uncore DTSes, CBB ring DTSes, CB
**Negative Test Aspect:** None
**NWP Delta:** Topology differences from DMR (2 CBB + 1 NIO); same SoC Thermal behavior expected

## Section A: Critical Execution Path
1. Step 1 — Induce thermal throttling via IMH uncore DTSes:
2. Step 2 — Induce thermal throttling via CBB ring DTSes:
3. Step 3 — Induce thermal throttling via CBB core DTSes:
4. Step 4 — Release thermal injection and verify recovery:

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
| PCUData | Yes | Primary interface |
| PLR | Yes | Primary interface |

## Section D: NWP Specification References
- **NWP PM HAS**: [NWP HAS - PM Features](https://docs.intel.com/documents/custom-xeon/newport-docs/has/Overview/NWP_HAS.html#pm-features)
- **NWP PM MAS**: [NWP IMH SoC PM MAS - Thermal](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html#thermal)
- **DMR PM HAS**: [DMR SoC PM HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/SOC_PM_HAS/DMR_SOC_PM_HAS.html)
- **Feature HAS**: [DMR Thermal HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/Features/Thermal/DMR_Thermal.html)
- **DMR CBB HAS**: [DMR CBB PM HAS - DTS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/IP%20Integration/PM%20HAS/cbb_pm_has.html#dts)
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