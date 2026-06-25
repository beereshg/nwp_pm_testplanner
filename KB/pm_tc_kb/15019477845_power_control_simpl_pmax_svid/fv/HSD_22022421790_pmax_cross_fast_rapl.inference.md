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

### Test Case Intent

Verify system **stability** when PMAX hard throttle is concurrent with Fast RAPL limiting. Both features activate simultaneously; the min(PMax ceiling, Fast RAPL ceiling) should be enforced without MCA or system hang. `NGA_MAIN` / `ti_gate.b0` cross-feature test. NWP: single `imh0`.

---

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| SV session | `sv.socket0.imh0` and `sv.socket0.cbb{0,1}` reachable |
| Workload | PTAT or stress-ng generating sustained load |
| RAPL active | Verify Fast RAPL loop operational (SVID IMON valid) |
| Platform S0 | No pre-existing MCAs |

---

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|----------------------|-------------------|
| 1 | Start sustained workload. Start PTAT or stress-ng and verify load is generating Fast RAPL response. `import time` | Workload running; Fast RAPL PLR bit (bit 9) visible in perf_limit_reasons | Fast RAPL not firing — SVID IMON invalid |
| 2 | Simultaneously inject PMAX hard throttle. `sv.socket0.imh0.punit.throttle.pmax_service.punit_supervises_pmax.write(0x1); sv.socket0.imh0.pcodeio_map.io_pmax_config.global_pmax_latch_bypass.write(0x1); sv.socket0.imh0.pcodeio_map.io_pmax_config.global_pmax_inject.write(0x1); time.sleep(30)` | System stable for 30 s with dual throttle; no MCA or hang | System hang or MCA — record NLOG and crash dump |
| 3 | Verify concurrent throttle state. `plr = sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.perf_limit_reasons.read(); print(f'PLR=0x{plr:08X}'); pmax_log = sv.socket0.imh0.punit.throttle.package_therm_status.pmax_log.read()` | Both PMAX and FAST_RAPL PLR bits set concurrently | Only one bit set — one throttle path blocked |
| 4 | Clear PMAX inject; verify Fast RAPL continues then clears with workload removed. `sv.socket0.imh0.pcodeio_map.io_pmax_config.global_pmax_inject.write(0x0); time.sleep(5.0)` | System stable post-clear; Fast RAPL clears after workload stops | Fast RAPL stuck after PMAX removed — check CBB pem_status |

---

### Pass / Fail Criteria

- **PASS**: System stable with concurrent PMAX + Fast RAPL; both PLR bits set; recovery clean after clear.
- **FAIL**: MCA, hang, or only one throttle active during concurrent test.

---

### Health Checks

| Register / Log | Access | Pass/Fail Criteria |
|----------------|--------|-------------------|
| pmax_log | sv.socket0.imh0.punit.throttle.package_therm_status.pmax_log | = 1 during PMAX inject |
| perf_limit_reasons bit 9 | sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.perf_limit_reasons | FAST_RAPL bit set during workload |
| pem_status | sv.socket0.cbb{0,1}.base.tpmi.pem_status | PEM excursion bit set during Fast RAPL |
| NLOG | peg_client --nlog --filter PMAX | No fatal events |

---

### Post-Process

Clear `global_pmax_inject`. Stop workload. Verify no residual PLR bits. Collect NLOG on failure.

---

### References

- [DMR PMax HAS](https://docs.intel.com/documents/pm_doc/src/server/dmr/pm_features/dmr_pmax.html) — PMAX hard throttle; min-ceiling arbitration with other RAPL controllers
- [Primecode Fast RAPL Flow](https://docs.intel.com/documents/primecode/primecode_two/firmware_architecture/flows_pm_features/fast_rapl.html) — concurrent Fast RAPL + PMAX behavior

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
