# Deep Analysis: Legacy_Pstate_through_MSR

| Field | Value |
|-------|-------|
| **HSD ID** | 22022422224 |
| **Title** | Legacy_Pstate_through_MSR |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | Pstate Stack |
| **Sub-Feature** | Legacy P-states via IA32_PERF_CTL / IA32_PERF_STATUS MSRs |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies **legacy OS P-states** using MSR interface (`IA32_PERF_CTL` 0x199 / `IA32_PERF_STATUS` 0x198). Pre-condition: HWP must be disabled (`ProcessorHWPMEnable = 0`). The test then:
1. Collects P1, P0, Pm ratios from CBB, IMH, MSR, TPMI
2. Issues per-core P-states via `IA32_PERF_CTL`
3. Verifies voting rights determine resolved ratio
4. Confirms resolved ratio observable in `IA32_PERF_STATUS`

On NWP, same MSR-based legacy P-state mechanism exists. Primary adaptation: `dmr.xml` → `nwp.xml`, update core loop to NWP topology (2 CBBs × 48 cores, no SMT).

**Key Justification:**
- `IA32_PERF_CTL` / `IA32_PERF_STATUS` are x86 architectural MSRs present on NWP
- Same ratio verification logic across CBB, IMH, MSR, TPMI
- `DMR_PO` tag: silicon validation bring-up priority
- `NGA_MAIN` tag: primary CI/regression coverage

---

## Section B: NWP-Specific Test Procedure

### Key MSRs

| MSR | Address | Function | NWP |
|-----|---------|----------|-----|
| `IA32_PERF_CTL` | 0x199 | Write target ratio (OS P-state request) | Same |
| `IA32_PERF_STATUS` | 0x198 | Read current executed ratio | Same |
| `IA32_MISC_ENABLES[16]` | 0x1A0 | HWP must be 0 (SpeedStep enabled for legacy mode) | Same |
| `MISC_PWR_MGMT` | 0x1AA | Single-thread PCTL coordination | Same |

### Adapted Test Steps

| Step | Action | NWP Adaptation |
|------|--------|----------------|
| 1 | Verify HWP disabled (BIOS knob `ProcessorHWPMEnable = 0`) | Same; verify `IA32_PM_ENABLE.HWP_ENABLE = 0` |
| 2 | Run P-state check | `python runPmx.py -x nwp.xml -p pstates_check -tM 6` |
| 3 | Collect P1, P0, Pm ratios from registers | IMH: `sv.socket0.imh0.*`; CBBs: `cbb0`, `cbb1` (2 CBBs) |
| 4 | Cross-check ratios: CBB == IMH == MSR == TPMI | Same verification |
| 5 | Issue per-core P-states via `IA32_PERF_CTL` | 96 cores (2 CBBs × 48) |
| 6 | Read `IA32_PERF_STATUS` per core | Verify resolved ratio matches requested |

### NWP Pass Criteria
- HWP disabled confirmed before test
- Ratios consistent across all register sources (CBB, IMH, MSR, TPMI)
- `IA32_PERF_STATUS.CURRENT_PERF` matches `IA32_PERF_CTL` request
- PEGA voting correctly resolves per-core requests to package maximum

---

## Section C: NWP Delta Impact Analysis

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| CBB count | 4 | **2** | Script XML change covers this |
| Cores per CBB | 32 | **48** | Script XML change covers this |
| SMT | Yes (2 threads/core) | **No** (non-SMT) | 96 physical cores total (not 128 logical) |
| `IA32_PERF_CTL` per thread | Per logical thread | Per physical core | Simplified: 1 write per core |
| Script XML | `dmr.xml` | `nwp.xml` | **Required change** |

---

## Section D: Key Registers & Validation Points

```python
# NWP Legacy P-state MSR verification

# Check HWP status first
try:
    hwp_en = sv.socket0.cbb0.compute0.cpu.module0.core0.ia32_pm_enable.read()
    print(f"IA32_PM_ENABLE (HWP): 0x{hwp_en:04X} (bit0=0 → HWP disabled → legacy mode)")
except Exception as e:
    print(f"HWP check: {e}")

# Check package ratios from IMH
try:
    p0 = sv.socket0.imh0.punit.ptpcioregs.ptpcioregs.max_ratio_limit.read()
    p1 = sv.socket0.imh0.punit.ptpcioregs.ptpcioregs.p1_ratio.read()
    pm = sv.socket0.imh0.punit.ptpcioregs.ptpcioregs.min_perf_ratio.read()
    print(f"IMH: P0={p0}, P1={p1}, Pm={pm}")
except Exception as e:
    print(f"IMH ratios: {e}")

# Per-core PERF_STATUS sample (NWP: 2 CBBs × 48 cores)
for cbb_idx in range(2):
    cbb = getattr(sv.socket0, f'cbb{cbb_idx}')
    for compute_idx in range(4):
        for module_idx in range(12):  # 48 cores = 4 computes × 12 modules
            try:
                perf_status = cbb.getbypath(
                    f"compute[{compute_idx}].module[{module_idx}].core0.ia32_perf_status"
                ).read()
                current_ratio = (perf_status >> 8) & 0xFF
                if current_ratio > 0:
                    print(f"CBB{cbb_idx} C{compute_idx}M{module_idx}: PERF_STATUS ratio={current_ratio}")
            except Exception:
                pass
```

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; non-SMT loop simplification**

Legacy P-state MSR verification is directly applicable on NWP with XML adaptation.

Required adaptations:
1. `python runPmx.py -x nwp.xml -p pstates_check -tM 6`
2. NWP script must iterate 2 CBBs (not 4), 48 cores/CBB (not 32), no thread index
3. Verify BIOS has `ProcessorHWPMEnable = 0` before test

**Priority**: High — `DMR_PO` + `NGA_MAIN`; primary legacy P-state validation path
