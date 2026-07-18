# Deep Analysis: Socket RAPL PL1 Toggle (0W ↔ TDP) Under Load

| Field | Value |
|-------|-------|
| **HSD ID** | [16031169546](https://hsdes.intel.com/appstore/article-one/#/16031169546) |
| **Title** | [FV PM] Socket RAPL PL1 Toggle 0W to TDP Under Load |
| **Date** | 2026-07-18 |
| **Target Program** | NWP (Newport) |
| **Source Program** | NWP-native (new TC) |
| **Feature** | Socket RAPL |
| **Sub-Feature** | PL1 runtime toggle — clipping, throttle engagement, recovery |
| **NWP Disposition** | **NWP-Native** |
| **Owner** | bg3 |
| **Status** | draft |
| **Val Environment** | silicon |
| **Tags** | PMSS_NWP_READINESS_CHECK |
| **Parent TCD** | [22022420821 -- Socket RAPL Registers Verification - CSR and TPMI](https://hsdes.intel.com/appstore/article-one/#/22022420821) |

---

## Test Case Intent

Validate that Socket RAPL PL1 can be safely toggled between 0W (clipped to MIN_PL) and TDP at runtime under sustained workload across multiple cycles. Each cycle verifies: (1) PL1=0 write is clipped to MIN_PL per spec, (2) PERF_STATUS throttle counter increments during throttling, (3) package power converges to approximately MIN_PL, (4) PL1=TDP restore causes power recovery to TDP level, and (5) PERF_STATUS stops incrementing after recovery. All 10 cycles must complete without MCA, hang, or frequency drift.

**Differentiation from related TCs:**
- TC 22022421931 (RAPL=0 at boot) validates the one-shot PL1=0 boundary — this TC validates **cyclic toggle robustness**
- TC 22022422034 (PL1/PL2 Limits and Tau) validates static register encoding — this TC validates **dynamic runtime transitions**

**Co-Design spec grounding (HAS):**
- PrimeCode clips PL1 to MIN_PL from PL_INFO when 0W is programmed (RAPL HAS, HSD 14024988302)
- PL1 is always enabled on TPMI; EN bit is ignored by PrimeCode
- EWMA PID controller settles in 3–5× tau; default tau=1s → settling ≈ 5s
- PERF_STATUS PWR_LIMIT_THROTTLE_CTR increments during PL1 throttling

---

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| Platform | NWP post-silicon system (OakStream) |
| BIOS | Default Socket RAPL configuration; PL1 LOCK bit must be **clear** (unlocked) |
| OS | SVOS or Ubuntu booted to idle |
| Tool | PythonSV with namednodes access to NIO TPMI registers |
| Baseline | Record default PL1 (= TDP) and MIN_PL from PL_INFO before starting |
| Workload | PTU or stress-ng running TDP-level load on all 96 cores |
| MCA monitor | `mcelog` or equivalent running to catch machine check exceptions |

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|---------------------|
| 1 | Read PL_INFO: `pl_info = sv.socket0.nio.punit.tpmi.socket_rapl.pl_info.read()` | MIN_PL field is non-zero; MAX_PL1 = TDP | MIN_PL = 0 (fuse not programmed) |
| 2 | Read baseline PL1: `baseline_pl1 = sv.socket0.nio.punit.tpmi.socket_rapl.pl1_control.read()` | PL1 = TDP (default) | PL1 already modified or locked |
| 3 | Read tau from PL1_CONTROL TIME_WINDOW field; compute settle_time = 5 × tau | tau is within [1s, 5s]; settle_time = 5–25s | tau = 0 or out of range |
| 4 | Record initial PERF_STATUS: `ps0 = sv.socket0.nio.punit.tpmi.socket_rapl.perf_status.read()` | Throttle counter value captured | Read error |
| 5 | Start TDP workload: `stress-ng --cpu 96 --cpu-method matrixprod` or PTU across all cores | CPU at full load; power ≈ TDP | Workload fails to start |
| 6 | **BEGIN CYCLE (repeat steps 6–13 for N=10 cycles)** | — | — |
| 7 | Write PL1=0: `sv.socket0.nio.punit.tpmi.socket_rapl.pl1_control.write(0x0)` | Write accepted (no error/crash) | System hang or MCA |
| 8 | Read back PL1_CONTROL: `effective = sv.socket0.nio.punit.tpmi.socket_rapl.pl1_control.pl1_power.read()` | Readback = MIN_PL (PrimeCode clipped 0 → MIN_PL) | Readback = 0 (no clipping) |
| 9 | Wait settle_time (5× tau); read PERF_STATUS: `ps1 = sv.socket0.nio.punit.tpmi.socket_rapl.perf_status.read()` | ps1 > ps0 (throttle counter incrementing) | ps1 == ps0 (no throttling) |
| 10 | Read ENERGY_STATUS twice, 2s apart; compute power = delta_energy / delta_time | pkg_power ≈ MIN_PL (within ±20%) | Power still at TDP |
| 11 | Write PL1=TDP: `sv.socket0.nio.punit.tpmi.socket_rapl.pl1_control.write(baseline_pl1)` | Write accepted; readback = TDP | Write rejected or readback mismatch |
| 12 | Wait settle_time (5× tau); record PERF_STATUS: `ps2 = sv.socket0.nio.punit.tpmi.socket_rapl.perf_status.read()` | PERF_STATUS stops incrementing (ps2 ≈ ps_after_recover, no new increments after recovery) | Counter still incrementing at TDP |
| 13 | Read ENERGY_STATUS twice, 2s apart; compute power | pkg_power ≈ TDP (within ±10%) | Power stuck at MIN_PL |
| 14 | **END CYCLE** — update ps0 = ps2; repeat from step 7 | Cycle N completes successfully | Any cycle fails |
| 15 | Stop workload; verify no MCA via `mcelog --client` or dmesg | No MCA, no IERR, no system errors | MCA or system error detected |

### Pass / Fail Criteria

**Bar:** Per [TCD 22022420821](https://hsdes.intel.com/appstore/article-one/#/22022420821) §5 sub-interface B (PL Control Encoding) and RAPL HAS — PL1=0 is clipped to MIN_PL; PL1=TDP readback matches programmed value.

**PASS** when ALL of the following hold across all 10 cycles:
- PL1_CONTROL readback = MIN_PL after writing 0 (clipping works every cycle)
- PL1_CONTROL readback = TDP after restoring baseline (recovery works every cycle)
- PERF_STATUS throttle counter increments during MIN_PL enforcement
- PERF_STATUS stops incrementing after PL1 restored to TDP
- Package power converges to MIN_PL ±20% during throttle phase
- Package power recovers to TDP ±10% during recovery phase
- No MCA, IERR, hang, or unrecoverable frequency drift across all cycles

**FAIL** when ANY of the following occur:
- PL1 readback = 0 on any cycle (no clipping)
- Power does not converge to MIN_PL during throttle phase
- Power does not recover to TDP during recovery phase
- PERF_STATUS does not increment during throttle phase
- MCA, IERR, or system hang on any cycle
- Frequency drifts beyond ±100 MHz of expected after final recovery

---

## Section A: NWP Delta

**Disposition: NWP-Native**

This is a new TC authored for NWP. No DMR predecessor exists.

| Aspect | NWP Detail |
|--------|------------|
| Register path | `sv.socket0.nio.punit.tpmi.socket_rapl.*` |
| MIN_PL source | SKU fuse via PL_INFO on NIO |
| Clipping logic | PrimeCode on NIO clips PL1 < MIN_PL to MIN_PL |
| PID settling | NN-PID on NIO; 3–5× tau for EWMA convergence |
| Topology | Single NIO (1 PrimeCode instance), 2 CBBs |
| PERF_STATUS | Throttle counter on NIO TPMI; incrementing during PL1 throttle |

---

## Section B: Interactions

### Swimlane Data
| Step | Actor | Action | Interface |
|------|-------|--------|-----------|
| 1 | OS/Test | Read PL_INFO (MIN_PL, TDP) | [TPMI MMIO] |
| 2 | OS/Test | Read baseline PL1_CONTROL | [TPMI MMIO] |
| 3 | OS/Test | Start TDP workload | [OS] |
| 4 | OS/Test | Write PL1=0 via PL1_CONTROL | [TPMI MMIO] |
| 5 | PrimeCode (NIO) | Clip PL1=0 to MIN_PL | [Internal] |
| 6 | PrimeCode (NIO) | NN-PID computes min freq from MIN_PL | [Internal] |
| 7 | PrimeCode (NIO) | Distribute RAPL_PERF_LIMIT to CBBs | [HPM] |
| 8 | PCode (CBB×2) | Enforce frequency ceiling; increment PERF_STATUS | [HPM] |
| 9 | OS/Test | Verify PERF_STATUS incrementing; power ≈ MIN_PL | [TPMI MMIO] |
| 10 | OS/Test | Write PL1=TDP via PL1_CONTROL | [TPMI MMIO] |
| 11 | PrimeCode (NIO) | NN-PID computes freq from TDP (no throttle) | [Internal] |
| 12 | PrimeCode (NIO) | Distribute new RAPL_PERF_LIMIT to CBBs | [HPM] |
| 13 | PCode (CBB×2) | Release frequency ceiling; PERF_STATUS stops incrementing | [HPM] |
| 14 | OS/Test | Verify power recovers to TDP; PERF_STATUS stable | [TPMI MMIO] |

### Sequence Data
| # | From | To | Message | Interface |
|---|------|----|---------|-----------|
| 1 | OS/Test | NIO TPMI | Read PL_INFO, PL1_CONTROL baseline | [TPMI MMIO] |
| 2 | OS/Test | NIO TPMI | Write PL1_CONTROL.PWR_LIM = 0 | [TPMI MMIO] |
| 3 | PrimeCode | PrimeCode | Clip PL1 to MIN_PL; recalculate NN-PID | [Internal] |
| 4 | PrimeCode | PCode (CBB0) | HPM RAPL_PERF_LIMIT (min freq) | [HPM 0x14] |
| 5 | PrimeCode | PCode (CBB1) | HPM RAPL_PERF_LIMIT (min freq) | [HPM 0x14] |
| 6 | PCode (CBB0) | PrimeCode | HPM LEAF_PERF_STATUS | [HPM 0x16] |
| 7 | PCode (CBB1) | PrimeCode | HPM LEAF_PERF_STATUS | [HPM 0x16] |
| 8 | OS/Test | NIO TPMI | Read PERF_STATUS (incrementing) | [TPMI MMIO] |
| 9 | OS/Test | NIO TPMI | Read ENERGY_STATUS (power ≈ MIN_PL) | [TPMI MMIO] |
| 10 | OS/Test | NIO TPMI | Write PL1_CONTROL.PWR_LIM = TDP | [TPMI MMIO] |
| 11 | PrimeCode | PrimeCode | Recalculate NN-PID (no throttle) | [Internal] |
| 12 | PrimeCode | PCode (CBB0) | HPM RAPL_PERF_LIMIT (unrestricted) | [HPM 0x14] |
| 13 | PrimeCode | PCode (CBB1) | HPM RAPL_PERF_LIMIT (unrestricted) | [HPM 0x14] |
| 14 | OS/Test | NIO TPMI | Read PERF_STATUS (stable), ENERGY_STATUS (power ≈ TDP) | [TPMI MMIO] |

---

## Section C: Coverage

| Coverage Dimension | What This TC Covers |
|-------------------|---------------------|
| Register encoding | PL1_CONTROL PWR_LIM field: boundary values 0 and TDP |
| Clipping | PrimeCode clips PL1 < MIN_PL to MIN_PL (spec compliance) |
| Dynamic transition | Runtime PL1 change under load — PID re-convergence |
| Throttle engagement | PERF_STATUS counter increments during MIN_PL enforcement |
| Throttle release | PERF_STATUS counter stops after PL1 restored to TDP |
| Power convergence | EWMA settles to MIN_PL within 5× tau |
| Power recovery | EWMA settles back to TDP within 5× tau |
| Cyclic robustness | 10 consecutive toggle cycles without drift or error |
| System stability | No MCA/IERR/hang across all toggle cycles |

---

## Section D: Spec References

| Source | Section | Relevance |
|--------|---------|-----------|
| [Intel RAPL HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/RAPL/RAPL.html) | TPMI register definitions | PL1_CONTROL, PL_INFO, PERF_STATUS field layouts |
| [PrimeCode RAPL DMR HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/RAPL/RAPL.html) | PL1 clipping, always-enabled | PL1 clips to MIN_PL; EN bit ignored |
| [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) | NWP TPMI path | NIO register paths |
| [Socket RAPL KB](../../pm_features/power_rapl/socket_rapl.md) | KPI & Timing | tau range 1–5s, PID loop 1ms, settling 3–5× tau |
| HSD 14024988302 | PL1 always-enabled design decision | PrimeCode ignores EN bit, clips to MIN_PL |

---

## Section E: Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| PID oscillation on rapid PL1 toggle | Medium | Medium | 5× tau wait ensures full EWMA convergence per cycle |
| Frequency stuck at Pm after TDP restore | Low | High | Verify freq recovery in step 13; if stuck, indicates PID bug |
| PERF_STATUS counter overflow during test | Very Low | Low | Counter is 32-bit; 10 cycles × 5s = 50s total throttle time — no overflow risk |
| MCA during rapid limit change | Low | High | Monitor mcelog; any MCA is an immediate fail |

---

## Section F: Recommendations

1. **Script implementation**: Extend existing RAPL PMx test or create `rapl_pl1_toggle_stress.py` under `pm/Active_PM/` with parameterized cycle count
2. **Cross-product with PL2**: Future TC should toggle PL2 simultaneously to validate multi-limit PID interaction
3. **Tau sweep variant**: Run with tau=1s and tau=5s to validate settling at both extremes
4. **OOB toggle variant**: Repeat via PECI-over-MCTP OOB path (covered by TCD scope item D)