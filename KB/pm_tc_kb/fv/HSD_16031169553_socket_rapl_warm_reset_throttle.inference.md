# TC: Socket RAPL Warm Reset Under Active Throttle

## Section A: Validation Scope

Validates the warm reset under active RAPL throttle scenario defined in [TCD 16031169466 — Socket RAPL Boot/Reset Boundary Conditions](https://hsdes.intel.com/appstore/article-one/#/16031169466) §5, row 8 (fresh RAPL_PERF_LIMIT HPM after reset), and §6 corner cases: warm reset during active throttle, rapid warm reset succession.
Environment: NWP-IMH post-silicon FV.

## Section B: Preconditions

| Requirement | Detail |
|-------------|--------|
| Platform | NWP-IMH system with JTAG/PythonSV access and warm reset capability |
| BIOS knobs | Default RAPL configuration; PL1/PL2 at defaults |
| OS / Driver | Linux with `intel_rapl` driver loaded; stress workload available (e.g. `stress-ng`) |
| Feature state | Socket RAPL active; PL1 set to value that will cause throttling under load |
| Tool | PythonSV with namednodes access; `stress-ng` or equivalent CPU workload |
| Starting state | System booted to OS; no active RAPL throttling initially |

## Section C: Automation

**Command line:**
`python scripts/pm/fv/socket_rapl_warm_reset_throttle.py`

**Script / tool:** PythonSV-based; requires JTAG for register reads + platform warm reset + workload generation
**Estimated runtime:** ~10 minutes (includes workload + 3x warm reset cycles)

## Section D: Test Steps

1. **Start CPU stress workload** — run `stress-ng --cpu 0 --timeout 60s` in background. Expected: all cores loaded; package power > TDP.
2. **Set PL1 below current power** — write PL1 = MIN_PL via TPMI to force RAPL throttling. Expected: RAPL PID begins frequency reduction.
3. **Verify active throttle** — read `sv.socket0.nio.punit.tpmi.socket_rapl.perf_status.read()` twice with 1s gap. Expected: PWR_LIMIT_THROTTLE_CTR is incrementing (delta > 0).
4. **Record pre-reset PERF_STATUS** — store current PERF_STATUS value. Expected: value > 0 (throttling active).
5. **Record pre-reset ENERGY_STATUS** — store current ENERGY_STATUS value. Expected: value > 0.
6. **Trigger warm reset while throttling** — issue warm reset via BMC. Expected: system resets; PID controllers stop.
7. **Wait for OS re-boot** — wait for PH6 + CPL3 + OS boot. Expected: system reaches OS prompt.
8. **Verify no stale RAPL throttle** — read `sv.socket0.nio.punit.tpmi.socket_rapl.perf_status.read()` twice with 2s gap (no workload running). Expected: PWR_LIMIT_THROTTLE_CTR NOT incrementing (no stale throttle from previous boot).
9. **Verify ENERGY_STATUS persisted** — read ENERGY_STATUS. Expected: value >= pre-reset (sticky).
10. **Verify PERF_STATUS persisted** — read PERF_STATUS. Expected: value >= pre-reset (sticky).
11. **Repeat warm reset 2 more times (rapid succession)** — trigger warm reset, wait for boot, verify no stale throttle. Repeat once more. Expected: each iteration produces clean PH6 init; no accumulated stale state; PERF_STATUS not incrementing without workload.

## Section E: Pass/Fail Measurement Method

**Bar:** Per [TCD 16031169466](https://hsdes.intel.com/appstore/article-one/#/16031169466) §5:
- Row 8: No RAPL throttling observed before workload starts post-reset

**Measurement procedure (this TC only):**
1. Verify: post-reset PERF_STATUS delta = 0 over 2s without workload (no stale throttle)
2. Verify: post-reset ENERGY_STATUS >= pre-reset (sticky persistence)
3. Verify: 3 consecutive warm resets all produce clean state
4. Execution assertions: no MCA during any reset; each boot completes < 3 minutes; no stale RAPL_PERF_LIMIT HPM effects

## Section F: NWP Delta

- Register path uses `sv.socket0.nio.punit.tpmi.socket_rapl.*` (NIO die, not IMH)
- Single NIO die sends RAPL_PERF_LIMIT HPM to all 4 CBBs — verify all CBBs receive fresh HPM
