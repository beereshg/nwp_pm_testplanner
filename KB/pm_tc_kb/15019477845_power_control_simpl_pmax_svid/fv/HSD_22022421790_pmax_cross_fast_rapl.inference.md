# Deep Analysis: PMAX Cross Fast RAPL

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421790 |
| **Title** | PMAX Cross Fast Rapl |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | PMAX |
| **Sub-Feature** | PMAX × Fast RAPL cross-feature — PMAX hard throttle concurrent with Fast RAPL, verify stability |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This cross-feature test runs Fast RAPL workload concurrently with a PMAX hard throttle injection and verifies system stability (no crash, no MCA). Both PMAX and Fast RAPL are functional on NWP.

*Note*: Test command is empty in HSD (TBD). Test approach: use `global_pmax_inject` for PMAX + concurrent Fast RAPL stress via PTAT or workload.

Tags: `New_Content`, `plc.ti_gate.b0`, `pm.xproducts.pm`, `NGA_MAIN`, `plc.feature.p3`, `PMSS_NWP_READINESS_CHECK`.

---

## Section B: NWP-Specific Test Procedure

### NWP Approach (command TBD in source)
```python
# NWP: PMAX × Fast RAPL cross test
# 1. Start RAPL stress (PTAT workload with RAPL PL1/PL2 limits)
# 2. Inject PMAX hard throttle simultaneously
sv.socket0.imh0.pcodeio_map.io_pmax_config.global_pmax_inject.write(0x1)
# 3. Run for several minutes
# 4. Verify no crashes, MCAs, or hangs
# 5. Clear PMAX inject
sv.socket0.imh0.pcodeio_map.io_pmax_config.global_pmax_inject.write(0x0)
```

### Pass Criteria
- System stable with concurrent PMAX hard throttle + Fast RAPL
- No machine check errors (MCAs)
- No system hang or crash
- Frequency and power recovery after PMAX clear

---

## Section F: Recommendation

**Recommendation: ADOPT — No command in source TC; implement via `global_pmax_inject` + concurrent PTAT/RAPL workload; `sv.socket0.imh0.*` only on NWP; `NGA_MAIN` priority**

**Priority**: Medium — `plc.feature.p3`; cross-feature stability is a `ti_gate.b0` requirement; run after individual PMAX and RAPL tests pass
