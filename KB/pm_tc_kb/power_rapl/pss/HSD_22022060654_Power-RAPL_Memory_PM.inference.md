# Deep Analysis: Memory PM ZBB Negative Checks

| Field | Value |
|-------|-------|
| **HSD ID** | [22022060654](https://hsdes.intel.com/appstore/article-one/#/22022060654) |
| **Title** | Memory PM ZBB Negative Checks |
| **Segment** | PSS |
| **Target Program** | NWP (Newport) |
| **Feature** | Power / RAPL — Memory PM |
| **Val Environment** | virtual_platform, emulation |
| **Parent TCD** | [22022060621 — NWP ZBB Negative Validation](https://hsdes.intel.com/appstore/article-one/#/22022060621) |

---

## Test Case Intent

**Objective:** Verify that Memory PM features are correctly ZBB'd on NWP: MemClos (memory closed-loop power management), DRC (Dynamic Register Correction), and memory power states APD/PPD/LPM/SSR/SR must all be inaccessible. **Exception: CLTT with MR4 IS supported on NWP and must NOT be validated as ZBB'd.**

**Dual-Environment:** Runs on both VP (Simics — boot-time model) and emulation (HSLE — full hardware model).

### Pre-Conditions

| Pre-Condition | Expected State | Failure Indication |
|---------------|---------------|-------------------|
| Platform booted | NWP system accessible via PythonSV | Environment not booted |
| Memory controller initialized | TPMI / MC registers accessible | MC not initialized post-boot |
| DRC feature header accessible | DRC_FEATURE_AVAILABLE field readable | Register access gap |
| MemClos registers accessible | MemClos config register readable | TPMI not ready |

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|--------------------|
| 1 | Read DRC_FEATURE_AVAILABLE field from DRC header register | Returns 0 (DRC not supported on NWP) | Returns 1 — DRC unexpectedly enabled |
| 2 | Attempt to configure MemClos: write MemClos enable bit | Write has no effect; readback = 0 (MemClos configuration ignored) | MemClos enabled — unexpected on NWP |
| 3 | Read APD (Autonomous Power Down) enable register | APD enable = 0 (not supported) | APD enabled — unexpected on NWP |
| 4 | Read PPD (Precharge Power Down) enable register | PPD enable = 0 (not supported) | PPD enabled — unexpected on NWP |
| 5 | Read LPM (Low Power Mode) enable register | LPM enable = 0 (not supported) | LPM enabled — unexpected on NWP |
| 6 | Read SR (Self Refresh) extended power state registers | Extended SR power states (SSR/SR beyond base) = not supported | Extended SR active — unexpected |
| 7 | Verify CLTT MR4 is functional (NOT ZBB'd): confirm MR4 thermal read path active | CLTT MR4 thermal reads returning valid temperature data | CLTT MR4 broken — should NOT be ZBB'd on NWP |
| 8 | On emulation: trigger memory thermal event and verify CLTT responds | Memory throttling via CLTT engages correctly; no DRC/MemClos involvement | CLTT not responding or DRC engaged |

### Pass / Fail Criteria

**PASS:** DRC_FEATURE_AVAILABLE=0; MemClos write has no effect; APD/PPD/LPM/SSR/SR all report disabled; CLTT with MR4 remains functional.

**FAIL:** Any ZBB'd feature (DRC/MemClos/APD/PPD/LPM/SSR/SR) accessible; OR CLTT with MR4 broken (false negative — this should still work).

### Post-Process

Save: DRC header readback, MemClos config readback (pre/post write), APD/PPD/LPM register values, CLTT MR4 temperature sample (emulation), environment type.

### Reference Documents

- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) — Memory PM ZBB scope; CLTT MR4 support
- [DMR DDR5/MCR HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/IP_PM_Features/DMR_DDR5_MCR.html) — MemClos, DRC, APD/PPD/LPM definitions; MR4-based CLTT
- [Intel RAPL HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/RAPL/RAPL.html) — DRAM power management context
- [Memory PM KB](../../pm_features/power_rapl/memory_pm.md)

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

NWP does not support the DMR-era Memory PM features (MemClos, DRC, APD/PPD/LPM/SSR/SR). These were removed from NWP silicon scope. CLTT with MR4 is the only memory thermal management path retained. This test validates all ZBB'd features are inaccessible AND CLTT remains functional.

Tags: plc.zbb.p1, PMSS_NWP_READINESS_CHECK.

---

## Section B: NWP-Specific Test Procedure

### Memory PM ZBB Register Summary

| Feature | Register | Expected on NWP | ZBB? |
|---------|----------|----------------|------|
| DRC | DRC_FEATURE_AVAILABLE | 0 | Yes |
| MemClos | MemClos enable register | Write = no effect | Yes |
| APD | APD enable | 0 | Yes |
| PPD | PPD enable | 0 | Yes |
| LPM | LPM enable | 0 | Yes |
| SSR/SR (extended) | Extended SR power state regs | Not supported | Yes |
| CLTT with MR4 | MR4 thermal read path | Functional — temperature valid | **NO — supported** |

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Read DRC header | MC TPMI DRC header register DRC_FEATURE_AVAILABLE field |
| 2 | Write/readback MemClos | Write MemClos enable bit, verify readback = 0 |
| 3 | Read APD/PPD/LPM | MC power state config registers — expect 0 |
| 4 | Verify CLTT MR4 | On emulation: confirm MR4 thermal reads active |

### Pass Criteria

DRC=0; MemClos write no-op; APD/PPD/LPM=0; CLTT with MR4 functional.
