# Deep Analysis: VF Curve Fuses

| Field | Value |
|-------|-------|
| **HSD ID** | 22022422446 |
| **Title** | VF curve fuses |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | Pstate Stack |
| **Sub-Feature** | V/F curve fuses — 12 curves; Pcode table construction and interpolation |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies **V/F (Voltage-Frequency) Curve Fuses** in PCode:
- DMR supports up to **12 fused V/F curves**, each with ~6 frequency/voltage points
- Pcode reads fuses at boot and constructs internal V/F tables
- Each core is mapped to a specific V/F curve via mapping fuses
- Test verifies: Pcode tables match fuse values for all curves and all points
- Test also verifies Pcode interpolates correctly between fused points

On NWP, V/F curves are similarly fused and read by Pcode. The number of curves and points may differ from DMR.

**Key Justification:**
- V/F curve fuse mechanism applicable on NWP
- `DMR_PO` + `plc.feature.p1` + `NGA_MAIN` + `PMSS_NWP_READINESS_CHECK` tags
- Command uses `itd_thermal` check — may need NWP-specific sub-check

---

## Section B: NWP-Specific Test Procedure

### V/F Curve Architecture (DMR)

| Aspect | DMR | NWP |
|--------|-----|-----|
| Max curves | 12 | TBD (verify from NWP HAS) |
| Points per curve | ~6 | TBD |
| Core-to-curve mapping | Per-core fuse | Per-core fuse |
| Curve read | Boot (Pcode) | Boot (Pcode) |

### Adapted Test Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Run ITD/thermal check (covers V/F) | `python runPmx.py -x nwp.xml -p itd_thermal -tM 9 -M 3` |
| 2 | Read Pcode internal V/F tables | PythonSV + Pcode telemetry |
| 3 | Read V/F fuse values from silicon | `sv.socket0.fuses.vf_curve_*` |
| 4 | Compare Pcode tables to fuse values | All 12 (or NWP equivalent) curves |
| 5 | Verify interpolation accuracy | Ratio/voltage at non-fused operating point |

### NWP V/F Fuse Read

```python
# Read V/F curve fuse data (NWP paths)
for curve_idx in range(12):
    try:
        vf_fuse = sv.socket0.imh0.fuses.punit.getbypath(f'vf_curve_{curve_idx}_fused_ratio').read()
        print(f"V/F Curve {curve_idx} fused ratio: {vf_fuse}")
    except Exception as e:
        print(f"V/F Curve {curve_idx}: {e}")
```

### NWP Pass Criteria
- Pcode V/F tables match silicon fuse values for all curves
- Core-to-curve mapping matches mapping fuses
- Pcode interpolation correct at intermediate frequency points
- No V/F table mismatch error in Pcode init logs

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; V/F curve count may differ on NWP**

Required adaptations:
1. `python runPmx.py -x nwp.xml -p itd_thermal -tM 9 -M 3`
2. Verify NWP V/F curve count (may be < 12; read from NWP HAS)
3. Verify NWP fuse namespace for V/F curve data (`sv.socket0.imh0.fuses.*`)

**Priority**: High — `DMR_PO` + `NGA_MAIN` + `plc.feature.p1`; V/F fuse → Pcode table correctness is voltage safety critical
