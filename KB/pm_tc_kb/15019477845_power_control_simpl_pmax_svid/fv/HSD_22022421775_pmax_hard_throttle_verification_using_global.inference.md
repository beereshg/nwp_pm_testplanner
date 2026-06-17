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
