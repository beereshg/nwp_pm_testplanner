# Deep Analysis: [ITD] Verify ACP (VccCore) ITD

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421522 |
| **Title** | [ITD] Verify ACP (VccCore) ITD |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | SoC Thermal Management > ITD |
| **Sub-Feature** | ACP (Autonomous Core Power) / VccCore |
| **NWP Disposition** | **Runnable_On_N-1** |

---


## Test Case Intent

Validates the VccCore (ACP/Acode) temperature-dependent voltage compensation scenario defined in [TCD 16031170072 — Core/Ring Rail ITD](https://hsdes.intel.com/appstore/article-one/#/16031170072) §5. Environment: NWP post-silicon, FV.

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

ACP (VccCore) ITD is controlled **autonomously by Acode** (per-core). Each core has an in-die FIVR fed by VccCore VR. Acode manages ITD+TTD simultaneously via: (1) periodic temperature readout folding voltage compensation into WP recalc, and (2) interrupt-based recalc when DTS crosses a threshold (non-sticky DTD bits). On NWP, PantherCove cores have the same Acode ITD architecture. NWP has 96 cores (2 CBBs × 48 cores) vs. DMR's structure, but the per-core Acode ITD mechanism is the same. Primary adaptation: `dmr.xml` → `nwp.xml`.

**Key Justification:**
- ACP (Acode) ITD for VccCore is present on NWP PantherCove cores
- Same 2-slope ITD algorithm with `VCCCORE_ITD_SLOPE/SLOPE_2` fuses
- `PMSS_NWP_READINESS_CHECK` tag: explicitly evaluated for NWP
- `DMR_PO` tag: silicon validation priority; WP test steps describe the Acode interrupt + periodic flow which is architecture-level (not DMR-specific)

---

## Section B: NWP-Specific Test Procedure

### Pre-Conditions
- NWP silicon platform with active cores (no SMT — NWP is non-SMT, 1 thread per core)
- ITD fuses non-zero (verified by TC 22022421521)
- PythonSv access to `sv.socket0.cbb0.*` and `sv.socket0.cbb1.*`

### Adapted Test Steps

| Step | Action | NWP Adaptation |
|------|--------|----------------|
| 1 | Run ITD thermal test with NWP config | `python runPmx.py -x nwp.xml -p itd_thermal -tM 9 -M 3` |
| 2 | Verify periodic ITD: read core DTS, calculate expected compensation, compare to FIVR output | NWP: 2 CBBs, 48 cores each; read `cbb0.module[0-7].compute[0-3]` DTS per core |
| 3 | Verify interrupt-based ITD: stress a core to trigger DTS DTD threshold crossing (±3°C) | Same mechanism; verify `CORE_PMA_CR_DTS_DDT_STICKY` non-sticky bits 0,1 |
| 4 | Verify ITD voltage compensation: `itd.print_itd_info(SockNum, 0)` shows non-zero offset | Same Python API; socket 0 |
| 5 | Verify MLC SSA FIVR uses same ITD fuses as core (see TC 22022421525) | Same architecture on NWP |

### NWP-Specific Topology Notes
- NWP: 2 CBBs (`cbb0`, `cbb1`), 48 cores each, single-threaded (no SMT)
- DMR: 4 CBBs, 32 cores each, no SMT
- Core namespace on NWP: `sv.socket0.cbb{0,1}.compute[0-3].module[0-11]` (estimate; verify during bring-up)

### NWP Pass Criteria
- ACP ITD active: `itd.print_itd_info(0, 0)` shows non-zero VCCCORE compensation
- Interrupt path: DTS ±3°C threshold crossing triggers fast recalc (~30-60 μS)
- Periodic path: compensation updated within ~300 μS
- FIVR output matches expected ITD calculation from fuse values

---

## Section C: NWP Delta Impact Analysis

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| Core count | 4 CBBs × 32 cores = 128 | 2 CBBs × 48 cores = 96 | Loop count differs; per-core mechanism identical |
| SMT | No | No | Same — single-threaded core ITD |
| Acode ITD mechanism | Per-core, autonomous | Same on NWP | Direct reuse |
| VCCCORE FIVR | In-die FIVR per core | Same on NWP | Same compensation path |
| XML config | `dmr.xml` | `nwp.xml` | **Must update** |

---

## Section D: Key Registers & Validation Points

### PythonSv Validation Commands (NWP)

```python
from pm.focus import itd

# Print ITD info for socket 0
SockNum = 0
itd.print_itd_info(SockNum, 0)

# Per-core DTS read (NWP cbb0 example — 48 cores per CBB)
for cbb_idx in range(2):  # NWP has 2 CBBs
    cbb = getattr(sv.socket0, f'cbb{cbb_idx}')
    print(f"=== CBB{cbb_idx} Core DTS ===")
    try:
        # Adapt to actual NWP core hierarchy
        for core_idx in range(48):
            try:
                dts = cbb.getbypath(f"compute[{core_idx // 12}].module[{core_idx % 12}].dts.temperature").read()
                print(f"  Core[{core_idx}] DTS: {dts} °C")
            except Exception:
                pass
    except Exception as e:
        print(f"CBB{cbb_idx}: {e}")
```

---

## Section E: Risk Assessment & Open Items

| # | Risk/Open Item | Severity | Notes |
|---|----------------|----------|-------|
| 1 | **NWP core hierarchy path** — exact namednodes path for NWP cores needs bring-up validation | Low | Use `sv.socket0.cbb0.search('dts', 'c')` to locate correct path |
| 2 | **NWP Acode ACP ITD fuse names** — fuse names assumed same as DMR; verify with NWP MAS | Low | `itd.print_itd_info` should expose values |

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; adapt core loop count**

ACP VccCore ITD is the same architecture on NWP. The only adaptation is the XML config and core count (96 vs 128).

Required adaptations:
1. `python runPmx.py -x nwp.xml -p itd_thermal -tM 9 -M 3`
2. Update per-core loop: 2 CBBs × 48 cores (not 4 CBBs × 32)
3. Verify NWP core DTS namednodes path during bring-up

**Priority**: Medium — DMR_PO; foundational ITD bring-up test
