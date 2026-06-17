# Deep Analysis: [PECI] Verify DIMM Temp in MC Is Updated by TPMI

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421347 |
| **Title** | [PECI] Verify DIMM temp in MC is being updated by TPMI |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Memory Thermal Management |
| **Sub-Feature** | PECI-based CLTT — BMC writes DIMM temp via TPMI into MC registers |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

In PECI-based CLTT, the **BMC controls DIMM temperatures** via TPMI. The BMC writes temperature values into TPMI, which are then used by the MC for throttle decisions. Test verifies the MC correctly reads and reflects these BMC-provided values.

Tags: `DMR_PO`, `NGA_MAIN`, `plc.ti_gate.b0`, `plc.feature.p1`, `PMSS_NWP_READINESS_CHECK`.

---

## Section B: NWP-Specific Test Procedure

### PECI DIMM Temperature Registers

| CSR Field | Description |
|-----------|-------------|
| `dimm_temp_snapshot_0.dimm_temp_sch0 [7:0]` | DIMM0 Sub-channel 0 temp |
| `dimm_temp_snapshot_0.dimm_temp_sch1 [15:8]` | DIMM0 Sub-channel 1 temp |
| `dimm_temp_snapshot_1.dimm_temp_sch0 [7:0]` | DIMM1 Sub-channel 0 temp |
| `dimm_temp_snapshot_1.dimm_temp_sch1 [15:8]` | DIMM1 Sub-channel 1 temp |

### NWP Register Paths
```python
# NWP: PECI-based CLTT DIMM temp registers (via IMH0 TPMI)
# sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.dimm_temp_snapshot_0
# sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.dimm_temp_snapshot_1
```

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Run `mem_thermals_debug.py` | Read all DIMM temp snapshots |
| 2 | Read current DIMM temperature from TPMI | Baseline value from BMC |
| 3 | BMC writes different temperature for each DIMM | Via TPMI write |
| 4 | Read DIMM temperature again | MC should show updated value |
| 5 | Verify updated value matches BMC write | Per DIMM, per sub-channel |

### NWP Notes
- `sv.sockets.imhs.*` → `sv.socket0.imh0.*` (single iMH)
- BMC PECI/TPMI interface same architecture on NWP
- `NGA_MAIN`: automate via NGA

### Pass Criteria
- Each DIMM temperature snapshot updates when BMC writes via TPMI
- Per sub-channel values independently tracked
- Update latency within expected polling interval

---

## Section F: Recommendation

**Recommendation: ADOPT — `sv.sockets.imhs.*` → `sv.socket0.imh0.*`; `mem_thermals_debug.py` NWP package; PECI TPMI interface same**

**Priority**: High — `NGA_MAIN`, `plc.feature.p1`; PECI-based CLTT is the primary memory thermal mechanism for data center deployments without thermal heads
