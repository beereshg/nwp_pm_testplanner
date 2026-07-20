# Deep Analysis: [ITD] Verify UCIe (VCCC2IA) ITD

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421536 |
| **Title** | [ITD] Verify UCIe (VCCC2IA) ITD |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | SoC Thermal Management > ITD |
| **Sub-Feature** | UCIe D2D (VCCC2IA) — CBB PCode |
| **NWP Disposition** | **Runnable_On_N-1** |

---


## Test Case Intent

Validates the UCIe VCCC2IA ITD compensation including boot-time one-time correction scenario defined in [TCD 16031170073 — Fabric/IO Rail ITD](https://hsdes.intel.com/appstore/article-one/#/16031170073) §5. Environment: NWP post-silicon, FV.

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

UCIe D2D Phy requires a **fixed voltage targeted to ~0.7V** with 40mV pk-pk AC noise tolerance at ≤16Gb/s. CBB PCode controls the TD compensation for UCIe to maintain this voltage despite temperature variations. There are two ITD events:
1. **Boot ITD** (PH2.40): One-time ITD calc from actual UCIe temp before D2D training — saves ~11.7% UCIe power
2. **Periodic ITD** (after PH2.52): Dynamic ITD tracking

NWP has UCIe D2D links (CBB-to-CBB and/or CBB-to-IMH). The VCCC2IA ITD mechanism is the same architecture. Primary adaptation: `dmr.xml` → `nwp.xml`.

**Key Justification:**
- UCIe D2D Phy ITD (VCCC2IA) is present on NWP
- Boot-time ITD for D2D training power optimization is the same mechanism
- Same AC noise budget (40mV pk-pk at 16Gb/s)
- `PMSS_NWP_READINESS_CHECK` tag: evaluated for NWP

---

## Section B: NWP-Specific Test Procedure

### Pre-Conditions
- NWP silicon with UCIe D2D links trained
- ITD fuses for UCIe (D2D_ITD_SLOPE/SLOPE_2, D2D_ITD_CUTOFF_V/V2) non-zero
- PythonSv access to `sv.socket0.cbb{0,1}.punit.*`

### Adapted Test Steps

| Step | Action | NWP Adaptation |
|------|--------|----------------|
| 1 | Run ITD thermal test | `python runPmx.py -x nwp.xml -p itd_thermal -tM 9 -M 3` |
| 2 | Verify Boot ITD (PH2.40): check D2D training used actual UCIe temperature | NWP: read pre-training UCIe DTS `PCU_CR_DTS_TEMP_SOC_CR[1:0]` |
| 3 | Verify periodic ITD: `itd.print_itd_info(0, 0)` shows VCCC2IA domain compensation | UCIe-specific fuses: `D2D_ITD_SLOPE`, `D2D_ITD_CUTOFF_V` |
| 4 | Read VCCC2IA RC voltage offset (should reflect current ITD compensation) | `RESCTRL_CR_C2IA_V_OFFSET` or equivalent in CBB punit |
| 5 | Verify AC noise margin maintained: VCCC2IA ±40mV from 0.7V target | Board-level or scope measurement (advanced) |

### NWP UCIe D2D Topology
- DMR: 4 CBBs, each with UCIe links to adjacent dies (D2D PHY)
- NWP: 2 CBBs with UCIe links; CBB-to-CBB and CBB-to-IMH
- Each CBB independently manages its VCCC2IA ITD

### NWP Pass Criteria
- VCCC2IA compensation non-zero at operating temperature
- Boot ITD applied before D2D training (verify via boot trace or fw_runtime_tracker log)
- Periodic ITD updates VCCC2IA voltage offset within slow-loop interval
- UCIe D2D training completes successfully with ITD-corrected voltage

---

## Section C: NWP Delta Impact Analysis

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| UCIe D2D topology | 4 CBBs, multi-die D2D links | 2 CBBs, CBB↔CBB + CBB↔IMH | Domain count differs; per-link mechanism same |
| Boot ITD (PH2.40) | D2D training ITD | Same phase structure | Same boot phase |
| DMR A0 D2D workaround | DVFS bypass, fixed boot voltage with ITD guardband | Workaround may persist or be fixed on NWP | Check NWP stepping for workaround status |
| Fuses | `D2D_ITD_SLOPE/SLOPE_2`, `D2D_ITD_CUTOFF_V/V2` | Same fuse names on NWP | Direct reuse |

---

## Section D: Key Registers & Validation Points

### PythonSv Validation Commands (NWP)

```python
from pm.focus import itd

SockNum = 0

# Print ITD info — VCCC2IA domain should appear
itd.print_itd_info(SockNum, 0)

# Per-CBB UCIe DTS
for cbb_idx in range(2):  # NWP: 2 CBBs
    cbb = getattr(sv.socket0, f'cbb{cbb_idx}')
    try:
        dts_c2ia = cbb.getbypath("punit.dts_temp_soc_cr").read()
        print(f"CBB{cbb_idx} DTS_SOC_CR (UCIe): 0x{dts_c2ia:08X}")
    except Exception as e:
        print(f"CBB{cbb_idx} UCIe DTS: {e}")

# VCCC2IA RC voltage offset
for cbb_idx in range(2):
    cbb = getattr(sv.socket0, f'cbb{cbb_idx}')
    try:
        c2ia_offset = cbb.getbypath("punit.resctrl_cr_c2ia_v_offset").read()
        print(f"CBB{cbb_idx} VCCC2IA V_OFFSET: {c2ia_offset}")
    except Exception as e:
        print(f"CBB{cbb_idx} C2IA: {e}")
```

---

## Section E: Risk Assessment & Open Items

| # | Risk/Open Item | Severity | Notes |
|---|----------------|----------|-------|
| 1 | **DMR A0 D2D workaround status on NWP** — DMR A0 had UCIe training errors from VCCIO DVFS; fixed boot voltage with ITD guardband was workaround; check if resolved on NWP | Medium | Verify NWP stepping-specific workaround applicability |
| 2 | **NWP UCIe D2D topology** — CBB↔IMH UCIe links may have different VCCC2IA ITD handling than CBB↔CBB | Low | Verify from NWP CFC/UCIe MAS |

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; check D2D workaround status**

UCIe D2D ITD is architecturally the same on NWP. Boot ITD and periodic ITD both apply. Verify DMR A0 workaround applicability on NWP stepping.

Required adaptations:
1. `python runPmx.py -x nwp.xml -p itd_thermal -tM 9 -M 3`
2. Check NWP stepping for DMR A0 UCIe DVFS workaround status
3. Confirm NWP UCIe D2D topology (CBB↔CBB vs CBB↔IMH VCCC2IA)

**Priority**: Medium — UCIe D2D power optimization and signal integrity critical for multi-die platforms
