# Deep Analysis: VF Curve Fuses

| Field | Value |
|-------|-------|
| **HSD ID** | 22022422446 |
| **TCD ID** | [22022421029](https://hsdes.intel.com/appstore/article-one/#/22022421029) |
| **Title** | VF curve fuses |
| **Updated** | 2026-07-17 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | Pstate Stack |
| **Sub-Feature** | V/F curve fuses — 12 fused curves; Pcode VID anchor read + V/F table construction; GV transition safety |
| **NWP Disposition** | **Runnable_On_N-1** |
| **Tags** | `DMR_PO`, `plc.feature.p1`, `NGA_MAIN`, `PMSS_NWP_READINESS_CHECK` |
| **Owner** | akurathi |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies **V/F (Voltage-Frequency) Curve Fuses** in PCode. DMR (and NWP) support up to **12 fused V/F curves** defining the voltage-frequency safety envelope:
- Pcode reads fuse VID anchors (Pn, P1, P0) at boot and builds an interpolated V/F table
- On each GV transition: voltage-first upward (V before F), frequency-first downward (F before V)
- All 12 curves must be readable, non-corrupt, and monotonically non-decreasing in VID

**NWP status (confirmed from KB `pstate_v_f_curve.md`):**
- V/F curve management is **fully supported on NWP** — mechanism unchanged from DMR
- Same fuse-based VID anchor points (Pn, P1, P0)
- Same runtime V/F optimization (ITD voltage offset, Cdyn-based adjustment)
- PantherCove V/F characteristics reused
- SST-PP removed on NWP → no per-SST-PP V/F profile variations to test

**Key Justification:**
- Feature applicable and runnable on NWP pre-silicon/silicon
- Test requires `nwp.xml` substitution for `dmr.xml`; core logic unchanged
- V/F fuse → Pcode table correctness is voltage safety critical — high priority

---

## Section B: NWP Architecture

### V/F Curve Architecture

| Aspect | DMR | NWP |
|--------|-----|-----|
| Max fused VF curves | 12 | 12 (same mechanism) |
| VID anchor points | Pn, P1, P0 per curve | Pn, P1, P0 per curve |
| Interpolation | Linear between anchors | Same algorithm |
| Core-to-curve mapping | Per-core fuse | Per-core fuse |
| Curve read | Boot — PCode early init before CPL3 | Boot — same timing |
| GV transition order | V-first upward, F-first downward | Identical rule |
| Adaptive voltage (DLVR/AVS) | Reduces below nominal V/F curve | Supported (NWP FIVR IP may differ) |
| SST-PP V/F profiles | Yes (per SST level) | **N/A — SST-PP ZBB on NWP** |
| FIVR | CBB-integrated | CBB-integrated |

### Key Registers / Interfaces

| Register | Address | Description |
|----------|---------|-------------|
| VID fuse registers | IMH die fuse bank | Fused VID anchor values at Pn, P1, P0; read by PCode at boot |
| `IA32_PERF_STATUS` | MSR `0x198` | Current operating ratio — corresponds to active V/F operating point |
| `PLATFORM_INFO` | MSR `0x0CE` [15:8] | P1 guaranteed ratio — key V/F anchor |
| FIVR_CONFIG | PCode internal | FIVR voltage regulator control |
| DLVR_CONFIG | PCode internal | Digital LVR adaptive voltage offset |

### NWP Register Paths (PythonSV)

```python
# NWP: IMH is accessed as sv.socket0.nio (not imh0/imh1 as on DMR)
# V/F curve fuse anchors — read per curve:
for curve_idx in range(12):
    try:
        # NWP path: sv.socket0.nio.fuses.punit.<vf_curve_field>
        # Confirm field names via: sv.socket0.nio.fuses.punit.search('vf_curve', 'f')
        vid_pn = sv.socket0.nio.fuses.punit.getbypath(f'vf_curve_{curve_idx}_vid_pn').read()
        vid_p1 = sv.socket0.nio.fuses.punit.getbypath(f'vf_curve_{curve_idx}_vid_p1').read()
        vid_p0 = sv.socket0.nio.fuses.punit.getbypath(f'vf_curve_{curve_idx}_vid_p0').read()
        print(f"Curve {curve_idx}: Pn VID={vid_pn:#x}, P1 VID={vid_p1:#x}, P0 VID={vid_p0:#x}")
    except Exception as e:
        print(f"Curve {curve_idx}: {e}")

# Read PCode internal V/F table via HPM mailbox
# (field names to confirm against NWP PCode source)
perf_status = sv.socket0.nio.punit.ia32_perf_status.read()
print(f"Current ratio: {(perf_status >> 8) & 0xFF}")
```

---

## Section C: Test Procedure (NWP Adapted)

### Current HSD Description Summary (TC 22022422446)

**Validation Scope:** Verify all 12 fused V/F curves are correctly read by pCode at boot and produce correct voltage/frequency operating points at runtime.

**Test Steps:**

| Step | Action | Expected Result (PASS) |
|------|--------|------------------------|
| 1 | Dump all 12 VF curve fuses via PythonSV. Record ratio and VID values per curve point. | All 12 VF curves readable; non-zero VID for all valid ratio points; no corrupt fuse entries. |
| 2 | Read pCode internal VF tables (via debug registers or HPM mailbox) after boot. Compare vs fused values. | pCode internal tables match fused VF curves for all 12 curves and all ratio points. |
| 3 | Force P-state transitions to key ratio points (Pn, P1, P01). Measure applied voltage via SVID readback or telemetry. | Applied voltage at each ratio matches the fused VF curve value (within SVID resolution). GV uses correct curve. |
| 4 | Verify monotonicity: higher frequency → higher-or-equal voltage in each VF curve. | All 12 VF curves monotonically non-decreasing in VID; no voltage inversions. |

**Preconditions:**
- Platform: Diamond Rapids / Newport (Simics with fuse model for pre-silicon)
- All 12 VF curve fuses readable via PythonSV fuse dump tool
- pCode internal VF table readable via debug registers or HPM mailbox
- SVOS, NWP PythonSV, fuse dump tool, Patch23 installed

**Health Check:**
- No MCA or hang during VF curve fuse read or runtime VF transitions
- pCode internal VF tables match all 12 fused curves
- Applied voltage at key ratio points matches fused VID values
- No VID inversions across any of the 12 VF curves

**Pass/Fail Criteria:**
- PASS: all 12 VF curve fuses readable, pCode tables match fused values, runtime voltage matches VF curve, no VID inversions
- FAIL: fuse read failure, pCode table mismatch vs fuse, voltage not matching VF curve at key ratio points, VID inversion, or MCA

---

## Section D: NWP Adaptation Notes

1. **XML substitution**: `dmr.xml` → `nwp.xml`
2. **NIO vs IMH**: NWP has a single NIO (not imh0/imh1); PythonSV path prefix `sv.socket0.nio.punit.*` instead of `sv.socket0.imh0.punit.*`
3. **Fuse namespace**: confirm NWP fuse field names for VF curve VIDs via `sv.socket0.nio.fuses.punit.search('vf', 'f')`
4. **Curve count**: 12 curves expected on NWP (same mechanism as DMR); validate from NWP fuse model
5. **SST-PP V/F profiles**: skip — SST-PP is ZBB on NWP; test covers base V/F curves only
6. **DLVR/FIVR IPs**: NWP FIVR IP may differ from DMR; verify SVID readback path

---

## Section F: Recommendation

**Recommendation: ADOPT with minor adaptations (`dmr.xml` → `nwp.xml`; NIO path substitution)**

Required adaptations:
1. Replace `dmr.xml` with `nwp.xml` in all runPmx / NGA command lines
2. Use `sv.socket0.nio.*` instead of `sv.socket0.imh0.*` for PCode/fuse register access
3. Confirm NWP fuse field names for VF curve VIDs before running
4. Verify SVID readback / voltage telemetry path on NWP FIVR

**Priority:** High — `DMR_PO` + `NGA_MAIN` + `plc.feature.p1`; V/F fuse → PCode table correctness is voltage-safety critical

**References:**
- [KB: pstate_v_f_curve.md](../../../pm_features/pstate_stack/pstate_v_f_curve.md) — NWP delta + architecture + register table
- [CBB PM HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/IP_PM_Features/CBB/DMR_CBB_PM.html) — FIVR/DLVR voltage management, VF fuse format
- [Core P-State HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Core_Pstates/Core_Pstate_HAS.html) — V/F curve in P-state context
- [TCD 22022421029](https://hsdes.intel.com/appstore/article-one/#/22022421029) — Feature Overview (HSD)
- [TC 22022422446](https://hsdes.intel.com/appstore/article-one/#/22022422446) — Test Case (HSD)
