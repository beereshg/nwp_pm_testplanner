# Deep Analysis: [ITD] Verify ITD During Reset

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421534 |
| **Title** | [ITD] Verify ITD during reset |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | SoC Thermal Management > ITD |
| **Sub-Feature** | ITD during reset / boot (cross-product: `pm.xproducts.reset`) |
| **NWP Disposition** | **Runnable_On_N-1** |

---


## Test Case Intent

Validates ITD reset-time behavior: before memory training, FW applies worst-case (conservative) ITD using MIN_OVERRIDE_TEMP instead of real DTS. Sets a reset-phase breakpoint, triggers warm reset, at breakpoint reads actual voltage and ratio, calculates expected worst-case offset using MIN_OVERRIDE_TEMP, and verifies actual offset matches expected within 10% tolerance.

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

During reset (while PCode periodic routines are not running), worst-case temperature must be assumed for ITD correction: `MIN_TEMPERATURE` for cold end and `ITD_CUTOFF_TJ` for hot end. At reset Phase 4 (after slow loops begin), PCode should start tracking temperature and compensating voltage per active state MoW. This is a fundamental safety requirement. On NWP, the same ITD-at-reset mechanism applies: reset exit voltage uses worst-case ITD, then transitions to dynamic ITD after Phase 4.

The sub_feature `To_be_ported` indicates this test needs porting from DMR to NWP (script reference `pm.Active_pm.Thermal_Management.CPU_thermals.itd.py` rather than `runPmx.py`). This is explicitly tracked for NWP adaptation.

**Key Justification:**
- ITD during reset is a reset-phase voltage safety requirement; identical on NWP
- `pm.xproducts.reset` tag: cross-product reset domain test
- `To_be_ported` tag: explicitly flagged for NWP porting (but mechanism is the same)
- `PMSS_NWP_READINESS_CHECK` tag: evaluated for NWP

---

## Section B: NWP-Specific Test Procedure

### Pre-Conditions
- NWP silicon with boot script capability (halt before Phase 4)
- PythonSv access to `sv.socket0.imh0.punit.*`
- `pm.Active_pm.Thermal_Management.CPU_thermals.itd` module available for NWP
- Test command: `python runPmx.py -x nwp.xml -p itd_thermal --itd_reset -tM 9 -M 3`

### Adapted Test Steps (from itd_pmx.py --itd_reset option)

| Step | Action | Expected Result (PASS) | Failure Indication |
|------|--------|----------------------|-------------------|
| 1 | Select reference IP (first CCF slice) and record ITD fuse coefficients including MIN_OVERRIDE_TEMP | Fuses readable; MIN_OVERRIDE_TEMP non-zero | Fuse read failure or zero MIN_OVERRIDE_TEMP |
| 2 | Calculate expected worst-case ITD offset using MIN_OVERRIDE_TEMP as temperature input (safe voltage before memory training) | Offset computable and positive (cold scenario) | Zero or negative offset with valid fuses |
| 3 | Set reset-phase breakpoint: write target phase (0x14) to io_reset_stalls[0] and pcode_reset_generic_0 | Both registers accept the breakpoint value | Write failure |
| 4 | Trigger warm reset via CF9h write (0xE) | System enters reset sequence | Reset not triggered or immediate hang |
| 5 | Poll io_pmsb_scratchpad until lower byte matches breakpoint — confirms FW reached target phase | Scratchpad matches within timeout | Timeout — FW did not reach breakpoint phase |
| 6 | At breakpoint: read CCF slice actual voltage and ratio | Voltage and ratio readable at breakpoint | Read failure while halted at breakpoint |
| 7 | Calculate base voltage from VF curve at current ratio | Base voltage within valid range | VF lookup fails |
| 8 | Compute actual ITD offset = actual voltage − base voltage | Actual offset is positive (worst-case compensation applied) | Zero offset — ITD not active during reset |
| 9 | Release breakpoint: clear both stall registers to zero | Registers cleared; system resumes boot | Clear fails — risk of hard hang |
| 10 | Compare actual offset vs expected worst-case offset | Match within 10% tolerance | Deviation > 10% — incorrect reset-time ITD |

### Worst-Case ITD During Reset

During reset, PCode uses fixed conservative temperatures:
- Cold case: `MIN_TEMPERATURE` (from fuse `ITD_MIN_OVERRIDE_TEMP`)
- Hot case: `ITD_CUTOFF_TJ` (fused)

This ensures voltage is safe for both cold and hot silicon scenarios before DTS is calibrated.

### NWP Pass Criteria
- At Phase 3 halt: voltage offset = worst-case ITD (based on `MIN_TEMP` cold, `CUTOFF_TJ` hot)
- After Phase 4: dynamic ITD active; voltage tracks actual DTS temperature
- No voltage undershoot during reset-to-active transition

---

## Section C: NWP Delta Impact Analysis

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| Reset phase structure | PH1-PH5 boot flow | Same on NWP | Same Phase 4 boundary |
| Worst-case ITD formula | `MIN_TEMP` cold, `CUTOFF_TJ` hot | Same fuse names on NWP | Direct reuse |
| Script | `pm.Active_pm.Thermal_Management.CPU_thermals.itd.py` | Needs NWP version | `To_be_ported` — coordinate with PM team |
| Bootscript halt | DMR bootscript syntax | NWP bootscript syntax may differ | Verify with NWP platform bring-up team |

---

## Section D: Key Registers & Validation Points

### PythonSv Validation Commands (NWP)

```python
from pm.focus import itd

SockNum = 0

# Calculate worst-case ITD compensation (reset state)
try:
    itd.calc_worst_case_itd(SockNum, 0)
except AttributeError:
    # Try alternate function name for NWP
    itd.print_itd_info(SockNum, 0)

# During reset halt (Phase 3) — read RC voltage offset
try:
    # VccInf (MBVR) — check SVID target at halt
    vccinf_offset = sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.vccinf_itd_comp.read()
    print(f"VccInf ITD at reset halt: {vccinf_offset}")
except Exception as e:
    print(f"VccInf ITD: {e}")

# CFCIO/CFCMEM RC voltage offsets at reset halt
for domain in ["cfcio", "cfcmem_w", "cfcmem_e"]:
    try:
        offset = sv.socket0.imh0.punit.getbypath(f"resctrl_cr_{domain}_v_offset").read()
        print(f"{domain} V_OFFSET at reset: {offset}")
    except Exception as e:
        print(f"{domain}: {e}")
```

---

## Section E: Risk Assessment & Open Items

| # | Risk/Open Item | Severity | Notes |
|---|----------------|----------|-------|
| 1 | **`To_be_ported` flag** — `pm.Active_pm.Thermal_Management.CPU_thermals.itd.py` needs NWP porting; coordinate with PM team before execution | High | This is the primary blocker; get NWP version of the script |
| 2 | **NWP bootscript halt capability** — NWP platform bootscript must support halt-before-Phase4; verify with NWP bring-up team | Medium | Critical for test methodology; may need alternative approach |
| 3 | **Phase boundary timing** — NWP reset phase boundaries may slightly differ from DMR | Low | Verify from NWP PCode trace/log |

---

## Section F: Recommendation

**Recommendation: ADAPT — `To_be_ported` flag requires script porting first**

The ITD-at-reset mechanism is architecturally identical on NWP, but the test script (`pm.Active_pm.Thermal_Management.CPU_thermals.itd.py`) needs NWP adaptation. This is explicitly tracked.

Required adaptations:
1. Port `pm.Active_pm.Thermal_Management.CPU_thermals.itd.py` for NWP (coordinate with PM team)
2. Verify NWP bootscript supports halt-before-Phase4
3. `dmr.xml` → `nwp.xml` (for related `runPmx.py` calls)

**Priority**: Medium — fundamental ITD safety test; needs porting work before execution; `pm.xproducts.reset` cross-domain relevance
