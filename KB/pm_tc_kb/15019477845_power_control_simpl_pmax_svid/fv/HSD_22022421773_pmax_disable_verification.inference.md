# Deep Analysis: PMAX Disable Verification

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421773 |
| **Title** | [Silicon Only] PMAX Disable Verification |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | PMAX |
| **Sub-Feature** | PMAX disable — verify no soft/hard throttle when PMAX feature is disabled |
| **NWP Disposition** | **Runnable_On_N-1** |

---

### Test Case Intent

Verify that when PMAX is **disabled** (`punit_supervises_pmax=0` / `pmax_disable=0`), injecting a PMAX event does **not** cause throttle. Key assertion: `package_therm_status.pmax_log = 0` despite inject active. Confirms the disable path is effective. NWP: single `imh0` only.

---

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| SV session | `sv.socket0.imh0` reachable |
| Platform S0 | Fully booted; no pending MCA |
| Idle | No active PMAX throttle before test |
| Baseline pmax_log | Read before test — must be 0 |

---

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|----------------------|-------------------|
| 1 | Record baseline pmax_log = 0. `baseline = sv.socket0.imh0.punit.throttle.package_therm_status.pmax_log.read(); assert baseline == 0` | pmax_log = 0 at start | pmax_log already set — clear residual state before test |
| 2 | Disable PMAX supervision and external trigger. `sv.socket0.imh0.punit.throttle.pmax_gpio_trigger.external_trigger.write(0x0); sv.socket0.imh0.punit.throttle.pmax_service.punit_supervises_pmax.write(0x0); sv.socket0.imh0.punit.throttle.pmax_gpio_trigger.pmax_disable.write(0x0)` | Supervision disabled | Register write fails — check BIOS PMAX lock |
| 3 | Enable bypass and inject PMAX; verify no throttle. `sv.socket0.imh0.pcodeio_map.io_pmax_config.global_pmax_latch_bypass.write(0x1); sv.socket0.imh0.pcodeio_map.io_pmax_config.global_pmax_inject.write(0x1); import time; time.sleep(1.0); pmax_log = sv.socket0.imh0.punit.throttle.package_therm_status.pmax_log.read(); assert pmax_log == 0` | pmax_log = 0 — PMAX inject ignored (disabled) | pmax_log = 1 — PMAX still firing despite disable; check punit_supervises_pmax fuse |
| 4 | Clear inject and restore supervision. `sv.socket0.imh0.pcodeio_map.io_pmax_config.global_pmax_inject.write(0x0); sv.socket0.imh0.punit.throttle.pmax_service.punit_supervises_pmax.write(0x1)` | Inject cleared; supervision restored | Register write fails |

---

### Pass / Fail Criteria

- **PASS**: `pmax_log = 0` with inject active when PMAX disabled; no soft or hard throttle observed; frequency unchanged.
- **FAIL**: `pmax_log = 1` during inject despite disable — PMAX disable path not effective.

---

### Health Checks

| Register / Log | Access | Pass/Fail Criteria |
|----------------|--------|-------------------|
| pmax_log | sv.socket0.imh0.punit.throttle.package_therm_status.pmax_log | Must remain 0 during inject |
| perf_limit_reasons | sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.perf_limit_reasons | No PMAX PLR bit during disabled inject |
| punit_supervises_pmax | sv.socket0.imh0.punit.throttle.pmax_service.punit_supervises_pmax | = 0 during disabled phase |

---

### Post-Process

Clear inject and restore supervision after test. Collect NLOG if `pmax_log` asserted unexpectedly.

---

### References

- [DMR PMax HAS](https://docs.intel.com/documents/pm_doc/src/server/dmr/pm_features/dmr_pmax.html) — PMAX disable mask; punit_supervises_pmax control
- [Punit Registers](https://docs.intel.com/documents/sysip_pm/punit/assets/punit_registers.html) — pmax_service / pmax_gpio_trigger fields

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies that when PMAX is disabled (`pmax_disable=0` + supervision off), injecting a PMAX event does NOT cause throttle. Functional on NWP (single imh0 only).

Tags: `DMR_PO`, `plc.feature.p2`, `PMSS_NWP_READINESS_CHECK`.

---

## Section B: NWP-Specific Test Procedure

### Adapted Command (NWP)
```bash
python runPmx.py -x nwp.xml -p pmax -tM 60
```

### NWP Disable Sequence
```python
# NWP: disable PMAX and verify no throttle on inject
sv.socket0.imh0.punit.throttle.pmax_gpio_trigger.external_trigger.write(0x0)
sv.socket0.imh0.punit.throttle.pmax_service.punit_supervises_pmax.write(0x0)
sv.socket0.imh0.punit.throttle.pmax_gpio_trigger.pmax_disable.write(0x0)
# Enable bypass and inject
sv.socket0.imh0.pcodeio_map.io_pmax_config.global_pmax_latch_bypass.write(0x1)
sv.socket0.imh0.pcodeio_map.io_pmax_config.global_pmax_inject.write(0x1)
# Verify: no throttle applied
sv.socket0.imh0.punit.throttle.package_therm_status.pmax_log.read()  # expect = 0
```

### Pass Criteria
- `pmax_log` = 0 despite inject (PMAX disabled, no throttle)
- Soft and hard throttle both absent
- System performance unaffected by inject when PMAX disabled

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; `sv.socket0.imh0.*` only (NWP single IMH); PMAX disable mechanism same**

**Priority**: Medium — `plc.feature.p2`; verifies PMAX can be safely disabled for test scenarios requiring unrestricted power
