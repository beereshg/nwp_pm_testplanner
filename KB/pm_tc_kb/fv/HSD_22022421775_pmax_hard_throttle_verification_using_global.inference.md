# Deep Analysis: PMAX Hard Throttle Verification using Global PMAX Inject

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421775 |
| **Title** | [Silicon Only] PMAX Hard Throttle Verification using Global PMAX Inject |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | PMAX |
| **Sub-Feature** | PMAX hard throttle via global_pmax_inject — immediate frequency collapse (not bandwidth-based) |
| **NWP Disposition** | **Runnable_On_N-1** |

---

### Test Case Intent

Verify PCode applies **hard (immediate) PMAX throttle** when `global_pmax_inject` is asserted with `punit_root_supervisor=0`. Hard throttle causes immediate frequency collapse (PROCHOT-like), not a gradual bandwidth reduction. Key assertion: `pmax_log = 1` and frequency drops to Psafe or below within 1 poll cycle. NWP: single `imh0` only.

---

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| SV session | `sv.socket0.imh0` reachable |
| Platform S0 | Fully booted; no pending MCA |
| Psafe freq known | Read `pkg_computed_pl1_power_budget_0` at idle as baseline |
| punit_supervises_pmax | fuse = 1 (verified pre-test) |
| BIOS PMAX lock | PMAX CONTROL not locked by BIOS |

---

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|----------------------|-------------------|
| 1 | Configure hard throttle path: disable external trigger, set supervision, punit_root_supervisor=0. `sv.socket0.imh0.punit.throttle.pmax_gpio_trigger.external_trigger.write(0x0); sv.socket0.imh0.punit.throttle.pmax_service.punit_supervises_pmax.write(0x1); sv.socket0.imh0.punit.throttle.pmax_service.punit_root_supervisor.write(0x0); sv.socket0.imh0.punit.throttle.pmax_gpio_trigger.pmax_disable.write(0x0)` | Registers set; hard path configured | Write fails — check PMAX CONTROL lock bit |
| 2 | Enable bypass and inject hard PMAX. `sv.socket0.imh0.pcodeio_map.io_pmax_config.global_pmax_latch_bypass.write(0x1); sv.socket0.imh0.pcodeio_map.io_pmax_config.global_pmax_inject.write(0x1); import time; time.sleep(1.0)` | System stable; no MCA after 1 s | System hang or MCA — catastrophic error; check for residual PMAX state |
| 3 | Verify hard throttle fired. `pmax_log = sv.socket0.imh0.punit.throttle.package_therm_status.pmax_log.read(); assert pmax_log == 1, 'Hard throttle must fire'` | pmax_log = 1; frequency at Psafe or lower | pmax_log = 0 — hard throttle not firing; check punit_root_supervisor = 0 |
| 4 | Clear inject; verify recovery. `sv.socket0.imh0.pcodeio_map.io_pmax_config.global_pmax_inject.write(0x0); time.sleep(2.0); pmax_log = sv.socket0.imh0.punit.throttle.package_therm_status.pmax_log.read()` | pmax_log = 0; frequency recovers to normal | pmax_log stays set — stale semaphore; check GLOBAL_PMAX_SEMAPHORE |

---

### Pass / Fail Criteria

- **PASS**: Hard throttle fires immediately on inject; `pmax_log = 1`; system stable; frequency recovers after inject cleared.
- **FAIL**: Hard throttle does not fire; soft throttle fires instead; MCA during throttle; frequency does not recover.

---

### Health Checks

| Register / Log | Access | Pass/Fail Criteria |
|----------------|--------|-------------------|
| pmax_log | sv.socket0.imh0.punit.throttle.package_therm_status.pmax_log | = 1 during inject; = 0 after clear |
| GLOBAL_PMAX_SEMAPHORE | sv.socket0.imh0.punit.IO_THERM_INDICATIONS.GLOBAL_PMAX_SEMAPHORE | Cleared post-throttle |
| perf_limit_reasons | sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.perf_limit_reasons | PMAX hard throttle PLR bit set during inject |
| NLOG PMAX | peg_client --nlog --filter PMAX | No unexpected fatal events |

---

### Post-Process

Clear inject: `global_pmax_inject.write(0x0)`. Restore `punit_root_supervisor` to 1. Clear semaphore if stuck. Collect NLOG on failure.

---

### References

- [DMR PMax HAS](https://docs.intel.com/documents/pm_doc/src/server/dmr/pm_features/dmr_pmax.html) — hard throttle; punit_root_supervisor=0; global_pmax_inject; semaphore clear flow
- [MT PMax HAS](https://docs.intel.com/documents/pm_doc/src/server/gnr/features/multi-threshold_pmax_detector/mt_pmax.html) — hard vs soft throttle distinction; PLR bit definitions

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

PMAX hard throttle causes immediate frequency collapse (PROCHOT-like response). Uses `io_pmax_config.global_pmax_inject` with `punit_root_supervisor=0` (hard path). Functional on NWP.

Tags: `DMR_PO`, `plc.feature.p2`, `PMSS_NWP_READINESS_CHECK`.

---

## Section B: NWP-Specific Test Procedure

### Adapted Command (NWP)
```bash
python runPmx.py -x nwp.xml -p pmax -tM 60
```

### NWP Hard Throttle Sequence
```python
# NWP: hard throttle via global_pmax_inject
sv.socket0.imh0.punit.throttle.pmax_gpio_trigger.external_trigger.write(0x0)
sv.socket0.imh0.punit.throttle.pmax_service.punit_supervises_pmax.write(0x1)
sv.socket0.imh0.punit.throttle.pmax_service.punit_root_supervisor.write(0x0)  # hard path
sv.socket0.imh0.punit.throttle.pmax_gpio_trigger.pmax_disable.write(0x0)
sv.socket0.imh0.pcodeio_map.io_pmax_config.global_pmax_latch_bypass.write(0x1)
# Inject hard throttle
sv.socket0.imh0.pcodeio_map.io_pmax_config.global_pmax_inject.write(0x1)
# Verify hard throttle active
sv.socket0.imh0.punit.throttle.package_therm_status.pmax_log.read()  # expect = 1
```

### Pass Criteria
- Hard throttle fires immediately on inject (frequency drops to Pn or lower)
- `pmax_log` set in `package_therm_status`
- System stable during hard throttle
- Throttle clears when inject de-asserted

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; `sv.socket0.imh0.*` only; hard throttle inject mechanism same on NWP**

**Priority**: High — `DMR_PO`, `plc.feature.p2`; hard throttle is the emergency PMAX response — must function correctly
