# Deep Analysis: [Memtrip] PECI Based

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421439 |
| **Title** | [Memtrip] PECI based |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Memory Thermal Management |
| **Sub-Feature** | PECI-based MEMTRIP — MC asserts ip_temp_memtrip when PECI TPMI temp crosses memtrip threshold |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

Same MEMTRIP mechanism as TC 22022421434 (MR4) but using **PECI/TPMI** temperature source. BMC writes DIMM temp via TPMI; when it exceeds memtrip threshold, MC asserts MEMTRIP.

Tags: `DMR_PO`, `NGA_MAIN`, `plc.ti_gate.b0`, `plc.feature.p1`, `PMSS_NWP_READINESS_CHECK`.

---

## Section B: NWP-Specific Test Procedure

### Adapted Command (NWP)
```bash
python runPmx.py -x nwp.xml -p memtrip_peci -tM 60 -M 5 --retry_count 2
```

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Configure PECI CLTT mode | BIOS knob `thermalthrottlingsupport` = PECI |
| 2 | Configure Punit memtrip registers | `thermtrip_config_cfg` for memtrip routing |
| 3 | Run `memtrip_peci` PMx plugin | Command above |
| 4 | BMC writes DIMM temp above memtrip threshold via TPMI | Simulated high temp |
| 5 | Verify MC asserts `ip_temp_memtrip` | Punit sees MEMTRIP |
| 6 | Verify xxMEMTRIP GPIO asserts | Platform output |
| 7 | BMC writes temp below threshold | MEMTRIP de-asserts |

### PECI vs MR4 MEMTRIP

| Feature | MR4 (TC 22022421434) | PECI (this TC) |
|---------|---------------------|-----------------|
| Temp source | DRAM MR4 register | BMC via TPMI |
| Threshold register | `mr4_temp_thresh` memtrip field | `dimm_temp_thresh` memtrip field |
| Trigger mechanism | MC reads MR4 | MC reads TPMI-populated register |

### Pass Criteria
- PECI TPMI temp write above memtrip threshold → MC MEMTRIP assertion
- xxMEMTRIP GPIO asserts
- MEMTRIP clears when temp below threshold

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; PECI MEMTRIP mechanism same as MR4 variant; BMC TPMI interface same on NWP**

**Priority**: High — `NGA_MAIN`, `plc.feature.p1`; PECI MEMTRIP is the primary data center DIMM overtemp protection path (no thermal heads in production)
