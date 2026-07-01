# Deep Analysis: Legacy Pstate Scenarios — Core Random Frequency With Traffic

| Field | Value |
|-------|-------|
| **HSD ID** | 22022422228 |
| **Title** | Legacy Pstate Scenarios: core random frequency with traffic |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | Pstate Stack |
| **Sub-Feature** | Legacy P-states with concurrent I/O or memory traffic |
| **NWP Disposition** | **Runnable_On_N-1** |

---

### Test Case Intent

Verify **random per-core P-state requests under concurrent IO/memory traffic**: PEGA voting resolves to max-requested ratio; executed ratio achievable under load; no unexpected RAPL/thermal throttle during ratio verification. `pm.xproducts.traffic` cross-product. NWP: 2 CBBs × 48 cores; HWP disabled. `NGA_MAIN` priority.

---

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| SV session | `sv.socket0.imh0` and CBBs reachable |
| HWP | Disabled (`ProcessorHWPMEnable = 0`) |
| Traffic tools | memicals or supercollider available in NWP environment |
| PMx | `python runPmx.py -x nwp.xml -p pstates_check -p cpu_traffic -tM 6` |

---

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|----------------------|-------------------|
| 1 | Verify HWP disabled; start memory/IO traffic. `import time; # start memicals or supercollider; time.sleep(5)` | Traffic running; no RAPL/thermal throttle visible | Traffic not starting — check tool installation |
| 2 | Issue random per-core P-state requests across all 96 NWP cores under traffic. `python runPmx.py -x nwp.xml -p pstates_check -p cpu_traffic -tM 6` | PEGA resolves to max-requested ratio; PMx PASS | PMx FAIL — collect log |
| 3 | Verify executed ratio per core via IA32_PERF_STATUS with traffic running. | Executed ratio matches PEGA resolved ratio under load | Ratio lower than requested — unexpected RAPL/thermal throttle |
| 4 | Stop traffic; verify ratio returns to autonomous. | No residual throttle after traffic stops | Stuck ratio — debug RAPL/thermal state |

---

### Pass / Fail Criteria

- **PASS**: Random per-core P-state requests resolve correctly under traffic; no unexpected throttle; PMx PASS.
- **FAIL**: Ratio mismatch under traffic; unexpected RAPL/thermal limiting; PMx FAIL.

---

### Health Checks

| Register / Log | Access | Pass/Fail Criteria |
|----------------|--------|-------------------|
| IA32_PERF_STATUS | Per-core MSR 0x198 | Executed ratio = PEGA resolved under traffic |
| perf_limit_reasons | sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.perf_limit_reasons | No unexpected RAPL/thermal PLR during ratio check |

---

### Post-Process

Stop traffic. Collect PMx log on failure. Verify no residual PLR bits.

---

### References

- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) — NWP PEGA; traffic cross-product; ratio enforcement

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test exercises **random per-core P-state requests while concurrent traffic** (I/O or memory) is running. The traffic creates load pressure that interacts with P-state resolution. Pre-condition: HWP disabled. The test verifies PEGA voting with per-core random P-state requests and confirms the resolved ratio is achievable under load.

On NWP, the same test applies — PEGA voting with random per-core requests under traffic. Primary adaptation: `dmr.xml` → `nwp.xml`.

**Key Justification:**
- PEGA voting under traffic load applicable on NWP
- `pm.xproducts.traffic` cross-product: memory or I/O load required
- `DMR_PO` + `NGA_MAIN`: primary CI coverage
- `PMSS_NWP_READINESS_CHECK` tag: evaluated for NWP

---

## Section B: NWP-Specific Test Procedure

### Adapted Test Steps

| Step | Action | NWP Adaptation |
|------|--------|----------------|
| 1 | Verify HWP disabled | Same (`ProcessorHWPMEnable = 0`) |
| 2 | Start memory/IO traffic (cpu_traffic plug-in) | Same traffic patterns (memicals or supercollider) |
| 3 | Issue random P-states per core | `python runPmx.py -x nwp.xml -p pstates_check -p cpu_traffic -tM 6` |
| 4 | Collect ratios (P1, P0, Pm) from IMH, CBB, MSR, TPMI | 2 CBBs × 48 cores |
| 5 | Issue random per-core P-state requests | Verify PEGA resolves to max-requested ratio |
| 6 | Confirm ratio achievable under traffic load | Check for unexpected throttle during verification |

### NWP Traffic Configuration
- Memory traffic: DIMM traffic (NWP has DDR5 or HBM depending on SKU)
- IO traffic: PCIe or D2D traffic
- Verify NWP traffic modules compatible with NWP `nwp.xml` configuration

### NWP Pass Criteria
- Random per-core P-state requests correctly resolved by PEGA voting
- Resolved ratio achievable under concurrent traffic (no unexpected RAPL/thermal throttle)
- `IA32_PERF_STATUS` per core matches expected resolution
- No test failures due to traffic-induced RAPL limits (unless RAPL cross-product test)

---

## Section C: NWP Delta Impact Analysis

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| CBB count | 4 | 2 | Script covers via XML |
| Cores per CBB | 32 | 48 | Script covers via XML |
| Traffic modules | DMR traffic config | NWP traffic config | Verify `cpu_traffic` plug-in works with NWP |
| Script XML | `dmr.xml` | `nwp.xml` | **Required change** |

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; verify traffic plug-in compatibility**

Random P-states under traffic is directly applicable. Primary risk: traffic plug-in may need NWP config.

Required adaptations:
1. `python runPmx.py -x nwp.xml -p pstates_check -p cpu_traffic -tM 6`
2. Verify `cpu_traffic` plug-in targets NWP memory/IO correctly
3. NWP: 96 cores, non-SMT — script handles via `nwp.xml`

**Priority**: High — `DMR_PO` + `NGA_MAIN`; P-state + traffic cross-product
