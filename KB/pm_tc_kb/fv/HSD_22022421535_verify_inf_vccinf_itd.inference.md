# Deep Analysis: [ITD] Verify Inf (VccInf) ITD

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421535 |
| **Title** | [ITD] Verify Inf (VccInf) ITD |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | SoC Thermal Management > ITD |
| **Sub-Feature** | VccInf (MBVR) — iMH PrimeCode |
| **NWP Disposition** | **Runnable_On_N-1** |

---


## Test Case Intent

Validates the VccInf (Primecode) ITD compensation scenario defined in [TCD 16031170073 — Fabric/IO Rail ITD](https://hsdes.intel.com/appstore/article-one/#/16031170073) §5. Environment: NWP post-silicon, FV.

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

VccInf is the **only MBVR** (multi-die bypass VR) where ITD occurs in DMR/NWP. Root IMH PrimeCode alone does the ITD correction using the Dispatcher WP → SVID Controller. Because VccInf is shared across IMH and CBB dies, the control requires min temperature across all dies — CBBs send their min temperature to IMH via the `SOCKET_THERMAL` HPM message. VccInf is non-GV (fixed-frequency) — baseline voltage comes from `ACTIVE_VID` fuse.

Sub_feature is `To_be_ported` indicating script porting needed. The test steps include an OPEN item about defining the Vccinf temperature telemetry interface between CBB and iMH (via HPM or dedicated path). On NWP, this architecture is the same but any OPEN items from DMR may or may not be resolved for NWP.

**Key Justification:**
- VccInf ITD via iMH PrimeCode is present on NWP
- CBB → IMH min temperature via `SOCKET_THERMAL` HPM same architecture
- `To_be_ported` and OPEN items require NWP team coordination
- Single IMH on NWP simplifies the flow slightly (no imh1 to coordinate)

---

## Section B: NWP-Specific Test Procedure

### Pre-Conditions
- NWP silicon with VccInf MBVR active
- ITD fuses for VccInf non-zero (from TC 22022421521: `pcode_itd_cutoff_tj`, etc.)
- `SOCKET_THERMAL` HPM from CBBs delivering min temperature to iMH

### Adapted Test Steps

| Step | Action | NWP Adaptation |
|------|--------|----------------|
| 1 | Run ITD thermal test | `python runPmx.py -x nwp.xml -p itd_thermal -tM 9 -M 3` |
| 2 | Verify CBB → iMH temperature reporting via `SOCKET_THERMAL` HPM | NWP: 2 CBBs sending min temp; iMH receives and uses minimum |
| 3 | Verify VccInf ITD compensation: `itd.print_itd_info(0, 0)` shows VccInf domain | Check VccInf compensation = `ITD_SLOPE * (CUTOFF_V - ACTIVE_VID) * (CUTOFF_TJ - MIN_TEMP)` |
| 4 | Stress CBB to change temperature; verify iMH updates VccInf SVID target | Verify SVID target changes within slow-loop interval |
| 5 | Check OPEN: confirm VccInf temperature telemetry path finalized for NWP | Coordinate with NWP iMH team |

### VccInf ITD Formula (non-GV domain)

```
# VccInf is fixed-frequency (non-GV):
# Baseline = ACTIVE_VID fuse
# ITD compensation adds to baseline:
DELTA_TEMP_COLD = ITD_CUTOFF_TJ - MIN_TEMP_ACROSS_ALL_DIES
DELTA_VOLT = ITD_CUTOFF_V - ACTIVE_VID
VOLT_COMP = ITD_SLOPE * DELTA_VOLT * DELTA_TEMP_COLD
VCCINF_TARGET = ACTIVE_VID + VOLT_COMP
```

### NWP Pass Criteria
- VccInf SVID target tracks temperature across all dies
- `SOCKET_THERMAL` HPM delivers correct min temp from each CBB to iMH
- VccInf ITD compensation is non-zero at expected operating temperature

---

## Section C: NWP Delta Impact Analysis

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| VccInf control | iMH PrimeCode (root) | Same — single iMH on NWP | Simpler: no imh1 coordination |
| CBB count sending min temp | 4 CBBs | 2 CBBs | Temperature min-tracking simpler |
| Temperature telemetry OPEN | HPM path being defined | NWP must resolve same OPEN | Check if OPEN is resolved in NWP design |
| VccInf non-GV | Fixed baseline `ACTIVE_VID` | Same on NWP | Direct reuse |

---

## Section D: Key Registers & Validation Points

### PythonSv Validation Commands (NWP)

```python
from pm.focus import itd

SockNum = 0

# VccInf ITD info
itd.print_itd_info(SockNum, 0)

# VccInf ITD compensation register
try:
    vccinf_comp = sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.vccinf_itd_comp.read()
    print(f"VccInf ITD compensation: {vccinf_comp}")
except Exception as e:
    print(f"VccInf ITD: {e}")

# SOCKET_THERMAL HPM monitoring (CBB min temp in iMH)
try:
    sock_thermal = sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.socket_thermal.read()
    print(f"SOCKET_THERMAL (CBB min temp): 0x{sock_thermal:08X}")
except Exception as e:
    print(f"SOCKET_THERMAL: {e}")

# VccInf SVID target
try:
    vccinf_vid = sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.vccinf_vid.read()
    print(f"VccInf SVID target: 0x{vccinf_vid:08X}")
except Exception as e:
    print(f"VccInf VID: {e}")
```

---

## Section E: Risk Assessment & Open Items

| # | Risk/Open Item | Severity | Notes |
|---|----------------|----------|-------|
| 1 | **OPEN: Vccinf temperature telemetry path** — DMR test steps mention this is unresolved; NWP must resolve the HPM or dedicated path for CBB→iMH temperature | High | Coordinate with NWP iMH design team before test execution |
| 2 | **`To_be_ported` flag** — script porting required for NWP | Medium | Port test to use `nwp.xml` and verify HPM path |
| 3 | **VccInf ITD fuse names** — `pcode_itd_cutoff_tj` etc. are the same; confirm NWP VccInf-specific slope fuses | Low | Verify from NWP PM MAS |

---

## Section F: Recommendation

**Recommendation: ADAPT — OPEN item resolution required; `To_be_ported` flag**

VccInf ITD architecture is the same on NWP. The temperature telemetry OPEN (CBB→iMH HPM path) must be resolved for NWP before test execution.

Required adaptations:
1. Resolve VccInf temperature telemetry OPEN for NWP (CBB→iMH HPM mechanism)
2. `python runPmx.py -x nwp.xml -p itd_thermal -tM 9 -M 3`
3. Single IMH on NWP simplifies monitoring: only `sv.socket0.imh0.*`

**Priority**: Medium — foundational for VccInf voltage correctness; OPEN item is a prerequisite
