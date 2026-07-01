# Deep Analysis: Core Pstates Through PEGA

| Field | Value |
|-------|-------|
| **HSD ID** | 22022422222 |
| **Title** | Core Pstates through PEGA |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | Pstate Stack |
| **Sub-Feature** | P-states via PEGA interface |
| **NWP Disposition** | **Runnable_On_N-1** |

---

### Test Case Intent

Verify **core P-states through PEGA** (P-state Engine for GV Approval) interface: collect P1/P0/Pm ratios from CBB/IMH/MSR/TPMI; issue per-core P-state requests; confirm PEGA voting resolves to expected ratio; verify executed ratio observable in cores. NWP: 2 CBBs × 48 cores = 96 cores (no SMT); single IMH (imh0); adapt core loop from DMR range.

---

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| SV session | `sv.socket0.imh0` and `sv.socket0.cbb{0,1}` reachable |
| PMx | `python runPmx.py -x nwp.xml -p pstates_check -tM 6` available |
| BIOS | SpeedStep enabled; HWP disabled (`ProcessorHWPMEnable = 0`) |
| NWP topology | 2 CBBs (cbb0, cbb1); 48 cores per CBB; no SMT |

---

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|----------------------|-------------------|
| 1 | Collect P1, P0, Pm ratios from IMH. `p1=sv.socket0.imh0.punit.ptpcioregs.ptpcioregs.min_perf_ratio.read(); p0=sv.socket0.imh0.punit.ptpcioregs.ptpcioregs.max_perf_ratio.read(); print(f'P0={p0} P1={p1}')` | P0 >= P1 > 0; ratios match fused TDP/turbo values | P0 or P1 = 0 — ratio registers not initialized |
| 2 | Collect ratios from CBB0 and CBB1; verify consistency with IMH. `for i in [0,1]: max_r=sv.socket0.cbb[i].base.ptpcioregs.max_perf_ratio.read(); print(f'CBB{i} max_ratio={max_r}')` | CBB P0/P1 ratios consistent with IMH; no mismatch | Ratio mismatch — PEGA init failure |
| 3 | Issue per-core P-state requests across all 96 NWP cores; verify PEGA voting resolves to max-requested ratio. `python runPmx.py -x nwp.xml -p pstates_check -tM 6` | PMx PASS; PEGA voting resolves correctly | PMx FAIL — collect log |
| 4 | Verify executed ratio per core via APERF/MPERF or PEGA feedback register. | Per-core executed ratio matches PEGA resolved ratio | Core stuck at wrong ratio |

---

### Pass / Fail Criteria

- **PASS**: Ratios collected correctly; PEGA voting resolves to max-requested; executed ratio observable; PMx pstates_check PASS.
- **FAIL**: Ratio mismatch; PEGA voting incorrect; PMx FAIL.

---

### Health Checks

| Register / Log | Access | Pass/Fail Criteria |
|----------------|--------|-------------------|
| max_perf_ratio | sv.socket0.imh0.punit.ptpcioregs.ptpcioregs.max_perf_ratio | = P0 turbo ratio |
| min_perf_ratio | sv.socket0.imh0.punit.ptpcioregs.ptpcioregs.min_perf_ratio | = P1 base ratio |
| PEGA_REQ resolved | sv.socket0.cbb{0,1} PEGA register | Max-requested wins |
| IA32_PERF_STATUS | Per-core MSR 0x198 | Executed ratio matches PEGA |

---

### Post-Process

Collect PMx log on failure. Verify no residual throttle (RAPL/thermal) affecting ratios.

---

### References

- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) — NWP P-state / PEGA topology; 2 CBBs; 96 cores
- [NWP PM MAS — P-state](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) — PEGA voting; ratio registers; core P-state enforcement

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies core P-states through the **PEGA** (P-state Engine for GV Approval) interface. PEGA is the internal P-state request pathway from cores to PCode. The test collects P1, P0, Pm ratios from CBB, IMH, MSR, TPMI registers; issues different P-states per core; verifies voting rights determine resolved ratio; and confirms resolved ratio is observable in cores.

On NWP, PEGA is the same mechanism. NWP has 2 CBBs × 48 cores (96 cores total) vs DMR's 4 CBBs × 32 cores × 2 threads. Primary adaptation: `dmr.xml` → `nwp.xml` and update core loop to NWP topology.

**Key Justification:**
- PEGA P-state mechanism present on NWP
- Same ratio reporting registers (CBB, IMH, MSR, TPMI)
- `DMR_PO` tag: silicon validation bring-up priority
- `PMSS_NWP_READINESS_CHECK` tag: evaluated for NWP

---

## Section B: NWP-Specific Test Procedure

### Adapted Test Steps

| Step | Action | NWP Adaptation |
|------|--------|----------------|
| 1 | Run P-state check via runPmx | `python runPmx.py -x nwp.xml -p pstates_check -tM 6` |
| 2 | Collect P1, P0, Pm ratios from IMH | `sv.socket0.imh0.punit.ptpcioregs.ptpcioregs.min_perf_ratio`, `.max_perf_ratio` |
| 3 | Collect ratios from CBB (each CBB) | 2 CBBs: `sv.socket0.cbb0`, `sv.socket0.cbb1` |
| 4 | Verify ratios consistent between IMH and CBB | Cross-check |
| 5 | Issue per-core P-state requests (96 cores) | Loop over 2 CBBs × 48 cores |
| 6 | Verify PEGA voting yields expected resolved ratio | Check `PEGA_REQ` register resolved value |
| 7 | Confirm per-core executed ratio | `APERF`/`MPERF` sampling or PEGA feedback register |

### NWP Topology

```python
# NWP P-state PEGA verification
# 2 CBBs × 48 cores = 96 physical cores (no SMT)

for cbb_idx in range(2):
    cbb = getattr(sv.socket0, f'cbb{cbb_idx}')
    print(f"\n--- CBB{cbb_idx} P-state ratios ---")
    try:
        p0 = cbb.base.punit_regs.punit_gpsb.gpsb_infvnn_crs.max_perf_ratio.read()
        p1 = cbb.base.punit_regs.punit_gpsb.gpsb_infvnn_crs.p1_ratio.read()
        pm = cbb.base.punit_regs.punit_gpsb.gpsb_infvnn_crs.min_perf_ratio.read()
        print(f"  P0={p0}, P1={p1}, Pm={pm}")
    except Exception as e:
        print(f"  CBB{cbb_idx} ratios: {e}")
```

### NWP Pass Criteria
- P1, P0, Pm ratios consistent between IMH, CBB, MSR, TPMI registers
- PEGA voting logic correctly resolves to maximum requested ratio
- Per-core executed ratio matches expected resolved ratio
- No cores stuck at lower ratio than requested

---

## Section C: NWP Delta Impact Analysis

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| CBB count | 4 | 2 | Loop `range(2)` not `range(4)` |
| Cores per CBB | 32 (non-SMT) | 48 | Update core iteration count |
| PEGA mechanism | DMR PEGA | NWP PEGA (same architecture) | Same verification logic |
| Script XML | `dmr.xml` | `nwp.xml` | **Required change** |

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; update CBB/core topology**

PEGA P-state verification is directly applicable on NWP. Script adapts via XML change.

Required adaptations:
1. `python runPmx.py -x nwp.xml -p pstates_check -tM 6`
2. Update CBB loop: 2 CBBs (not 4), 48 cores per CBB (not 32)
3. No thread iteration (NWP is non-SMT)

**Priority**: High — `DMR_PO`; foundational P-state bring-up verification
