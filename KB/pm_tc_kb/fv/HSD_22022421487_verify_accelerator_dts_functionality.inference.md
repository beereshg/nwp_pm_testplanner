# Deep Analysis: [IMH DTS & Telemetry] Verify Accelerator DTS Functionality

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421487 |
| **Title** | [IMH DTS & Telemetry] Verify Accelerator DTS Functionality |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | SoC Thermal Management |
| **Sub-Feature** | DTS — Accelerator IP thermal sensor via CFCIO Resource Controller |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies **Accelerator DTS** functionality. From test step IP table:

| IP Stack | No. of DTS | IMH RS location | DTS location | Comment |
|----------|-----------|-----------------|--------------|---------|
| Accelerator | 1 | inside accelerator | inside accelerator misc block | One DTS and one RS within accelerator stack |

Flow:
1. Read DTS temperature in Accelerator IP
2. Read temperature in corresponding Resource Controller — **CFCIO**
3. Read temperature in PUNIT telemetry
4. Compare all — should match

Tags: `DMR_PO`, `plc.feature.p1`, `PMSS_NWP_READINESS_CHECK`

NWP has Accelerator IP (DSA/IAA/QAT type accelerators in iMH die). Adapt CFCIO RC path.

---

## Section B: NWP-Specific Test Procedure

### Accelerator DTS Chain (NWP)

| Measurement | NWP Path |
|-------------|----------|
| Accelerator DTS direct | `sv.socket0.imh0.<accel_dts_path>.temperature` |
| CFCIO Resource Controller | `sv.socket0.imh0.cfcio.<rc_telem_reg>` |
| PUNIT telemetry | `sv.socket0.imh0.punit.<accel_telem_reg>` |

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Run dts_telemetry PMx | `python runPmx.py -x nwp.xml -p dts_telemetry -tM 60 --retry_count 2` |
| 2 | Read Accelerator DTS temperature directly | `sv.socket0.imh0.<accel_misc>.dts.temperature.read()` |
| 3 | Read CFCIO RC temperature | `sv.socket0.imh0.cfcio.<telem_reg>.read()` |
| 4 | Read PUNIT telemetry | `sv.socket0.imh0.punit.<accel_telem>.read()` |
| 5 | Compare all three — should match | DTS ≈ CFCIO RC ≈ PUNIT telem |
| 6 | Stress accelerator (run accelerator workload) | Verify all three tracking together |

### NWP Notes
- NWP: single `imh0` — Accelerator IP in iMH die
- CFCIO is the RC for Accelerator thermal; also manages IO Fabric DTS
- 1 DTS instance in Accelerator stack (not multiple)

### Pass Criteria
- Accelerator DTS, CFCIO RC, and PUNIT telemetry agree on temperature
- All three update together under accelerator workload
- 1 DTS per Accelerator stack confirmed

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; Accelerator DTS in imh0; CFCIO RC path**

1. `python runPmx.py -x nwp.xml -p dts_telemetry -tM 60 --retry_count 2`
2. NWP: Accelerator DTS in `sv.socket0.imh0.*`
3. Validate 3-level chain: Accelerator DTS → CFCIO RC → PUNIT telemetry

**Priority**: Medium — `plc.feature.p1`; Accelerator DTS validates IO accelerator thermal monitoring path
