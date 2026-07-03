# Deep Analysis: [Memhot] MR4 Verify Memhot_Out Mode Functionality

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421412 |
| **Title** | [Memhot] MR4 Verify Memhot_Out mode functionality (copy) |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Memory Thermal Management |
| **Sub-Feature** | Memhot_Out (MEMHOT_OUT GPIO) — MC asserts MEMHOT output when DIMM temp crosses threshold |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

The **MEMHOT_OUT** pin is driven by the MC when DIMM temperature crosses the threshold configured by `temp_memhotout_sel`. This propagates a thermal event to the platform BMC. Test uses MR4-based CLTT.

Tags: `DMR_PO`, `plc.ti_gate.b0`, `plc.feature.p1`, `PMSS_NWP_READINESS_CHECK`.

---

## Section B: NWP-Specific Test Procedure

### Memhot_Out Configuration

| Register | Fields | Description |
|----------|--------|-------------|
| `dimm_temp_ev_ctrl[1:0]` | `temp_memhotout_sel` | Selects threshold level that drives MEMHOT output |
| `dimm_temp_thresh[1:0]` | Low/mid/high | Threshold the MC compares to TSOD/MR4 temp |

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Run `runPmx.py` memhot_mr4 plugin | `python runPmx.py -x nwp.xml -p memhot_mr4 -tM 60 -M 5 --retry_count 2` |
| 2 | Configure MEMHOT output threshold | `dimm_temp_ev_ctrl.temp_memhotout_sel = low` |
| 3 | Warm DIMM above configured threshold (MR4 reading) | Physical thermal head |
| 4 | Verify MC asserts MEMHOT output pin | `ip_temp_memhotout` = 1 |
| 5 | Verify MEMHOT_OUT drives platform GPIO | Platform BMC sees MEMHOT assertion |
| 6 | Cool DIMM below threshold | MEMHOT_OUT de-asserts |
| 7 | Verify MEMTRIP output when temp crosses memtrip threshold | Additional verification |

### Pass Criteria
- MC asserts MEMHOT_OUT when MR4 temp crosses programmed threshold
- Platform GPIO reflects assertion
- MEMHOT de-asserts when temperature drops below threshold
- MEMTRIP asserts at memtrip threshold

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; `dimm_temp_ev_ctrl` and `dimm_temp_thresh` same architecture on NWP**

**Priority**: Medium — `plc.feature.p1`; MEMHOT_OUT drives BMC thermal response — must work correctly for platform thermal management
