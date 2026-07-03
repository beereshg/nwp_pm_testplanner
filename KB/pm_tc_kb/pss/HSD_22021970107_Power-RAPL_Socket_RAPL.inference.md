# NWP PSS Analysis

## Metadata
- HSD ID: 22021970107
- Title: PEM - Socket RAPL PL2
- Feature: Power/RAPL
- Sub Feature: Socket RAPL
- Script: pm/pss/pmax/pmax_inject_cbb.py
- HSD Script: (none)
- TC Owner: isaxena
- TR Owner: mps
- Validation Environment: virtual_platform
- Test Cycle: Newport Product.trunk.pss_1p0.pss.val.NWP_VP
- NWP Scope: Runnable_On_N-1

## HSD Hierarchy
- Test Case Definition: [22021969919 - Socket RAPL](https://hsdes.intel.com/appstore/article/#/22021969919)
- Test Case: [22021970107 - PEM - Socket RAPL PL2](https://hsdes.intel.com/appstore/article/#/22021970107)
- Test Result: [22022027537 - [PSS][SOCKET_RAPL] PEM - Socket RAPL PL2](https://hsdes.intel.com/appstore/article/#/22022027537)

## KB References
- KB Article: [KB/pm_features/power_rapl/socket_rapl.md](../../../KB/pm_features/power_rapl/socket_rapl.md)

## Model Response

## Refined Intent
Verify whether RAPL throttles IPs when PL2 power limit is exceeded. RAPL algorithm is implemented in Primecode and enforces power consumed by SoC to within PL1/PL2. In NWP only Socket RAPL is implemented (DRAM RAPL and Platform RAPL are ZBB). BIOS, OS and FW are required for simulating end-to-end RAPL flow. MBVR Xtors provide power data as input to RAPL algorithm.

## Refined Test Steps
Pre-Conditions:
  - No special configuration required, boot with default fuses
  - BIOS knobs: PL2 enable, PL2 power limit, PL2 time window
  - Ingredients: BIOS, OS, Pcode

Step 1 — Request >Pn ratios:
  Request >Pn ratios on core/mesh on CBB and IMH dies.

Step 2 — Set Socket RAPL PL2 to low value:
  Set via BIOS (initial values) or TPMI (runtime) to a low value.
  Use Punit register: package_rapl_limit.pkg_pwr_lim_2 and pkg_pwr_lim_2_en.
  Ensure PL2 is consumed by Pcudata/TPMI.

Step 3 — Read Perf Status:
  Read socket RAPL Perf Status (package_rapl_perf_status.pwr_limit_throttle_ctr).
  Check socket power consumed and core/mesh ratios.

Step 4 — Repeat with other PL2 values:
  Program different PL2 values and re-check perf status.

Pass/Fail Criteria:
  PASS: RAPL perf status increments and core/mesh ratios throttle in response to PL2 violation
  FAIL: No perf status change or no throttling on PL2 violation

HAS/MAS References:
  - DMR RAPL Simplification HAS — PL2: https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_RAPL_Simplification.html#pl2-interface
  - Socket RAPL HAS (Wave3): https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Socket_RAPL/Socket_RAPL.html

### NWP Project Relevance
**Test Classification:** Regression (DMR-inherited)
**Feature Status:** Expected to work
**Test Purpose:** Verify whether RAPL throttles IPs when PL2 power limit is exceeded. RAPL algorithm is implemented in Primecode and enforces power consumed by SoC to within PL1/PL2. In NWP only Socket RAPL is implemen
**Negative Test Aspect:** None
**NWP Delta:** Topology differences from DMR (2 CBB + 1 NIO); same Power/RAPL behavior expected

## Section A: Critical Execution Path
1. Step 1 — Request >Pn ratios:
2. Step 2 — Set Socket RAPL PL2 to low value:
3. Step 3 — Read Perf Status:
4. Step 4 — Repeat with other PL2 values:

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
| MSR | Yes | Primary interface |
| SVID | Yes | Primary interface |
| TPMI_IB | Yes | Primary interface |
| 0x610 PKG_POWER_LIMIT | Yes | Register access |
| TPMI: package_rapl_limit (PL2) | Yes | TPMI interface |

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