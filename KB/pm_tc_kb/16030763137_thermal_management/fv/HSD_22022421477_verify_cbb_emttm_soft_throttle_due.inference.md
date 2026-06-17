# Deep Analysis: [CBB Thermal Management] Verify CBB EMTTM Soft Throttle due to Self Throttle

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421477 |
| **Title** | [CBB Thermal Management] Verify CBB EMTTM Soft Throttle due to Self Throttle |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | SoC Thermal Management > CBB Thermal Management |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies the CBB EMTTM "self-throttle" path: when a hot domain (e.g. CCF/Ring) exceeds its temperature target, the EMTTM PID reduces that domain's own frequency ceiling without cross-throttling other domains. This is distinct from cross-throttle — the hot domain throttles itself. On NWP, CBB EMTTM self-throttle is implemented and is the primary thermal frequency control path for the Ring domain. The test requires adapting script config (dmr.xml → nwp.xml) and CBB monitoring scope (4→2 CBBs). The `DMR_PO` + `NGA_MAIN` tags indicate this is a priority validation test.

**Key Justification:**
- CBB EMTTM self-throttle (hot domain reduces its own frequency via PID) is present on NWP
- Ring/CCF domain self-throttle via CBB PCode PID is the primary thermal mechanism for CCF on NWP
- Ring C6 is ZBB on NWP, but Ring **frequency throttling** (EMTTM) is not C-state related and is supported
- `NGA_MAIN` tag: this TC should be prioritized for NWP NGA automation

---

## Section B: NWP-Specific Test Procedure

### Pre-Conditions
- NWP silicon platform with CCF/Ring thermal stress capability
- `runPmx.py` with `nwp.xml` config
- PythonSv access to CBB TPMI and EMTTM registers

### Adapted Test Steps

| Step | Action | NWP Adaptation |
|------|--------|----------------|
| 1 | Load and configure EMTTM test | `nwp.xml` config; 2 CBBs |
| 2 | Run `emttm_test.loopSetup(); emttm_test.mainTest()` | `runPmx.py -x nwp.xml -p emttm_thermal -tM 30 -M 6` |
| 3 | Apply Ring/CCF thermal stress to push CCF temp above eff_tj_max | Same mechanism; verify on both CBBs |
| 4 | Verify CBB EMTTM PID reduces CCF ratio ceiling (self-throttle) | Loop over `range(2)` CBBs (DMR: 4); check CCF ratio limit in slow-limits PMA_CR |
| 5 | Verify `IA32_PACKAGE_THERM_STATUS.THERMAL_MONITOR_STATUS` = 1 | Same package MSR |
| 6 | Verify TPMI PLR `THERMAL` bit set | `range(2)` CBBs |
| 7 | Reduce thermal load; verify CCF ratio recovers and PLR clears | Same acceptance criterion |

### NWP Pass Criteria
- CBB EMTTM PID lowers CCF/Ring frequency ceiling on the hot CBB when `CCF_temp > eff_tj_max`
- `THERMAL_MONITOR_STATUS` = 1 during self-throttle event
- PLR THERMAL bit set; cleared after recovery
- Core frequency unchanged during Ring self-throttle (no cross-throttle triggered unless Ring at minimum)

---

## Section C: NWP Delta Impact Analysis

### EMTTM Self-Throttle Path

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| CCF/Ring self-throttle | PCode PID via `CCF_EMTTM_PID` | Same on NWP | No change |
| CBB count | 4 | 2 | Monitoring: `range(2)` |
| Ring C6 | Supported | ZBB | No impact on EMTTM frequency throttle (C-state vs. freq limit) |
| SST-PP eff_tj_max | Active | ZBB | eff_tj_max uses base fuse TjMax - TCC_offset |
| Script XML | `dmr.xml` | `nwp.xml` | Direct substitution |

---

## Section D: Key Registers & Validation Points

### Register Check Table (NWP)

| Category | Register | Field | Expected | Verify On |
|----------|----------|-------|----------|-----------|
| Ring temp | `PCU_CR_DTS_TEMP_CCF` | Temperature | > eff_tj_max (throttle trigger) | Per CBB |
| EMTTM limit | CBB slow limits | CCF ratio ceiling | Below P1 (throttled by PID) | Per CBB |
| Package status | `IA32_PACKAGE_THERM_STATUS` | `THERMAL_MONITOR_STATUS[0]` | 1 during throttle | Package |
| PLR | TPMI PLR mailbox | Bit 3 (THERMAL) | 1 during throttle | Per CBB |

### PythonSv Validation Commands (NWP)

```python
# Monitor CBB EMTTM self-throttle on NWP (2 CBBs)
for cbb_idx in range(2):  # NWP has 2 CBBs
    cbb = sv.socket0.getbypath(f"cbb{cbb_idx}")
    try:
        # TPMI PLR thermal bit
        plr = cbb.getbypath("base.tpmi.plr_mailbox_interface").read()
        thermal = (plr >> 3) & 1
        print(f"CBB{cbb_idx}: PLR THERMAL={thermal}")

        # Ring/CCF temperature (DTS)
        ring_temp = cbb.getbypath("base.punit.ptpcfsms.dts_temp_ccf").read()
        print(f"CBB{cbb_idx}: Ring/CCF temp={ring_temp}")
    except Exception as e:
        print(f"CBB{cbb_idx}: {e}")

# Package thermal monitor
ptpcfsms = sv.socket0.imh0.punit.ptpcfsms.ptpcfsms
print(f"Package PLR: 0x{ptpcfsms.perf_limit_reasons.read():08X}")
```

---

## Section E: Risk Assessment & Open Items

| # | Risk/Open Item | Severity | Notes |
|---|----------------|----------|-------|
| 1 | **Silicon required** — Ring thermal self-throttle needs real thermal excursion; VP simulation may not be accurate | Medium | NGA_MAIN tag → prioritize for silicon NGA |
| 2 | **eff_tj_max without SST-PP** — test may need to account for simplified eff_tj_max formula (no SST-PP on NWP) when computing expected throttle trigger point | Low | Update test expected temperature computation |

---

## Section F: Recommendation

**Recommendation: ADOPT with minor adaptation — high-priority NGA target**

Ring/CCF EMTTM self-throttle is the primary thermal mechanism for NWP CBB and should be prioritized for NGA automation (`NGA_MAIN` tag). The adaptation is minimal: XML config + CBB loop count.

Required adaptations:
1. `runPmx.py -x dmr.xml` → `-x nwp.xml`
2. CBB monitoring loop: `range(2)`
3. Update eff_tj_max formula in test: remove SST-PP branch

**Priority**: Critical — NGA_MAIN; fundamental EMTTM self-throttle path validation
