# Deep Analysis: [ITD] Verify Core MLC SSA (VCC MLC SSA) ITD

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421525 |
| **Title** | [ITD] Verify Core MLC SSA (VCC MLC SSA) ITD |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | SoC Thermal Management > ITD |
| **Sub-Feature** | Core MLC SSA (VCC_MLC_SSA) — Core ACP (Acode) |
| **NWP Disposition** | **Runnable_On_N-1** |

---


## Test Case Intent

Validates the Core MLC SSA voltage domain ITD compensation scenario defined in [TCD 16031170074 — Memory/CFC Rail ITD](https://hsdes.intel.com/appstore/article-one/#/16031170074) §5. Environment: NWP post-silicon, FV.

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

In DMR's CBB DCM architecture, both Core and MLC voltages are driven by the same core FIVR, however the MLC SSA is driven by a **separate MLC SSA FIVR** (one FIVR for all MLC SRAMs in the CBB). PCode does not control the MLC SSA FIVR ITD directly — Core Acode manages it using the same ITD fuses as the core (VCCCORE ITD fuses). On NWP, the same DCM architecture applies: PantherCove cores have separate MLC SSA FIVRs controlled by Acode using shared core ITD fuses. Primary adaptation: `dmr.xml` → `nwp.xml`.

**Key Justification:**
- MLC SSA FIVR ITD via Acode is present on NWP (shared fuses with core)
- Same 2-slope ITD algorithm; uses `VCCCORE_ITD_SLOPE/SLOPE_2` fuses for MLC SSA
- `PMSS_NWP_READINESS_CHECK` tag: explicitly evaluated for NWP
- `DMR_PO` tag: silicon validation priority

---

## Section B: NWP-Specific Test Procedure

### Pre-Conditions
- NWP silicon with active cores (MLC SSA FIVR active when cores active)
- ITD fuses non-zero (same fuses as VccCore ITD — TC 22022421521)
- PythonSv access to NWP Acode interfaces

### Adapted Test Steps

| Step | Action | NWP Adaptation |
|------|--------|----------------|
| 1 | Run ITD thermal test | `python runPmx.py -x nwp.xml -p itd_thermal -tM 9 -M 3` |
| 2 | Verify MLC SSA FIVR ITD: read MLC SSA FIVR RC voltage offset | NWP: 2 CBBs; one MLC SSA FIVR per CBB |
| 3 | Confirm Acode uses same ITD fuses for Core and MLC SSA: `itd.print_itd_info(0, 0)` | Verify MLC SSA compensation matches core ITD calculation |
| 4 | Temperature stress: verify MLC SSA voltage compensation updates with core temperature | Same interrupt + periodic path as VccCore ITD |
| 5 | (Future) Note: fuses may split between Core and MLC SSA in future TR — monitor | Track NWP MAS for any fuse split decision |

### NWP Pass Criteria
- MLC SSA FIVR RC voltage offset matches core ITD compensation (same fuses)
- Acode manages MLC SSA ITD via same autonomous mechanism as VccCore
- ITD compensation applied within ~300 μS (periodic) or ~30-60 μS (interrupt)

---

## Section C: NWP Delta Impact Analysis

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| MLC SSA FIVR | One per CBB × 4 CBBs | One per CBB × 2 CBBs | Domain count halved |
| ITD fuses | Shared with VccCore | Same on NWP | No change |
| Acode control | Per-core autonomous | Same | Direct reuse |
| Future fuse split | Possible (TR note) | Same open item | Monitor NWP MAS |

---

## Section D: Key Registers & Validation Points

### PythonSv Validation Commands (NWP)

```python
from pm.focus import itd

# Print ITD info — MLC SSA domains should appear alongside core
itd.print_itd_info(0, 0)

# MLC SSA FIVR RC offset (one per CBB on NWP)
for cbb_idx in range(2):  # NWP: 2 CBBs
    cbb = getattr(sv.socket0, f'cbb{cbb_idx}')
    try:
        mlcssa_offset = cbb.getbypath("resctrl_cr_vmlcssa_offset").read()
        print(f"CBB{cbb_idx} MLC_SSA V_OFFSET: 0x{mlcssa_offset:08X}")
    except Exception as e:
        print(f"CBB{cbb_idx} MLC_SSA: {e}")
```

---

## Section E: Risk Assessment & Open Items

| # | Risk/Open Item | Severity | Notes |
|---|----------------|----------|-------|
| 1 | **Fuse split possibility** — DMR test steps note "may split later"; NWP design may or may not split Core/MLC SSA ITD fuses | Low | Confirm from NWP PCode MAS before test execution |
| 2 | **MLC SSA namednodes path** — RC offset register name for MLC SSA may differ on NWP | Low | Locate via namednodes search during bring-up |

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; adapt CBB count**

MLC SSA ITD is the same architecture on NWP. Fuse sharing with VccCore remains; adapt domain count for 2 CBBs.

Required adaptations:
1. `python runPmx.py -x nwp.xml -p itd_thermal -tM 9 -M 3`
2. Loop over 2 CBBs (not 4) for MLC SSA FIVR RC offset reads
3. Confirm NWP MAS for any fuse split decision between Core and MLC SSA

**Priority**: Medium — DMR_PO; secondary to VccCore ITD but same fuse set
