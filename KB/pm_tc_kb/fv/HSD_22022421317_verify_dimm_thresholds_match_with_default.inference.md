# HSD 22022421317: [MR4] Verify DIMM Thresholds match with default values programed by BIOS

| Field | Value |
|-------|-------|
| **HSD ID** | [22022421317](https://hsdes.intel.com/appstore/article/#/22022421317) |
| **Segment** | FV |
| **Feature** | Memory Thermal Management |
| **Sub-Feature** | MR4-based CLTT |
| **Environment** | silicon, virtual_platform |
| **Status** | open |
| **Owner** | jinwengo |
| **Command** | `runPmx.py -x dmr.xml -p mt_basic_checks -tM 60 --retry_count 2` |
| **KB Article** | [KB/pm_features/memory_thermal/mr4.md](KB/pm_features/memory_thermal/mr4.md) |

### Version History

| Version | Date | Changes | Trigger |
|---------|------|---------|---------|
| v1 | 2026-05-29 | LLM-driven enrichment with full 9-tab structure | `enrich 22022421317` |

---

## Test Case

### Intent

Verify that BIOS correctly programs MC registers controlling DIMM thermal throttle thresholds (low/mid/high).
These thresholds determine when MC applies bandwidth throttling based on MR4-reported DRAM temperatures.

**MR4-based CLTT** uses per-DRAM die temperature sensors via JEDEC DDR5 Mode Register 4. MC reads MR4
periodically (~128 ms), and applies throttle/refresh actions when temp exceeds programmed thresholds.

### Pre-Conditions

1. Boot SVOS with MR4 CLTT enabled (`B2P WRITE_PCU_MISC_CONFIG[MR4_CLTT_ENABLE]`)
2. BIOS programs default threshold values in `mr4_temp_thresh[0:1]` registers
3. PythonSV environment available
4. Memory populated (DDR5 DIMMs with MR4 support)

### Test Steps

| Step | Action | Interface | Expected |
|------|--------|-----------|----------|
| 1 | Boot system with MR4 CLTT enabled | BIOS | System boots |
| 2 | Read `mr4_temp_2xrefresh_threshold` | CSR | Value = 0x3 (default) |
| 3 | Read `mr4_temp_low_maxthreshold` | CSR | Value = 0x3 (default) |
| 4 | Read `mr4_temp_mid_maxthreshold` | CSR | Value = 0x4 (default) |
| 5 | Read `mr4_temp_high_maxthreshold` | CSR | Value = 0x5 (default) |
| 6 | Run `mt_basic_checks.py` | PythonSV | All threshold checks pass |

### Pass/Fail Criteria

**PASS:**
- All `mr4_temp_thresh[0:1]` fields match BIOS-programmed default values
- `mt_basic_checks.py` completes without assertion failures
- Threshold values: 2xRefresh=0x3, Low=0x3, Mid=0x4, High=0x5

**FAIL:**
- Any threshold register mismatches expected default
- Script reports threshold verification failure

---

## Section A: NWP Architecture Delta

**Disposition: Revalidate (update config)**

MR4-based CLTT is **supported and carried from DMR** to NWP. The MC thermal architecture is identical.
The test is applicable but requires config file update (`dmr.xml` -> `nwp.xml`).

### DMR to NWP Delta Analysis

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| MR4 CLTT support | Yes | **Yes** (carried) | Test applicable |
| IMH topology | 2× IMH (IMH0/IMH1) | **1× NIO** | Single IMH host |
| MC channels | 8 per IMH | 8 (NWP SP) / 16 (NWP AP) | Same per-channel logic |
| MR4 polling period | ~128 ms | ~128 ms | Identical |
| Threshold registers | `mr4_temp_thresh[0:1]` | `mr4_temp_thresh[0:1]` | Same CSRs |
| Default values | 2xRef=3, Low=3, Mid=4, High=5 | Same | Same defaults |
| HPM DIMM_TEMP | Multi-die distribution | N/A (single die) | Simplifies |

### Rationale for Revalidate

1. MR4 CLTT architecture identical — threshold registers and defaults unchanged
2. Config file path must change: `dmr.xml` -> `nwp.xml`
3. Single NIO topology simplifies HPM distribution (no inter-IMH messaging)
4. All JEDEC DDR5 MR4 semantics preserved

---

## Section B: Interactions

### Swimlane Data

| Step | Actor | Action | Interface |
|------|-------|--------|-----------|
| 1 | BIOS | Enable MR4 CLTT mode | B2P Mailbox |
| 2 | BIOS | Program threshold defaults | MC CSR |
| 3 | BIOS | Disable TSOD polling | MC CSR |
| 4 | MC | Periodic MR4 read (~128 ms) | DDR Mainband |
| 5 | MC | Populate mr4temp_0/1 | Internal |
| 6 | Primecode | Read MR4 telemetry (1 ms) | GPSB |
| 7 | Primecode | Convert JEDEC to Celsius | Internal |
| 8 | Primecode | Write dimm_tsod_temp | GPSB |
| 9 | Test | Read mr4_temp_thresh | CSR |
| 10 | Test | Verify vs defaults | Assertion |

### Sequence Data

| # | From | To | Message | Interface |
|---|------|-----|---------|-----------|
| 1 | BIOS | B2P | WRITE_PCU_MISC_CONFIG[MR4_CLTT_ENABLE]=1 | Mailbox |
| 2 | BIOS | MC | Program mr4_temp_thresh defaults | CSR |
| 3 | MC | DRAM | MR4 Mode Register Read | DDR Mainband |
| 4 | DRAM | MC | Return MR4[2:0] (3-bit temp code) | DDR Mainband |
| 5 | MC | Primecode | mr4temp_0/1 telemetry | GPSB Read |
| 6 | Test | MC | Read mr4_temp_thresh | CSR |
| 7 | MC | Test | Return threshold values | CSR |

---

## Section C: Interface Coverage Assessment

| Interface | Covered | Notes |
|-----------|---------|-------|
| B2P MR4_CLTT_ENABLE | Indirect | BIOS enables; test assumes enabled |
| MC mr4_temp_thresh[0:1] | **Yes** | Primary test target |
| MC mr4temp_0/1 | No | Not read in this test |
| Primecode CLTT flow | Indirect | Threshold values used by CLTT |
| TPMI OPC_DIMM_TEMPS | No | Separate test coverage |
| HPM DIMM_TEMPERATURE | No | N/A for NWP (single die) |

---

## Section D: NWP Specification References

- **NWP PM MAS**: MR4-based CLTT carried from DMR
- **DMR DDR5/MCR HAS**: MR4-based CLTT section — threshold registers
- **JEDEC DDR5 spec**: MR4 temperature encoding (3-bit codes)
- **KB Article**: [mr4.md](KB/pm_features/memory_thermal/mr4.md)
- **Primecode**: `src/flow/cltt/` — threshold usage

### Key Registers

| Register | Field | Default | Description |
|----------|-------|---------|-------------|
| mr4_temp_thresh[0:1] | mr4_temp_2xrefresh_threshold | 0x3 | 2× DRAM refresh trigger |
| mr4_temp_thresh[0:1] | mr4_temp_low_maxthreshold | 0x3 | THRT_MID trigger |
| mr4_temp_thresh[0:1] | mr4_temp_high_maxthreshold | 0x4 | THRT_HIGH trigger |
| mr4_temp_thresh[0:1] | mr4_temp_high_maxthreshold | 0x5 | THRT_CRIT trigger |

---

## Section E: NWP Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Config file mismatch | High | Low | Update `dmr.xml` to `nwp.xml` |
| Threshold defaults differ | Low | Medium | Confirm with NWP BIOS team |
| Register path change | Low | Medium | Verify CSR paths on NWP |
| Single-die topology | N/A | N/A | Simplifies — no inter-IMH HPM |

---

## Section F: Recommendations

1. **Update config**: Change `runPmx.py -x dmr.xml` to `-x nwp.xml`
2. **Verify CSR paths**: Confirm `mr4_temp_thresh[0:1]` path exists on NWP
3. **Confirm defaults**: Verify threshold defaults with NWP BIOS spec
4. **Keep test logic**: Threshold verification logic unchanged
5. **Priority**: High — `plc.feature.p1`, bring-up prerequisite for memory thermal

### NWP Adapted Command

```bash
python runPmx.py -x nwp.xml -p mt_basic_checks -tM 60 --retry_count 2
```

---

## User Notes

> Instructions for LLM: Read all notes chronologically. Apply corrections/clarifications
> to relevant sections. Do not modify notes — append new entries only.

*(No user notes yet — add feedback to refine this analysis)*
