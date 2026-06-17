# Deep Analysis: [Memhot] Verify Memhot_Out Mode Functionality (TSOD)

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421423 |
| **Title** | [Memhot] Verify Memhot_Out mode functionality |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Memory Thermal Management |
| **Sub-Feature** | Memhot_Out with TSOD-based CLTT — MC drives MEMHOT_OUT when TSOD/MR4 temp crosses threshold |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

Same MEMHOT_OUT mechanism as TC 22022421412 (MR4), but using **TSOD** as temperature source. MC compares TSOD temp code to threshold and drives MEMHOT_OUT pin.

Tags: `DMR_PO`, `plc.ti_gate.b0`, `plc.feature.p1`, `PMSS_NWP_READINESS_CHECK`.

---

## Section B: NWP-Specific Test Procedure

### Adapted Command (NWP)
```bash
python runPmx.py -x nwp.xml -p memhot_tsod -tM 60 -M 5 --retry_count 2
```

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Run `memhot_tsod` PMx plugin | Command above |
| 2 | Configure MEMHOT output threshold | `dimm_temp_ev_ctrl.temp_memhotout_sel` |
| 3 | Configure `dimm_temp_thresh[1:0]` | Low/mid/high for TSOD temp |
| 4 | Warm DIMM above threshold | TSOD reading crosses threshold |
| 5 | Verify MC drives MEMHOT_OUT | `ip_temp_memhotout` = 1 |
| 6 | Cool DIMM | MEMHOT_OUT de-asserts |
| 7 | Verify MEMTRIP at memtrip threshold | `ip_temp_memtrip` = 1 |

### Pass Criteria
- MC drives MEMHOT_OUT when TSOD temp ≥ programmed threshold
- MEMHOT_OUT de-asserts when TSOD temp drops below threshold
- MEMTRIP asserts at memtrip threshold

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; `memhot_tsod` PMx plugin; MEMHOT_OUT mechanism same as MR4 variant**

**Priority**: Medium — `plc.feature.p1`; TSOD-based MEMHOT_OUT provides platform notification of memory thermal events
