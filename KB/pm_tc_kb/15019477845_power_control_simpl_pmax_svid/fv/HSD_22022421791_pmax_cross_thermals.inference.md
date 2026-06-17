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
