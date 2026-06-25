# Deep Analysis: PMAX Cross Thermals

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421791 |
| **Title** | PMAX Cross Thermals |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | PMAX |
| **Sub-Feature** | PMAX × Thermals cross-feature — PMAX hard throttle concurrent with thermal throttle, verify stability |
| **NWP Disposition** | **Runnable_On_N-1** |

---

### Test Case Intent

Verify system **stability** when PMAX hard throttle is concurrent with thermal throttle (PROCHOT inject). Both features activate simultaneously; PMAX hard throttle should dominate over thermal throttle. `NGA_MAIN` / `ti_gate.b0` cross-feature test. NWP: single `imh0`.

---

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| SV session | `sv.socket0.imh0` reachable |
| Thermal debug | `import diamondrapids.pm.Active_PM.Thermal_Management.CPU_Thermal_Management.thermal_debug as td` |
| Platform S0 | No pre-existing MCAs or thermal events |

---

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|----------------------|-------------------|
| 1 | Inject thermal throttle (PROCHOT). `sv.socket0.imh0.punit.prochot_trigger.write(1); import time; time.sleep(1.0); plr = sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.perf_limit_reasons.read(); print(f'PLR=0x{plr:08X}')` | PROCHOT PLR bit set; thermal throttle active | PROCHOT PLR not set — thermal inject failed |
| 2 | Simultaneously inject PMAX hard throttle. `sv.socket0.imh0.pcodeio_map.io_pmax_config.global_pmax_latch_bypass.write(0x1); sv.socket0.imh0.pcodeio_map.io_pmax_config.global_pmax_inject.write(0x1); time.sleep(30)` | System stable for 30 s; no MCA or hang | MCA or hang — dual throttle instability; collect NLOG |
| 3 | Verify concurrent throttle: both PMAX and Thermal PLR bits set. `plr = sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.perf_limit_reasons.read(); pmax_log = sv.socket0.imh0.punit.throttle.package_therm_status.pmax_log.read(); print(f'PLR=0x{plr:08X} pmax_log={pmax_log}')` | PMAX + PROCHOT PLR bits both set; PMAX dominates (lower ceiling) | Only one PLR bit — one path blocked |
| 4 | Clear both injections; verify full recovery. `sv.socket0.imh0.punit.prochot_trigger.write(0); sv.socket0.imh0.pcodeio_map.io_pmax_config.global_pmax_inject.write(0x0); time.sleep(2.0)` | Both PLR bits clear; frequency recovers | Stuck PLR — stale semaphore or hysteresis issue |

---

### Pass / Fail Criteria

- **PASS**: System stable with concurrent PROCHOT + PMAX; both PLR bits set; PMAX ceiling more restrictive; clean recovery.
- **FAIL**: MCA or hang during dual throttle; one path not active; stuck PLR after clear.

---

### Health Checks

| Register / Log | Access | Pass/Fail Criteria |
|----------------|--------|-------------------|
| pmax_log | sv.socket0.imh0.punit.throttle.package_therm_status.pmax_log | = 1 during PMAX inject |
| perf_limit_reasons | sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.perf_limit_reasons | Both PMAX and PROCHOT bits set concurrently |
| NLOG | peg_client --nlog --filter PMAX,THERMAL | No fatal events |

---

### Post-Process

Clear both injections. Restore prochot_trigger = 0. Collect NLOG on failure.

---

### References

- [DMR PMax HAS](https://docs.intel.com/documents/pm_doc/src/server/dmr/pm_features/dmr_pmax.html) — PMAX vs thermal priority; hard throttle dominance
- [DMR Thermal HAS](https://docs.intel.com/documents/pm_doc/src/server/dmr/pm_features/thermals/dmr_thermal.html) — PROCHOT inject; concurrent throttle behavior

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

Same cross-feature structure as TC 22022421790 but with Thermals instead of Fast RAPL. Runs thermal throttle (PROCHOT inject or high temp workload) concurrent with PMAX hard throttle injection. Verifies system stability under simultaneous thermal and PMAX events.

Tags: `New_Content`, `plc.ti_gate.b0`, `pm.xproducts.pm`, `NGA_MAIN`, `plc.feature.p3`, `PMSS_NWP_READINESS_CHECK`.

---

## Section B: NWP-Specific Test Procedure

### NWP Approach (command TBD in source)
```python
# NWP: PMAX × Thermals cross test
# 1. Inject PROCHOT to cause thermal throttle
sv.socket0.imh0.punit.prochot_trigger.write(1)
# 2. Simultaneously inject PMAX hard throttle
sv.socket0.imh0.pcodeio_map.io_pmax_config.global_pmax_inject.write(0x1)
# 3. Run for several minutes
# 4. Verify no crashes, MCAs, or hangs
# 5. Clear both injections
sv.socket0.imh0.punit.prochot_trigger.write(0)
sv.socket0.imh0.pcodeio_map.io_pmax_config.global_pmax_inject.write(0x0)
```

### Pass Criteria
- System stable with concurrent PROCHOT (thermal) + PMAX hard throttle
- No MCAs during dual-throttle condition
- Correct priority handling (PMAX hard throttle should dominate)
- Recovery after both cleared

---

## Section F: Recommendation

**Recommendation: ADOPT — No command in source TC; implement via `prochot_trigger` + `global_pmax_inject`; `sv.socket0.imh0.*` only; `NGA_MAIN` priority**

**Priority**: Medium — `plc.feature.p3`; dual throttle stability is a `ti_gate.b0` cross-feature requirement
