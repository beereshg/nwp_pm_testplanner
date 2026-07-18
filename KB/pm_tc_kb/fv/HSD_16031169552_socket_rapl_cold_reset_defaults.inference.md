# TC: Socket RAPL Cold Reset Register Defaults

## Section A: Validation Scope

Validates the cold reset register defaults scenarios defined in [TCD 16031169466 — Socket RAPL Boot/Reset Boundary Conditions](https://hsdes.intel.com/appstore/article-one/#/16031169466) §5, rows 4 (LOCK bit cleared), 6 (PL1/PL2 defaults), and 7 (PL_INFO repopulation).
Environment: NWP-IMH post-silicon FV.

## Section B: Preconditions

| Requirement | Detail |
|-------------|--------|
| Platform | NWP-IMH system with JTAG/PythonSV access and BMC cold reset capability |
| BIOS knobs | Default RAPL configuration |
| OS / Driver | Linux with `intel_rapl` driver loaded |
| Feature state | Socket RAPL active; PL1/PL2 LOCK = 1 (BIOS locked) before cold reset |
| Tool | PythonSV with namednodes access; BMC or AC power cycle capability |
| Starting state | System booted to OS with BIOS-locked PL1/PL2; known TDP from PL_INFO |

## Section C: Automation

**Command line:**
`python scripts/pm/fv/socket_rapl_cold_reset_defaults.py`

**Script / tool:** PythonSV-based; requires JTAG for early register reads + cold reset capability
**Estimated runtime:** ~8 minutes (includes cold reset + full boot)

## Section D: Test Steps

1. **Record pre-reset PL_INFO** — run `sv.socket0.nio.punit.tpmi.socket_rapl.pl_info.read()`. Expected: MAX_PL1 [17:0] = fuse TDP; MAX_PL2 [53:36] = 1.2 x TDP.
2. **Confirm pre-reset LOCK = 1** — run `sv.socket0.nio.punit.tpmi.socket_rapl.pl1_control.show()`. Expected: LOCK [63] = 1.
3. **Trigger cold reset** — power cycle via BMC or AC power cycle. Expected: powergood_rst_b asserted; full platform re-init.
4. **Halt at PH6 completion (before BIOS CPL3)** — break after PrimeCode PH6 init, before BIOS locks registers. Expected: PythonSV break at post-PH6 sync point.
5. **Read PL1_CONTROL.LOCK** — run `sv.socket0.nio.punit.tpmi.socket_rapl.pl1_control.read()` and extract LOCK [63]. Expected: LOCK = 0 (cleared by cold reset).
6. **Read PL2_CONTROL.LOCK** — run `sv.socket0.nio.punit.tpmi.socket_rapl.pl2_control.read()` and extract LOCK [63]. Expected: LOCK = 0 (cleared by cold reset).
7. **Read PL_INFO** — run `sv.socket0.nio.punit.tpmi.socket_rapl.pl_info.read()`. Expected: MAX_PL1 = fuse TDP; MAX_PL2 = 1.2 x fuse TDP (repopulated from fuses at PH6).
8. **Resume boot to OS** — release PythonSV break. Expected: BIOS re-programs PL1=TDP, PL2=1.2xTDP, sets LOCK=1.
9. **Read PL1/PL2 at OS handoff** — run `sv.socket0.nio.punit.tpmi.socket_rapl.pl1_control.read()`. Expected: PWR_LIM = PL_INFO.MAX_PL1 (TDP); LOCK = 1.
10. **Read PL2 at OS handoff** — run `sv.socket0.nio.punit.tpmi.socket_rapl.pl2_control.read()`. Expected: PWR_LIM = PL_INFO.MAX_PL2 (1.2xTDP); LOCK = 1.

## Section E: Pass/Fail Measurement Method

**Bar:** Per [TCD 16031169466](https://hsdes.intel.com/appstore/article-one/#/16031169466) §5:
- Row 4: `PL1_CONTROL.LOCK == 0` AND `PL2_CONTROL.LOCK == 0` (sampled before BIOS lock)
- Row 6: `PL1_CONTROL.PWR_LIM == PL_INFO.MAX_PL1` AND `PL2_CONTROL.PWR_LIM == PL_INFO.MAX_PL2`
- Row 7: `PL_INFO.MAX_PL1 == fuse_TDP` AND `PL_INFO.MAX_PL2 == 1.2 x fuse_TDP`

**Measurement procedure (this TC only):**
1. At PH6 (pre-BIOS): verify LOCK = 0 for both PL1 and PL2
2. At PH6: verify PL_INFO matches fuse TDP values
3. At OS handoff: verify PL1 = TDP, PL2 = 1.2xTDP, both locked
4. Execution assertions: cold reset asserted powergood_rst_b; no MCA; boot completes < 5 minutes

## Section F: NWP Delta

- Register path uses `sv.socket0.nio.punit.tpmi.socket_rapl.*` (NIO die, not IMH)
- NWP PL_INFO TDP derived from single NIO die fuses
