# Deep Analysis: [Memhot] MR4 Verify Memhot_In Mode Functionality

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421411 |
| **Title** | [Memhot] MR4 Verify Memhot_In mode functionality |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Memory Thermal Management |
| **Sub-Feature** | Memhot_In (MEMHOT_IN GPIO) — external thermal event throttles all MCs via Punit |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

When the platform asserts the **xxMEMHOT_IN** pin (external thermal event from platform), it propagates through the Punit to all MCs causing bandwidth throttling. This test verifies MEMHOT_IN mode with MR4-based CLTT.

NWP Punit register: `sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.mh_mainctl_cfg` (from `sv.sockets.imhs.uncore.punit.ptpcfsms.ptpcfsms.mh_mainctl_cfg`).

Tags: `DMR_PO`, `NGA_MAIN`, `plc.ti_gate.b0`, `plc.feature.p1`, `PMSS_NWP_READINESS_CHECK`.

---

## Section B: NWP-Specific Test Procedure

### Memhot_In Configuration

| Register | Field | Description |
|----------|-------|-------------|
| `mh_mainctl_cfg` | `mh_sense_en` | Enable MEMHOT sense input |
| `mh_mainctl_cfg` | `unidir_memhot_in_en` | Enable unidirectional MEMHOT_IN propagation |
| `mh_mainctl_cfg` | `unidir_memhot_in_to_memhot0_en` | Propagate MEMHOT_IN to MH network 0 |

### NWP Register Path
```python
# NWP Memhot control register (single imh0)
mh_cfg = sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.mh_mainctl_cfg
mh_cfg.show()  # Show all Memhot config fields
```

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Run `runPmx.py` memhot_mr4 plugin | `python runPmx.py -x nwp.xml -p memhot_mr4 -tM 60 -M 5 --retry_count 2` |
| 2 | Set `mh_mainctl_cfg.unidir_memhot_in_en = 1` | Enable MEMHOT_IN sense |
| 3 | Assert MEMHOT_IN (external pin or inject) | Simulated MEMHOT_IN assertion |
| 4 | Verify throttle level applied to all MCs | `memhot_ext_thrt` configured bandwidth |
| 5 | Verify Punit sees MEMHOT_IN | `mh_mainctl_cfg.mh_sense_en` active |
| 6 | De-assert MEMHOT_IN | Throttle should clear |

### Pass Criteria
- MEMHOT_IN → Punit → all MCs throttled at configured level
- `mh_mainctl_cfg.mh_sense_en` = 1 required for propagation
- Throttle clears when MEMHOT_IN de-asserted

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; `sv.sockets.imhs.*` → `sv.socket0.imh0.*`; Memhot mechanism same on NWP**

**Priority**: High — `NGA_MAIN`, `plc.feature.p1`; MEMHOT_IN propagation is critical for platform-level thermal emergency response
