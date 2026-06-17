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
