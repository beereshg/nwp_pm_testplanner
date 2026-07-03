# Deep Analysis: ICCP — AVX 512 License Request and Grant Flow

| Field | Value |
|-------|-------|
| **HSD ID** | 22022422267 |
| **Title** | ICCP: AVX 512 License request and grant flow |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | Pstate Stack |
| **Sub-Feature** | ICCP — AVX-512 license grant and frequency limiting |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies the **AVX-512 ICCP license request and grant flow**: when a core executes AVX-512 (512-bit wide) instructions, frequency is limited to the AVX-512 turbo ratio limit table, and `IA_PERF_LIMIT_REASONS.AVX_STATUS` is set when clipped. AVX-512 is the widest SIMD (excluding AMX matrix) and imposes significant power, so the frequency cap is typically lower than AVX-256.

On NWP, AVX-512 is supported (NWP is an AI-optimized platform that heavily uses AVX-512 and AMX). ICCP license mechanism is the same.

**Key Justification:**
- AVX-512 is critical for NWP workloads (AI/inference)
- ICCP AVX-512 license mechanism present on NWP
- `Ready_for_testing` + `PMSS_NWP_READINESS_CHECK` tags
- Same grant flow as AVX-256 (TC 22022422266) but higher cdyn

---

## Section B: NWP-Specific Test Procedure

### AVX-512 Turbo Ratio Limits (TRL)

On DMR/NWP, AVX-512 TRL is typically per core count (group license):
- **1 core**: AVX-512 1-core TRL (highest)
- **All-core**: AVX-512 all-core TRL (lowest)
- License grants per execution unit type (512-wide FMA, etc.)

### Adapted Test Steps

| Step | Action | NWP Adaptation |
|------|--------|----------------|
| 1 | Configure BIOS: TurboMode = 1, EETurbo = 1 | Same knobs |
| 2 | Run AVX-512 turbo verification | `python runPmx.py -x nwp.xml -p turbo -tM 60` |
| 3 | Execute AVX-512 workload on varying core counts | turbo plug-in drives AVX-512 (zmm instructions) |
| 4 | Verify ICCP AVX-512 license granted | Read ICCP license register |
| 5 | Verify frequency clamped to AVX-512 ratio limit table | Check per-core ratio from `IA32_PERF_STATUS` |
| 6 | Verify PLR AVX_STATUS = 1 when clipped | Per-core PLR check |

### ICCP License Level Encoding (Standard Intel)

| Value | License Level |
|-------|---------------|
| 0x0 | Level 0 (no license needed / base) |
| 0x1 | Level 1 (AVX-128 light) |
| 0x2 | Level 2 (AVX-256 heavy / AVX-512 light) |
| 0x3 | Level 3 (AVX-512 heavy / AMX) |

### NWP Validation

```python
# NWP AVX-512 ICCP License Verification

# AVX-512 turbo ratio limit
try:
    avx512_trl = sv.socket0.imh0.punit.ptpcioregs.ptpcioregs.avx512_turbo_ratio_limit.read()
    print(f"AVX-512 Turbo Ratio Limit (1-core): 0x{avx512_trl:08X}")
except Exception as e:
    print(f"AVX-512 TRL: {e}")

# Compare AVX-512 TRL vs AVX-256 TRL vs base TRL
try:
    max_trl = sv.socket0.imh0.punit.ptpcioregs.ptpcioregs.max_ratio_limit.read()
    avx256_trl = sv.socket0.imh0.punit.ptpcioregs.ptpcioregs.avx256_turbo_ratio_limit.read()
    print(f"Ratio limits: base={max_trl}, AVX-256={avx256_trl}, AVX-512={avx512_trl}")
    print(f"Expected: base >= AVX-256 >= AVX-512 (descending by cdyn)")
except Exception as e:
    print(f"TRL compare: {e}")

# PLR AVX_STATUS per core (NWP: 2 CBBs × 48 cores)
for cbb_idx in range(2):
    cbb = getattr(sv.socket0, f'cbb{cbb_idx}')
    try:
        # Check first core in each CBB
        plr = cbb.compute0.cpu.module0.core0.ia_perf_limit_reasons.read()
        avx_status = (plr >> 18) & 1
        print(f"CBB{cbb_idx} core0 PLR.AVX_STATUS: {avx_status}")
    except Exception as e:
        print(f"CBB{cbb_idx} PLR: {e}")
```

### NWP Pass Criteria
- ICCP AVX-512 license granted when ZMM (512-bit) instructions executing
- Core frequency ≤ AVX-512 turbo ratio limit during AVX-512
- AVX-512 TRL ≤ AVX-256 TRL ≤ base TRL (ratio limit hierarchy preserved)
- `IA_PERF_LIMIT_REASONS.AVX_STATUS = 1` when frequency clipped by AVX-512 limit
- Frequency restores to AVX-256 or base when ZMM instructions stop

---

## Section C: NWP Delta Impact Analysis

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| AVX-512 support | Yes | Yes (critical for NWP AI) | Direct reuse |
| AVX-512 TRL values | DMR fuse values | NWP-specific (likely similar) | Verify NWP fuses |
| ICCP grant flow | Same | Same | Consistent with TC 262, 266 |
| Script XML | `dmr.xml` | `nwp.xml` | **Required change** |

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; AVX-512 critical for NWP AI workloads**

AVX-512 ICCP license verification is highest priority for NWP given its AI-inference workload focus.

Required adaptations:
1. `python runPmx.py -x nwp.xml -p turbo -tM 60`
2. Get NWP AVX-512 turbo ratio limit from NWP HAS/fuses
3. Verify TRL hierarchy: base ≥ AVX-256 ≥ AVX-512 (≥ AMX)

**Priority**: High — AVX-512 is primary workload instruction set on NWP; ICCP frequency limiting critical for power compliance
