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
