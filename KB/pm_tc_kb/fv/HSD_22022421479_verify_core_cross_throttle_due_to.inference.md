# Deep Analysis: [CBB Thermal Management] Verify Core Cross Throttle Due to Ring

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421479 |
| **Title** | [CBB Thermal Management] Verify Core Cross Throttle Due to Ring |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | SoC Thermal Management > CBB Thermal Management |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies that CBB EMTTM applies core frequency demotion when the Ring domain is overtemperature — a cross-throttle from Ring to Core. Because core and ring traffic are thermally coupled (core traffic drives ring traffic, which generates ring heat), allowing cores to run at full frequency while the ring is thermally limited is architecturally unsound. Pcode implements this by computing: `Core Ratio Floor = Ring EMTTM PID Limit + Core_Ring_Offset`. On NWP, this Ring→Core cross-throttle mechanism is present. The adaptation required is script config (dmr.xml → nwp.xml) and CBB loop count (4→2).

**Key Justification:**
- Ring→Core cross-throttle is implemented in CBB PCode EMTTM on NWP; the Ring is not ZBB (only Ring C6 is)
- The test uses `runPmx.py -p emttm_thermal`; updating `-x dmr.xml` to `-x nwp.xml` is the primary adaptation
- NWP has 2 CBBs × 48 cores; verification scope changes from DMR's 4×32 layout
- DMR_PO tag indicates silicon validation; NWP silicon is required for this test

---

## Section B: NWP-Specific Test Procedure

### Pre-Conditions
- NWP silicon platform with Ring thermal stress workload capability
- `runPmx.py` with `nwp.xml` config
- PythonSv access to CBB TPMI registers for PLR and CCF DTS temperature

### Adapted Test Steps

| Step | Action | NWP Adaptation |
|------|--------|----------------|
| 1 | Run `emttm_test.loopSetup(); emttm_test.mainTest()` | `runPmx.py -x nwp.xml -p emttm_thermal -tM 30 -M 6` |
| 2 | Apply Ring thermal stress (high ring bandwidth workload) until CCF temp > eff_tj_max | Same; both CBBs |
| 3 | Verify Ring self-throttle: Ring ratio reduced by PID to CCF_EMTTM limit | Loop over `range(2)` CBBs |
| 4 | If Ring still hot and at minimum ratio: verify Core cross-throttle triggers | `Core Ratio Floor = Ring_EMTTM_PID_Limit + Core_Ring_Offset`; verify GPSS core limit |
| 5 | Verify `THERMAL_MONITOR_STATUS` = 1 during cross-throttle | Package MSR |
| 6 | Verify TPMI PLR THERMAL bit set on both CBBs | Loop over `range(2)` |
| 7 | Reduce ring load; verify core ratios recover and PLR clears | Same acceptance |

### Key Formula to Verify

```
Core Ratio Floor (enforced by Pcode) = Ring_EMTTM_PID_Limit + Core_Ring_Offset
```
Where `Core_Ring_Offset` is a platform-specific constant (from NWP config). Verify by reading:
- Ring PID output (CCF ratio ceiling in slow-limits)
- Core ratio ceiling enforced by Pcode
- Difference should match `Core_Ring_Offset`

### NWP Pass Criteria
- Core frequency does not exceed Ring PID Limit + Core_Ring_Offset when Ring is thermally limited
- TPMI PLR THERMAL bit set during ring-induced core cross-throttle
- Core frequency recovers when ring temperature drops below eff_tj_max

---

## Section C: NWP Delta Impact Analysis

### Cross-Throttle: Ring → Core

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| Ring EMTTM | CBB PCode PID on CCF/Ring | Same on NWP | No change |
| Ring C6 | Supported | ZBB | **No impact** — Ring C-states ≠ Ring thermal throttle |
| Core_Ring_Offset fuse | DMR-specific value | NWP-specific value | Verify offset in NWP config/fuse |
| CBB count | 4 | 2 | Monitoring: `range(2)` |
| Script XML | `dmr.xml` | `nwp.xml` | Direct substitution |

---

## Section D: Key Registers & Validation Points

### Register Check Table (NWP)

| Category | Register | Field | Expected | Verify On |
|----------|----------|-------|----------|-----------|
| Ring temp | CCF DTS temp | Temperature | > eff_tj_max (trigger condition) | Per CBB |
| Ring limit | CBB slow limits | CCF ratio ceiling | PID output (throttled) | Per CBB |
| Core limit | GPSS core ratio | Core ceiling | ≤ Ring_PID_limit + Core_Ring_Offset | Per CBB |
| PLR | TPMI PLR mailbox | Bit 3 (THERMAL) | 1 during cross-throttle | Per CBB |
| Package status | `IA32_PACKAGE_THERM_STATUS` | `THERMAL_MONITOR_STATUS[0]` | 1 during cross-throttle | Package |

### PythonSv Validation Commands (NWP)

```python
# Monitor Ring→Core cross-throttle on NWP (2 CBBs)
for cbb_idx in range(2):  # NWP has 2 CBBs
    try:
        cbb = sv.socket0.getbypath(f"cbb{cbb_idx}")

        # PLR THERMAL bit
        plr = cbb.getbypath("base.tpmi.plr_mailbox_interface").read()
        thermal = (plr >> 3) & 1
        print(f"CBB{cbb_idx}: PLR THERMAL={thermal}")

        # CCF DTS temperature
        ccf_temp = cbb.getbypath("base.punit.ptpcfsms.dts_temp_ccf").read()
        print(f"CBB{cbb_idx}: CCF temp={ccf_temp}")

    except Exception as e:
        print(f"CBB{cbb_idx}: {e}")

# Package perf limit reasons
ptpcfsms = sv.socket0.imh0.punit.ptpcfsms.ptpcfsms
print(f"Package PLR: 0x{ptpcfsms.perf_limit_reasons.read():08X}")
```

---

## Section E: Risk Assessment & Open Items

| # | Risk/Open Item | Severity | Notes |
|---|----------------|----------|-------|
| 1 | **Silicon required** — Ring→Core cross-throttle requires real ring thermal excursion; VP cannot accurately simulate | Medium | Silicon-only test; plan for NGA silicon station |
| 2 | **`Core_Ring_Offset` value** — verify NWP fuse/config value for `Core_Ring_Offset`; may differ from DMR | Low | Check NWP EMTTM config in `nwp.xml` or PM HAS |
| 3 | **Ring ZBB confusion risk** — testers may confuse Ring C6 (ZBB) with Ring thermal throttle (not ZBB); test description should be explicit | Low | Document clearly in test instructions |

---

## Section F: Recommendation

**Recommendation: ADOPT with adaptation — core mechanism identical on NWP**

Ring→Core cross-throttle is architecturally unchanged on NWP. The ring frequency throttle (EMTTM) is separate from Ring C-state (Ring C6 is ZBB but irrelevant here). Adapt script config and CBB loop count; verify the Core_Ring_Offset fuse/config value for NWP.

Required adaptations:
1. `runPmx.py -x dmr.xml` → `-x nwp.xml`
2. CBB monitoring loop: `range(2)`
3. Verify NWP `Core_Ring_Offset` value from fuse/config
4. Document in test that Ring C6 ZBB ≠ Ring thermal throttle (not ZBB)

**Priority**: High — Ring→Core cross-throttle is a validated PO test; key EMTTM interaction
