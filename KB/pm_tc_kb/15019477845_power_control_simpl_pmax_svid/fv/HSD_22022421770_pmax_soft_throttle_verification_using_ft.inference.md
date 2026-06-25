# Deep Analysis: PMAX Soft Throttle Verification using FT PMAX INJECT

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421770 |
| **Title** | [Silicon Only]: PMAX Soft Throttle Verification using FT PMAX INJECT |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | PMAX |
| **Sub-Feature** | PMAX soft throttle via ft_pmax_inject — Punit supervises PMAX, applies bandwidth-based throttle |
| **NWP Disposition** | **Runnable_On_N-1** |

---

### Test Case Intent

Verify PCode applies **soft (bandwidth-based) PMAX throttle** when the fast-threshold PMAX wire is asserted via FT inject. Soft throttle reduces frequency proportionally rather than causing an immediate hard collapse. Key assertion: `package_therm_status.pmax_log = 1` and soft PLR bit set; system remains stable and recovers after inject cleared. NWP: single `imh0` only.

---

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| SV session | `sv.socket0.imh0` reachable without timeout |
| Platform S0 | Fully booted; no pending MCA |
| Idle | No workload running before inject |
| punit_supervises_pmax | fuse = 1 (verified by TC 22022421799) |
| pmax_mt_en | fuse = 1 (MT-PMAX enabled) |
| PMx | `python runPmx.py -x nwp.xml -p pmax -tM 60` available |

---

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|----------------------|-------------------|
| 1 | Disable external trigger and enable Punit supervision. `sv.socket0.imh0.punit.throttle.pmax_gpio_trigger.external_trigger.write(0x0); sv.socket0.imh0.punit.throttle.pmax_service.punit_supervises_pmax.write(0x1); sv.socket0.imh0.punit.throttle.pmax_service.punit_root_supervisor.write(0x1)` | Supervision enabled; external trigger disabled | Register write fails — check BIOS PMAX lock |
| 2 | Disable hard throttle path and enable bypass. `sv.socket0.imh0.punit.throttle.pmax_gpio_trigger.pmax_disable.write(0x1); sv.socket0.imh0.pcodeio_map.io_pmax_config.global_pmax_latch_bypass.write(0x1)` | Hard path disabled; latch bypass enabled | pmax_disable or bypass register not responding |
| 3 | Assert PMAX soft throttle inject and verify response within 2 s. `import time; sv.socket0.imh0.pcodeio_map.io_pmax_config.global_pmax_inject.write(0x1); time.sleep(2.0); pmax_log = sv.socket0.imh0.punit.throttle.package_therm_status.pmax_log.read(); assert pmax_log == 1` | pmax_log = 1; soft throttle PLR bit set; frequency reduced but system stable | pmax_log = 0 — soft throttle not firing; check punit_root_supervisor |
| 4 | Clear inject; verify recovery. `sv.socket0.imh0.pcodeio_map.io_pmax_config.global_pmax_inject.write(0x0); time.sleep(1.0); pmax_log = sv.socket0.imh0.punit.throttle.package_therm_status.pmax_log.read()` | pmax_log = 0; frequency returns to normal | pmax_log stays set — stuck throttle; check for stale semaphore |

---

### Pass / Fail Criteria

- **PASS**: `pmax_log` asserts during inject; soft throttle PLR bit set; system stable (no MCA, no hang); `pmax_log` clears after inject removed.
- **FAIL**: `pmax_log` = 0 during inject; hard throttle fires instead of soft; system hang or MCA during test.

---

### Health Checks

| Register / Log | Access | Pass/Fail Criteria |
|----------------|--------|-------------------|
| pmax_log | sv.socket0.imh0.punit.throttle.package_therm_status.pmax_log | = 1 during inject; = 0 after clear |
| perf_limit_reasons | sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.perf_limit_reasons | PMAX/MT-PMAX PLR bit set during soft throttle |
| io_pmax_config | sv.socket0.imh0.pcodeio_map.io_pmax_config | global_pmax_inject = 1 during test; cleared after |
| NLOG PMAX | peg_client --nlog --filter PMAX | No fatal/error-level PMAX events |

---

### Post-Process

Clear inject: `sv.socket0.imh0.pcodeio_map.io_pmax_config.global_pmax_inject.write(0x0)`. Restore pmax_disable to 0 if changed. Collect NLOG if failed. Verify no residual PLR bits.

---

### References

- [DMR PMax HAS](https://docs.intel.com/documents/pm_doc/src/server/dmr/pm_features/dmr_pmax.html) — PMAX soft throttle via punit_root_supervisor=1; bandwidth-based throttle
- [MT PMax HAS](https://docs.intel.com/documents/pm_doc/src/server/gnr/features/multi-threshold_pmax_detector/mt_pmax.html) — FT PMAX inject; soft vs hard throttle path
- [NWP NIO GPIO HAS](https://docs.intel.com/documents/custom-xeon/newport-docs/has/gpio/newport_nio_gpio_has.html) — PMAX_TRIGGER_IO; NWP single NIO topology

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

PMAX soft throttle uses the Fast Threshold PMAX inject mechanism to simulate a PMAX overcurrent event without actual hardware trigger. Punit supervises PMAX and applies soft (bandwidth) throttle. Functional on NWP.

Tags: `DMR_PO`, `plc.feature.p2`, `PMSS_NWP_READINESS_CHECK`.

---

## Section B: NWP-Specific Test Procedure

### Adapted Command (NWP)
```bash
python runPmx.py -x nwp.xml -p pmax -tM 60
```

### NWP Soft Throttle Sequence
```python
# NWP: inject PMAX soft throttle (imh0 only)
# 1. Disable external trigger
sv.socket0.imh0.punit.throttle.pmax_gpio_trigger.external_trigger.write(0x0)
# 2. Enable Punit supervision
sv.socket0.imh0.punit.throttle.pmax_service.punit_supervises_pmax.write(0x1)
sv.socket0.imh0.punit.throttle.pmax_service.punit_root_supervisor.write(0x1)
# 3. Disable hard throttle path
sv.socket0.imh0.punit.throttle.pmax_gpio_trigger.pmax_disable.write(0x1)
# 4. Enable bypass and inject
sv.socket0.imh0.pcodeio_map.io_pmax_config.global_pmax_latch_bypass.write(0x1)
# 5. Verify soft throttle applied (perf limit reason)
sv.socket0.imh0.punit.throttle.package_therm_status.pmax_log.read()
```

### Pass Criteria
- Soft throttle applied after inject (bandwidth-based, not hard shutoff)
- `pmax_log` bit set in `package_therm_status`
- Perf limit reason reflects PMAX throttle
- System recovers when inject cleared

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; register paths use `sv.socket0.imh0.*` only (no imh1 on NWP); PMAX inject mechanism same**

**Priority**: Medium — `plc.feature.p2`; soft throttle injection is the key debug mechanism for PMAX validation
