# Deep Analysis: [IMH DTS & Telemetry] Verify MIO DTS Functionality

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421506 |
| **Title** | [IMH DTS & Telemetry] Verify MIO DTS Functionality |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | SoC Thermal Management |
| **Sub-Feature** | DTS — MIO (Management IO / UIO controller) thermal sensor via MIO_EW Resource Controller |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies **MIO DTS** functionality. From test step IP table:

| IP Stack | No. of DTS | IMH RS location | DTS location | Comment |
|----------|-----------|-----------------|--------------|---------|
| MIO | 3 | inside controller | inside controller misc block | One DTS and one or two RS within UIO stack |

Flow:
1. Read DTS temperature in MIO IP
2. Read temperature in corresponding Resource Controller — **MIO_EW**
3. Read temperature in PUNIT telemetry
4. Compare all — should match

Tags: `DMR_PO`, `plc.feature.p1`, `PMSS_NWP_READINESS_CHECK`

NWP MIO (Management IO, also UIO controller) is in the iMH die. MIO_EW is the RC. 3 DTS instances in the MIO stack.

---

## Section B: NWP-Specific Test Procedure

### MIO DTS Chain (NWP)

| Measurement | NWP Path |
|-------------|----------|
| MIO DTS direct | `sv.socket0.imh0.<mio_ctrl>.<dts_reg>.temperature` |
| MIO_EW Resource Controller | `sv.socket0.imh0.mio_ew.<rc_telem_reg>` |
| PUNIT telemetry | `sv.socket0.imh0.punit.<mio_telem_reg>` |

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Run dts_telemetry PMx | `python runPmx.py -x nwp.xml -p dts_telemetry -tM 60 --retry_count 2` |
| 2 | Read MIO DTS (all 3 instances) | `sv.socket0.imh0.<mio_misc>.<dts_N>.temperature.read()` for N in [0,1,2] |
| 3 | Read MIO_EW RC temperature | `sv.socket0.imh0.mio_ew.<telem_reg>.read()` |
| 4 | Read PUNIT telemetry | `sv.socket0.imh0.punit.<mio_telem_reg>.read()` |
| 5 | Compare all — DTS ≈ MIO_EW RC ≈ PUNIT telem | All 3 DTS instances checked |
| 6 | Stress MIO (management traffic) | Verify telemetry tracks DTS |

### NWP Notes
- MIO is in iMH die (`imh0`) — 3 DTS + 1 or 2 RS within UIO stack
- MIO_EW is the dedicated RC for MIO thermal path
- Single `imh0` — all MIO DTS in `sv.socket0.imh0.*`

### Pass Criteria
- All 3 MIO DTS instances, MIO_EW RC, and PUNIT telemetry agree
- Telemetry updates under MIO activity
- 3 DTS instances each functional and distinguishable

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; MIO DTS (3 instances) in imh0; MIO_EW RC path**

1. `python runPmx.py -x nwp.xml -p dts_telemetry -tM 60 --retry_count 2`
2. NWP: MIO DTS in `sv.socket0.imh0.*`; MIO_EW RC; 3 DTS instances
3. Verify 3-level chain: MIO DTS (×3) → MIO_EW RC → PUNIT telemetry

**Priority**: Medium — `plc.feature.p1`; MIO DTS monitors management IO controller thermal — important for platform management link thermal integrity
