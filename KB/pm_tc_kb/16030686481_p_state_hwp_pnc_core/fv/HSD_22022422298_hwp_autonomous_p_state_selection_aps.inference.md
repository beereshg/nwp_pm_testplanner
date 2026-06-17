# Deep Analysis: HWP Autonomous P-State Selection (APS)

| Field | Value |
|-------|-------|
| **HSD ID** | 22022422298 |
| **Title** | HWP Autonomous P-state Selection (APS) |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | Pstate Stack |
| **Sub-Feature** | HWP — Autonomous P-state Selection (APS) algorithm |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

**APS (Autonomous P-state Selection)** is the core HWP algorithm that dynamically selects core frequency based on real-time workload characteristics and EPP value. Key metrics:
- **Instantaneous Utilization (C0%)**: Percentage of time core is active
- **Instantaneous FreqUtil**: Product of frequency × C0%
- **IdleN**: Recent idle history metric
- **EPP (Energy Performance Preference)**: Guides performance vs power tradeoff

APS is a closed-loop utilization-based algorithm that runs in the PCode slow loop on each CBB core.

On NWP, HWP and APS are the same architecture. Primary adaptation: `dmr.xml` → `nwp.xml`; NWP topology (2 CBBs × 48 cores, no SMT).

**Key Justification:**
- HWP APS is present on NWP (server HWP)
- `DMR_PO` + `NGA_MAIN` tags: primary CI coverage
- `plc.feature.p2` tag: P-state P2 feature validation
- `PMSS_NWP_READINESS_CHECK` tag: evaluated for NWP

---

## Section B: NWP-Specific Test Procedure

### APS Algorithm Overview

```
Each slow loop:
1. Compute InstUtil = C0% of last epoch
2. Compute FreqUtil = Frequency × C0%
3. Apply EPP bias to target frequency selection
4. Select frequency within [min_perf, max_perf] HWP limits
5. Issue PEGA request to achieve target frequency
```

### Adapted Test Steps

| Step | Action | NWP Adaptation |
|------|--------|----------------|
| 1 | Enable HWP: `ProcessorHWPMEnable = 0x1` in BIOS | Same BIOS knob |
| 2 | Run HWP APS verification | `python runPmx.py -x nwp.xml -p hwpm_aps_check -tM 60` |
| 3 | Set EPP to Performance (EPP = 0): verify high C0% → high frequency granted | `IA32_HWP_REQUEST.ENERGY_PERFORMANCE_PREFERENCE = 0` |
| 4 | Set EPP to Power Saving (EPP = 255): verify low frequency granted even at high C0% | Same register, EPP = 255 |
| 5 | Measure InstUtil and verify frequency tracks utilization × EPP | APS telemetry from PCode |
| 6 | Verify per-core APS frequency selection (96 cores on NWP) | Per-core `IA32_PERF_STATUS` |

### Key Registers (NWP)

```python
# NWP HWP APS Verification

# Verify HWP enabled
try:
    hwp_en = sv.socket0.cbb0.compute0.cpu.module0.core0.ia32_pm_enable.read()
    print(f"IA32_PM_ENABLE (HWP): 0x{hwp_en:04X} (bit0=1 → HWP enabled)")
except Exception as e:
    print(f"HWP enable: {e}")

# Per-core HWP request register
for cbb_idx in range(2):
    cbb = getattr(sv.socket0, f'cbb{cbb_idx}')
    try:
        hwp_req = cbb.compute0.cpu.module0.core0.ia32_hwp_request.read()
        epp = (hwp_req >> 24) & 0xFF
        min_perf = hwp_req & 0xFF
        max_perf = (hwp_req >> 8) & 0xFF
        desired = (hwp_req >> 16) & 0xFF
        print(f"CBB{cbb_idx} core0 HWP_REQUEST: EPP={epp}, min={min_perf}, max={max_perf}, desired={desired}")
    except Exception as e:
        print(f"CBB{cbb_idx} HWP_REQ: {e}")

# APS instantaneous utilization from PCode (if exposed)
try:
    inst_util = sv.socket0.imh0.punit.ptpcioregs.ptpcioregs.instantaneous_utilization.read()
    print(f"Instantaneous Utilization: {inst_util}%")
except Exception as e:
    print(f"Inst Util: {e}")
```

### NWP Pass Criteria
- HWP APS correctly scales frequency with instantaneous C0%
- EPP = 0 (Performance): high utilization → max turbo frequency
- EPP = 255 (Power Save): high utilization → capped at lower frequency
- Frequency within `[IA32_HWP_REQUEST.min_perf, IA32_HWP_REQUEST.max_perf]` bounds
- No MCAs during APS frequency transitions

---

## Section C: NWP Delta Impact Analysis

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| HWP APS algorithm | Server HWP APS | Same on NWP | Direct reuse |
| SMT | 2 threads/core | Non-SMT (1/core) | Per-core (not per-thread) HWP requests |
| C0% computation | Per-logical thread | Per-physical core | Simplified (no SMT aggregation) |
| EPP source | OS/BIOS/PECI | Same | Direct reuse |
| Script XML | `dmr.xml` | `nwp.xml` | **Required change** |

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; APS algorithm identical, NWP non-SMT simplifies per-core tracking**

HWP APS verification is directly applicable on NWP with XML adaptation.

Required adaptations:
1. `python runPmx.py -x nwp.xml -p hwpm_aps_check -tM 60`
2. NWP: per-physical-core HWP requests (no thread aggregation)
3. 2 CBBs × 48 cores = 96 APS decision points per slow loop

**Priority**: High — `DMR_PO` + `NGA_MAIN`; HWP APS is the default OS-agnostic P-state algorithm
