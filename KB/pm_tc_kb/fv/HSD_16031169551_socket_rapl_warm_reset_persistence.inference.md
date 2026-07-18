# TC: Socket RAPL Warm Reset Register Persistence

## Section A: Validation Scope

Validates the warm reset register persistence scenarios defined in [TCD 16031169466 — Socket RAPL Boot/Reset Boundary Conditions](https://hsdes.intel.com/appstore/article-one/#/16031169466) §5, rows 2 (ENERGY_STATUS persistence), 3 (PERF_STATUS persistence), and 5 (LOCK bit persistence).
Environment: NWP-IMH post-silicon FV.

## Section B: Preconditions

| Requirement | Detail |
|-------------|--------|
| Platform | NWP-IMH system with JTAG/PythonSV access |
| BIOS knobs | Default RAPL configuration; PL1/PL2 locked by BIOS |
| OS / Driver | Linux with `intel_rapl` driver loaded |
| Feature state | Socket RAPL active; ENERGY_STATUS accumulating |
| Tool | PythonSV with namednodes access to `sv.socket0.nio.punit.tpmi.socket_rapl.*` |
| Starting state | System booted to OS; workload running long enough to accumulate ENERGY_STATUS > 0 and PERF_STATUS > 0 (if throttling) |

## Section C: Automation

**Command line:**
`python scripts/pm/fv/socket_rapl_warm_reset_persistence.py`

**Script / tool:** PythonSV-based; requires JTAG for register reads + platform warm reset capability
**Estimated runtime:** ~5 minutes (includes warm reset + re-boot)

## Section D: Test Steps

1. **Read pre-reset ENERGY_STATUS** — run `sv.socket0.nio.punit.tpmi.socket_rapl.energy_status.read()`. Expected: ENERGY [31:0] > 0 (energy accumulated since boot).
2. **Read pre-reset PERF_STATUS** — run `sv.socket0.nio.punit.tpmi.socket_rapl.perf_status.read()`. Expected: record value (may be 0 if no throttling; if so, trigger brief PL1=MIN_PL to force throttle, then restore PL1=TDP).
3. **Read pre-reset LOCK bits** — run `sv.socket0.nio.punit.tpmi.socket_rapl.pl1_control.read()` and extract LOCK [63]. Expected: LOCK = 1 (BIOS locked).
4. **Trigger warm reset** — issue platform warm reset via BMC or PythonSV reset command. Expected: system resets without powergood de-assertion.
5. **Wait for OS re-boot** — wait for PH6 + CPL3 + OS boot complete. Expected: system reaches OS prompt.
6. **Read post-reset ENERGY_STATUS** — run `sv.socket0.nio.punit.tpmi.socket_rapl.energy_status.read()`. Expected: ENERGY [31:0] >= pre-reset value (persisted, sticky).
7. **Read post-reset PERF_STATUS** — run `sv.socket0.nio.punit.tpmi.socket_rapl.perf_status.read()`. Expected: PWR_LIMIT_THROTTLE_CTR [31:0] >= pre-reset value (persisted, sticky).
8. **Read post-reset LOCK bits** — run `sv.socket0.nio.punit.tpmi.socket_rapl.pl1_control.read()` and extract LOCK [63]. Expected: LOCK = 1 (persisted across warm reset).

## Section E: Pass/Fail Measurement Method

**Bar:** Per [TCD 16031169466](https://hsdes.intel.com/appstore/article-one/#/16031169466) §5:
- Row 2: `ENERGY_STATUS.ENERGY[31:0] > pre_reset_energy_value`
- Row 3: `PERF_STATUS.PWR_LIMIT_THROTTLE_CTR[31:0] >= pre_reset_throttle_ctr`
- Row 5: `PL1_CONTROL.LOCK == pre_reset_lock_value`

**Measurement procedure (this TC only):**
1. Compare: post-reset ENERGY_STATUS >= pre-reset ENERGY_STATUS (account for rollover if post < pre)
2. Compare: post-reset PERF_STATUS >= pre-reset PERF_STATUS
3. Compare: post-reset PL1_CONTROL.LOCK == pre-reset PL1_CONTROL.LOCK
4. Execution assertions: warm reset did not assert powergood_rst_b; no MCA during reset; test completes < 5 minutes

## Section F: NWP Delta

- Register path uses `sv.socket0.nio.punit.tpmi.socket_rapl.*` (NIO die, not IMH)
- Single NIO die — no IMH-S leaf aggregation step to verify
