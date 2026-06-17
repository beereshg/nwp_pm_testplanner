# Deep Analysis: [Memtrip] Disables Memtrip MR4-based

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421425 |
| **Title** | [Memtrip] Disables Memtrip MR4-based |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Memory Thermal Management |
| **Sub-Feature** | Memtrip disable — verify MEMTRIP can be optionally disabled via `thermtrip_config_cfg` |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies that **MEMTRIP can be disabled** by clearing the appropriate bits in Punit `thermtrip_config_cfg`:
- When disabled: crossing the memtrip temperature threshold should NOT trigger MEMTRIP/THERMTRIP

NWP Punit register: `sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.thermtrip_config_cfg`.

Tags: `plc.ti_gate.b0`, `plc.feature.p1`, `PMSS_NWP_READINESS_CHECK`.

---

## Section B: NWP-Specific Test Procedure

### Memtrip Disable Register (NWP)

```python
# NWP: disable MEMTRIP
therm_cfg = sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.thermtrip_config_cfg
# Disable memtrip (set relevant bits to 0)
therm_cfg.show()  # Check current state and field names
```

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Configure BIOS knob `MemTripReporting = Disabled` | Or clear via register |
| 2 | Run `mt_basic_checks.py` | `python runPmx.py -x nwp.xml -p mt_basic_checks -tM 60 --retry_count 2` |
| 3 | Set `thermtrip_config_cfg` memtrip bits = 0 | Disable memtrip reporting |
| 4 | Warm DIMM above memtrip threshold (MR4 mode) | Threshold crossed |
| 5 | Verify MEMTRIP NOT asserted | Despite threshold crossing, no MEMTRIP |
| 6 | Verify THERMTRIP NOT triggered | No platform-level action |
| 7 | Run `mem_thermals_debug.py` to confirm | `mem_thermals_debug.py -v` |

### Pass Criteria
- With MEMTRIP disabled: crossing memtrip threshold does NOT assert MEMTRIP pin
- System remains operational above memtrip threshold when feature disabled
- Re-enabling MEMTRIP restores normal behavior

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; `sv.sockets.imhs.*` → `sv.socket0.imh0.*`; `thermtrip_config_cfg` same on NWP**

**Priority**: Medium — `plc.feature.p1`; MEMTRIP disable is needed for testing scenarios requiring operation above normal thermal limits
