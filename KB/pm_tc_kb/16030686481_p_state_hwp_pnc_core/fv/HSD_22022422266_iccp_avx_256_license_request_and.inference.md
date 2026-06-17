# Deep Analysis: ICCP — AVX 256 License Request and Grant Flow

| Field | Value |
|-------|-------|
| **HSD ID** | 22022422266 |
| **Title** | ICCP: AVX 256 License request and grant flow |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | Pstate Stack |
| **Sub-Feature** | ICCP — AVX-256 license grant and frequency limiting |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies the **AVX-256 ICCP license request and grant flow**: when a core executes AVX-256 (256-bit wide) instructions, frequency is limited to the AVX-256 turbo ratio limit table, and `IA_PERF_LIMIT_REASONS.AVX_STATUS` is set when clipped.

On NWP, AVX-256 is supported and the ICCP license mechanism is the same as DMR. Primary adaptation: `dmr.xml` → `nwp.xml`.

**Key Justification:**
- AVX-256 instructions supported on NWP
- ICCP AVX-256 license mechanism present on NWP
- `Ready_for_testing` + `PMSS_NWP_READINESS_CHECK` tags
- Same ICCP grant flow as AMX (TC 22022422262) but lower cdyn level

---

## Section B: NWP-Specific Test Procedure

### AVX License Hierarchy

| License Level | Instructions | cdyn | Frequency Impact |
|---------------|-------------|------|-----------------|
| Base/Normal | SSE/scalar | Low | No clipping |
| AVX-128 | 128-bit AVX | Medium | Minor clip or none |
| AVX-256 | 256-bit AVX (Heavy) | High | AVX-256 turbo ratio limit |
| AMX | AMX TMUL | Highest | AMX turbo ratio limit (lowest freq) |

### Adapted Test Steps

| Step | Action | NWP Adaptation |
|------|--------|----------------|
| 1 | Configure BIOS: TurboMode = 1, EETurbo = 1 | Same knobs |
| 2 | Run AVX-256 turbo verification | `python runPmx.py -x nwp.xml -p turbo -tM 60` |
| 3 | Execute AVX-256 workload on test core | turbo plug-in drives AVX-256 execution |
| 4 | Verify ICCP AVX-256 license granted | Read ICCP license register |
| 5 | Verify frequency clamped to AVX-256 ratio limit | `IA32_PERF_STATUS` per core |
| 6 | Verify PLR AVX_STATUS = 1 when frequency clipped | Read per-core PLR |

### NWP Validation

```python
# NWP AVX-256 ICCP License Verification

# AVX-256 turbo ratio limit (from fuses or TPMI)
try:
    avx256_trl = sv.socket0.imh0.punit.ptpcioregs.ptpcioregs.avx256_turbo_ratio_limit.read()
    print(f"AVX-256 Turbo Ratio Limit: 0x{avx256_trl:08X}")
except Exception as e:
    print(f"AVX256 TRL: {e}")

# Per-core PLR check (NWP: 2 CBBs × 48 cores)
for cbb_idx in range(2):
    cbb = getattr(sv.socket0, f'cbb{cbb_idx}')
    for compute_idx in range(4):
        try:
            plr = cbb.getbypath(
                f"compute[{compute_idx}].cpu.module0.core0.ia_perf_limit_reasons"
            ).read()
            avx_status = (plr >> 18) & 1  # AVX status bit (verify bit position for NWP)
            if avx_status:
                print(f"CBB{cbb_idx} C{compute_idx}: PLR AVX_STATUS=1 (frequency clipped by AVX-256 limit)")
        except Exception:
            pass
```

### NWP Pass Criteria
- ICCP AVX-256 license granted when AVX-256 code running
- Core frequency ≤ AVX-256 turbo ratio limit during AVX-256 execution
- `IA_PERF_LIMIT_REASONS.AVX_STATUS = 1` when clipped
- Frequency restores when AVX-256 code stops

---

## Section C: NWP Delta Impact Analysis

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| AVX-256 support | Yes | Yes | Direct reuse |
| AVX-256 turbo ratio limit | DMR fuse values | NWP-specific values | Verify NWP AVX-256 TRL fuses |
| ICCP grant flow | Same as AMX TC 262 | Same | Consistent |
| Script XML | `dmr.xml` | `nwp.xml` | **Required change** |

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; get NWP AVX-256 turbo ratio limit values**

AVX-256 ICCP license verification is directly applicable on NWP.

Required adaptations:
1. `python runPmx.py -x nwp.xml -p turbo -tM 60`
2. Get NWP AVX-256 turbo ratio limit from NWP HAS/fuses
3. Verify PLR AVX_STATUS bit position consistent with NWP

**Priority**: Medium — `Ready_for_testing`; AVX-256 ICCP license validation
