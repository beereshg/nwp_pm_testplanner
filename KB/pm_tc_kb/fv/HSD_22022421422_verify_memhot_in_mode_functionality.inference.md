# Deep Analysis: [Memhot] Verify Memhot_In Mode Functionality (TSOD)

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421422 |
| **Title** | [Memhot] Verify Memhot_In mode functionality |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Memory Thermal Management |
| **Sub-Feature** | Memhot_In with TSOD-based CLTT — MEMHOT_IN GPIO asserted → all MCs throttle |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

Same MEMHOT_IN mechanism as TC 22022421411, but uses **TSOD (Temperature Sensor On DIMM)** instead of MR4. TSOD is read via I2C SMBus. MEMHOT_IN propagation through Punit to all MCs is the same.

Tags: `DMR_PO`, `NGA_MAIN`, `plc.ti_gate.b0`, `plc.feature.p1`, `PMSS_NWP_READINESS_CHECK`.

---

## Section B: NWP-Specific Test Procedure

### Adapted Command (NWP)
```bash
python runPmx.py -x nwp.xml -p memhot_tsod -tM 60 -M 5 --retry_count 2
```

### Adapted Steps (Same as MR4 variant, but TSOD source)

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Run `memhot_tsod` PMx plugin | `python runPmx.py -x nwp.xml -p memhot_tsod -tM 60 -M 5 --retry_count 2` |
| 2 | Set `unidir_memhot_in_en = 1` | Enable MEMHOT_IN sense |
| 3 | Assert MEMHOT_IN pin | External pin or simulated |
| 4 | Verify all MCs throttle | TSOD mode: all MCs throttle on MEMHOT_IN |
| 5 | De-assert MEMHOT_IN | Throttle clears |

### TSOD vs MR4 Source
| Feature | MR4 (TC 22022421411) | TSOD (this TC) |
|---------|---------------------|-----------------|
| Temp source | DRAM MR4 register | SMBus TSOD sensor |
| MEMHOT_IN mechanism | Same | Same |
| MEMHOT_OUT mechanism | Same | Same |

### Pass Criteria
- Same as MR4 variant: MEMHOT_IN → all MC throttle
- TSOD-based temp reading provides the thermal trigger
- Throttle clears on de-assertion

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; `memhot_tsod` PMx plugin; MEMHOT_IN mechanism identical to MR4 variant**

**Priority**: High — `NGA_MAIN`, `plc.feature.p1`; TSOD-based CLTT is the older/complementary mechanism to MR4/PECI
