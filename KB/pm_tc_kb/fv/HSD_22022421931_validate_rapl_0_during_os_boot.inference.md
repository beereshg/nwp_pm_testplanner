# Deep Analysis: [BEAT][FV PM][AR] Validate RAPL=0 during OS Boot

| Field | Value |
|-------|-------|
| **HSD ID** | [22022421931](https://hsdes.intel.com/appstore/article-one/#/22022421931) |
| **Title** | [BEAT][FV PM][AR] Validate RAPL=0 during OS Boot |
| **Date** | 2026-07-18 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Socket RAPL |
| **Sub-Feature** | PL1=0 boundary validation (PrimeCode clips to MIN_PL) |
| **NWP Disposition** | **Runnable_On_N-1** |
| **Owner** | mps |
| **Status** | open |
| **Val Environment** | silicon |
| **Tags** | PMSS_NWP_READINESS_CHECK |
| **Parent TCD** | [22022420821 -- Socket RAPL Registers Verification - CSR and TPMI](https://hsdes.intel.com/appstore/article-one/#/22022420821) |

---

## Test Case Intent

Verify that when Socket RAPL PL1 is programmed to 0 watts via TPMI PL1_CONTROL, PrimeCode firmware clips the effective power limit to MIN_PL (minimum programmable power limit from SKU fuse), the RAPL NN-PID output is clamped to minimum frequency (Pm), and package power converges to approximately MIN_PL watts. This validates the PL1=0 boundary clipping behavior per the Socket RAPL HAS.

**Differentiation from related TCs:**
- TC 22022422034 (PL1/PL2 Limits and Tau) validates normal PL1/PL2 encoding and readback -- this TC validates the **boundary case PL1=0**
- TC 22022421976 (Sweep CPU RAPL Limits) sweeps PL1 across a range -- this TC specifically targets the **zero boundary**

---

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| Platform | NWP post-silicon system (OakStream) |
| BIOS | Default Socket RAPL; PL1 LOCK bit must be clear (unlocked) to allow runtime PL1 override |
| OS | SVOS or Ubuntu booted to idle |
| Tool | PythonSV with namednodes access to NIO TPMI registers |
| Baseline | Record default PL1 (= TDP) and MIN_PL from PL_INFO before starting |
| Workload | PTU or stress-ng running TDP-level load on all 96 cores |

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|---------------------|
| 1 | Read PL_INFO to get MIN_PL and MAX_PL1: `pl_info = sv.socket0.nio.punit.tpmi.socket_rapl.pl_info.read()` | MIN_PL field is non-zero; MAX_PL1 = TDP | MIN_PL = 0 (fuse not programmed) |
| 2 | Record baseline PL1: `baseline = sv.socket0.nio.punit.tpmi.socket_rapl.pl1_control.read()` | PL1 = TDP (default) | PL1 already modified |
| 3 | Start TDP workload: `./ptu -ct 3` across all cores | CPU at full load; power near TDP | Workload fails to start |
| 4 | Program PL1=0: `sv.socket0.nio.punit.tpmi.socket_rapl.pl1_control.write(0x0)` (PWR_LIM=0, enable=1) | Write accepted (no error) | Write rejected or system crash |
| 5 | Read back PL1_CONTROL: `effective = sv.socket0.nio.punit.tpmi.socket_rapl.pl1_control.read()` | Effective PWR_LIM readback shows MIN_PL (PrimeCode clipped 0 to MIN_PL) | Readback shows 0 (no clipping) or unexpected value |
| 6 | Wait 5x PL1 tau (~5s) for PID convergence; read PERF_STATUS throttle counter | PERF_STATUS throttle counter incrementing (system is RAPL-throttled) | No throttling observed |
| 7 | Measure package power: read ENERGY_STATUS twice 2s apart and compute power | pkg_power approximately MIN_PL watts (within +/-20%) | Power at TDP (no throttling) or zero |
| 8 | Restore PL1 to baseline: `sv.socket0.nio.punit.tpmi.socket_rapl.pl1_control.write(baseline)` | PL1 restored; power returns to TDP level | Power does not recover |

### Pass / Fail Criteria

**Bar:** Per RAPL HAS -- PL1=0 is clipped to MIN_PL by PrimeCode. System throttles to minimum frequency (Pm). pkg_power converges to approximately MIN_PL.

**PASS**: PL1_CONTROL readback shows MIN_PL after writing 0 AND PERF_STATUS throttle counter incrementing AND pkg_power within MIN_PL +/-20% AND power recovers after PL1 restore
**FAIL**: PL1 readback shows 0 (no clipping) OR no throttling OR system hang/MCA OR power does not converge to MIN_PL

---

## Section A: NWP Delta

**Disposition: Runnable_On_N-1**

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| Register path | `sv.socket0.imh0.punit.tpmi.socket_rapl.*` | `sv.socket0.nio.punit.tpmi.socket_rapl.*` | Path prefix swap only |
| MIN_PL source | SKU fuse via PL_INFO | Same SKU fuse via PL_INFO | Identical mechanism |
| Clipping logic | PrimeCode clips PL1 < MIN_PL to MIN_PL | Same PrimeCode logic on NIO | No change |
| PID behavior | NN-PID output clamped to Pm | Same NN-PID on NIO | Single instance vs dual |

**Adaptation required:** Register path prefix swap (`imh0` to `nio`). No script logic changes.

---

## Section B: Interactions

### Swimlane Data
| Step | Actor | Action | Interface |
|------|-------|--------|-----------|
| 1 | OS/Test | Read PL_INFO for MIN_PL and MAX_PL1 | [TPMI MMIO] |
| 2 | OS/Test | Write PL1_CONTROL.PWR_LIM = 0 | [TPMI MMIO] |
| 3 | PrimeCode (NIO) | Detect PL1 < MIN_PL; clip to MIN_PL; update effective PL1 | [Internal] |
| 4 | PrimeCode (NIO) | NN-PID computes output; clamps to Pm; asserts fast_throttle | [Internal] |
| 5 | PrimeCode (NIO) | Distribute RAPL_PERF_LIMIT to CBBs via HPM 0x14 | [HPM] |
| 6 | PCode (CBBx2) | Enforce Pm frequency ceiling; increment PERF_STATUS | [HPM] |
| 7 | OS/Test | Read PERF_STATUS and measure power | [TPMI MMIO] |

### Sequence Data
| # | From | To | Message | Interface |
|---|------|----|---------|-----------|
| 1 | OS/Test | PrimeCode (NIO) | TPMI write PL1_CONTROL.PWR_LIM=0 | [TPMI MMIO] |
| 2 | PrimeCode (NIO) | PrimeCode (NIO) | Clip PL1 to MIN_PL; feed NN-PID | [Internal] |
| 3 | PrimeCode (NIO) | PCode (CBBx2) | HPM RAPL_PERF_LIMIT = Pm | [HPM] |
| 4 | PCode (CBBx2) | Cores | Enforce frequency ceiling = Pm | [HW wire] |
| 5 | PCode (CBBx2) | PrimeCode (NIO) | HPM LEAF_PERF_STATUS (throttled) | [HPM] |
| 6 | OS/Test | PrimeCode (NIO) | TPMI read PERF_STATUS | [TPMI MMIO] |

---

## Section C: Coverage

| Scenario | Covered by this TC | Covered elsewhere |
|----------|-------------------|-------------------|
| PL1=0 clipped to MIN_PL | Yes | -- |
| PERF_STATUS increments under PL1=0 throttle | Yes | TC 22022422038 (general PERF_STATUS) |
| Power converges to MIN_PL | Yes | -- |
| PL1 restore to baseline | Yes | -- |
| PL2=0 boundary | No | TC TBD (boundary case for PL2) |
| PL1 = MIN_PL (exact boundary) | No | TC 22022421976 (sweep) |
| PL1 below MIN_PL but non-zero | No | TC 22022421976 (sweep) |
| PL1=0 with LOCK bit set | No | TC 22022422034 (LOCK behavior) |

---

## Section D: Spec Refs

- [Socket RAPL KB -- socket_rapl.md](../../pm_features/power_rapl/socket_rapl.md) -- PL1 clipping, MIN_PL, PID behavior
- [TCD 22022420821 -- Socket RAPL Registers CSR/TPMI](https://hsdes.intel.com/appstore/article-one/#/22022420821) -- register interface validation
- [Intel RAPL HAS -- Clipping of Power Limits](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/RAPL/RAPL.html) -- PL1 clipping to MIN_PL
- [PrimeCode Socket RAPL -- Frequency Clipping below TDP](https://docs.primecode.intel.com/master/rapl.html) -- NN-PID output clamped to Pm

---

## Section E: Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| System hang when PL1=0 before clipping takes effect | Low | High | PrimeCode clips synchronously on TPMI write; no transient 0W window |
| MIN_PL fuse not programmed (reads 0) | Low | Test blocked | Step 1 checks MIN_PL before proceeding |
| Power measurement tolerance too tight | Medium | False fail | Use +/-20% tolerance for MIN_PL convergence |
| PL1 LOCK bit set by BIOS | Medium | Test blocked | Pre-condition: verify LOCK=0 before write |

---

## Section F: Recommendations

1. **Runnable as-is on NWP** with path prefix swap (`imh0` to `nio`). No script logic changes needed.
2. **Add PL2=0 boundary variant** as a separate TC under the same TCD.
3. **Consider adding to kayak automation** -- this is a write-read-measure-restore pattern suitable for `runPmx.py`.
4. **Note for TC title clarity:** "RAPL=0" means PL1=0W; the title could be clarified to "Validate PL1=0 Boundary Clipping" to avoid confusion with counter initialization.
