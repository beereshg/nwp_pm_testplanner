# Deep Analysis: [MR4] Verify DIMM Temp Is Updated by MC

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421328 |
| **Title** | [MR4] Verify DIMM temp is updated by the MC |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Memory Thermal Management |
| **Sub-Feature** | MR4 temperature reading — verify MC reads and updates MR4 temperature per rank |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies the MC reads MR4 temperature registers from DRAM and updates the `mr4_temp_rank[0:3]` fields. Physical thermal head warming is used to validate temperature tracking. Tags: `DMR_PO`, `NGA_MAIN`, `plc.ti_gate.b0`, `plc.feature.p1`, `PMSS_NWP_READINESS_CHECK`.

---

## Section B: NWP-Specific Test Procedure

### MR4 Temperature Rank Registers

| CSR Field | Description |
|-----------|-------------|
| `mr4_temp_rank0 [2:0]` | Max MR4 temp reading from rank 0 |
| `mr4_temp_rank1 [5:3]` | Max MR4 temp reading from rank 1 |
| `mr4_temp_rank2 [8:6]` | Max MR4 temp reading from rank 2 |
| `mr4_temp_rank3 [11:9]` | Max MR4 temp reading from rank 3 |

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Read MR4 temperature from MC registers | `mem_thermals_debug.py` |
| 2 | Apply thermal head to warm DIMM | Physical thermal test equipment |
| 3 | Read MR4 temperature registers again | `mr4_temp_rank[0:3]` updated |
| 4 | Verify temperature matches thermal head setting | Temperature code matches programmed value |

### NWP Command
```bash
mem_thermals_debug.py
```

### Pass Criteria
- `mr4_temp_rank[0:3]` updates as DIMM temperature changes
- Temperature reading tracks thermal head temperature within tolerance
- MC polls MR4 at expected rate

---

## Section F: Recommendation

**Recommendation: ADOPT — `mem_thermals_debug.py` script needs NWP package adaptation; MR4 temperature tracking same mechanism**

**Priority**: High — `NGA_MAIN`, `plc.feature.p1`; MR4 temperature update is the source input for MR4-based CLTT — must work correctly
