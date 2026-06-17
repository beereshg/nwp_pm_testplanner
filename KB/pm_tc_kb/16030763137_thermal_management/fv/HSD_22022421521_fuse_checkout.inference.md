# Deep Analysis: [ITD] Fuse Checkout

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421521 |
| **Title** | [ITD] Fuse checkout |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | SoC Thermal Management > ITD (Integrated Temperature Diode / Thermal Determination) |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test is a basic bring-up validation that ITD (Integrated Temperature/Thermal Decision) fuses are programmed to non-zero values. ITD is supported on NWP. The fuse register paths are in `imh0.fuses.punit` and the register names are the same. The primary adaptation is updating the `runPmx.py` command from `dmr.xml` to `nwp.xml`, and noting that TC is in WIP state (2 IPs still need functional validation beyond this fuse checkout). The NWP adaptation is minimal — it is a direct bring-up prerequisite.

**Key Justification:**
- ITD is supported on NWP; fuses are expected to be programmed on production parts
- Fuse paths `imh0.fuses.punit.pcode_itd_*` are in the same PTPCFSMS/fuses register space on NWP
- `dmr.xml` → `nwp.xml` is the only script-level adaptation needed
- `PMSS_NWP_READINESS_CHECK` tag: explicit NWP readiness classification
- WIP note in test steps means this is an evolving test; NWP team should track completion

---

## Section B: NWP-Specific Test Procedure

### Pre-Conditions
- NWP silicon platform (ITD fuses are programmed by manufacturing)
- PythonSv access to `sv.socket0.imh0.fuses.punit.*`

### Adapted Test Steps

| Step | Action | NWP Adaptation |
|------|--------|----------------|
| 1 | Run ITD thermal test module with NWP config | `python runPmx.py -x nwp.xml -p itd_thermal -tM 9 -M 3` |
| 2 | Read `pcode_itd_cutoff_tj` fuse — verify non-zero | `sv.socket0.imh0.fuses.punit.pcode_itd_cutoff_tj.read()` |
| 3 | Read `pcode_itd_min_override_temp` fuse — verify non-zero | `sv.socket0.imh0.fuses.punit.pcode_itd_min_override_temp.read()` |
| 4 | Read `pcode_cfc_itd_slope` fuse — verify non-zero | `sv.socket0.imh0.fuses.punit.pcode_cfc_itd_slope.read()` |
| 5 | Read `pcode_cfc_itd_slope_2` fuse — verify non-zero | `sv.socket0.imh0.fuses.punit.pcode_cfc_itd_slope_2.read()` |
| 6 | Read `pcode_cfc_itd_cutoff_v` fuse — verify non-zero | `sv.socket0.imh0.fuses.punit.pcode_cfc_itd_cutoff_v.read()` |
| 7 | (WIP) Additional fuses TBD — track with TC owner (22022421521 marked WIP) | Monitor TC status; add to NWP fuse checkout script as test evolves |

### NWP Pass Criteria
- All five ITD fuses read non-zero values
- `itd.pre_test(SockNum)` (from `pm.focus import itd`) completes without errors
- WIP note: 2 additional IPs remain for functional ITD validation (tracked separately)

---

## Section C: NWP Delta Impact Analysis

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| XML config file | `dmr.xml` | `nwp.xml` | **Critical** — must update `runPmx.py` command |
| ITD fuse register path | `imh0.fuses.punit.pcode_itd_*` | Same on NWP | Direct reuse |
| ITD CFC slope fuses | Present on DMR | Present on NWP | Same fuse names |
| WIP status | 2 IPs pending functional validation | Same WIP tracked for NWP | Check with TC owner for NWP closure |

---

## Section D: Key Registers & Validation Points

### PythonSv Fuse Read Commands (NWP)

```python
# ITD fuse checkout — NWP single IMH
fuses = sv.socket0.imh0.fuses.punit

itd_fuses = [
    "pcode_itd_cutoff_tj",
    "pcode_itd_min_override_temp",
    "pcode_cfc_itd_slope",
    "pcode_cfc_itd_slope_2",
    "pcode_cfc_itd_cutoff_v",
]

print("=== ITD Fuse Checkout (NWP imh0) ===")
all_pass = True
for fuse_name in itd_fuses:
    try:
        fuse_obj = getattr(fuses, fuse_name)
        val = fuse_obj.read()
        status = "PASS" if val != 0 else "FAIL (zero)"
        if val == 0:
            all_pass = False
        print(f"  {fuse_name}: 0x{val:08X} [{status}]")
    except Exception as e:
        print(f"  {fuse_name}: ERROR — {e}")
        all_pass = False

print(f"\nOverall: {'PASS' if all_pass else 'FAIL'}")
```

### runPmx.py Command (NWP)

```bash
# Run ITD thermal test module (NWP config)
python runPmx.py -x nwp.xml -p itd_thermal -tM 9 -M 3
```

### ITD pre-test (from pm.focus)

```python
from pm.focus import itd
SockNum = 0
itd.pre_test(SockNum)
```

---

## Section E: Risk Assessment & Open Items

| # | Risk/Open Item | Severity | Notes |
|---|----------------|----------|-------|
| 1 | **TC is WIP** — additional fuses and 2 IPs still pending functional validation on DMR; same gap exists for NWP | Medium | Track TC owner (22022421521) for updates; add fuses to NWP fuse checkout script when TC is finalized |
| 2 | **ITD fuse names on NWP** — fuse names assumed same as DMR from known PTPCFSMS architecture; validate during NWP bring-up | Low | Verify with NWP EV team |
| 3 | **`pm.focus.itd` NWP support** — `itd.pre_test(SockNum)` function must support NWP (may auto-detect via SV topology) | Low | Verify import path on NWP test system |

---

## Section F: Recommendation

**Recommendation: ADOPT with single command adaptation; track WIP completion**

This is a direct port from DMR to NWP. Only `dmr.xml` → `nwp.xml` is needed. Fuse register paths are identical. The WIP state of the TC means the test will expand over time — NWP team should track TC owner updates.

Required adaptations:
1. Change `runPmx.py -x dmr.xml` → `python runPmx.py -x nwp.xml`
2. Monitor TC 22022421521 for WIP completion (additional fuses and 2 remaining IPs)
3. Verify `pm.focus import itd` works in NWP PythonSv environment

**Priority**: High — PMSS_NWP_READINESS_CHECK; ITD fuse checkout is a bring-up prerequisite for all subsequent ITD functional tests
