# Deep Analysis: [Memtrip] Memtrip to Thermtrip

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421437 |
| **Title** | [Memtrip] Memtrip to Thermtrip |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Memory Thermal Management |
| **Sub-Feature** | Memtrip_to_Thermtrip — enable MEMTRIP network to assert xxTHERMTRIP_N pin |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

When `thermtrip_config_cfg.memtrip0_to_xxTHERMTRIP_N_en` is set, a MEMTRIP event causes the xxTHERMTRIP_N GPIO to assert (platform shutdown). This test verifies this escalation path.

NWP register: `sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.thermtrip_config_cfg`.

Tags: `DMR_PO`, `NGA_MAIN`, `plc.ti_gate.b0`, `plc.feature.p1`, `PMSS_NWP_READINESS_CHECK`.

---

## Section B: NWP-Specific Test Procedure

### thermtrip_config_cfg Fields (NWP)

| Bit | Field | Description |
|-----|-------|-------------|
| 4 | `memtrip0_to_xxTHERMTRIP_N_en` | MEMTRIP network 0 → xxTHERMTRIP_N |
| 5 | `memtrip1_to_xxTHERMTRIP_N_en` | MEMTRIP network 1 → xxTHERMTRIP_N |
| 6 | TBD | Additional routing options |

### NWP Register Path
```python
# NWP: enable MEMTRIP → THERMTRIP escalation
therm_cfg = sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.thermtrip_config_cfg
therm_cfg.memtrip0_to_xxTHERMTRIP_N_en.write(1)  # Enable escalation
therm_cfg.show()
```

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Enable `memtrip0_to_xxTHERMTRIP_N_en = 1` | Via BIOS knob or register |
| 2 | Run `mem_thermals_debug.py` | Verify escalation config |
| 3 | Trigger MEMTRIP (MR4/PECI temp above memtrip threshold) | Warm DIMM above threshold |
| 4 | Verify MEMTRIP → xxTHERMTRIP_N asserted | Platform GPIO driven |
| 5 | Verify platform responds (shutdown or log) | BMC reacts to THERMTRIP |
| 6 | **Important**: This is a destructive test — system may shut down | Run with care; need recovery path |

### Pass Criteria
- `memtrip0_to_xxTHERMTRIP_N_en = 1`: MEMTRIP event causes THERMTRIP assertion
- Platform responds to THERMTRIP (power off or reset)
- `memtrip0_to_xxTHERMTRIP_N_en = 0`: MEMTRIP does NOT cause THERMTRIP

---

## Section F: Recommendation

**Recommendation: ADOPT — `sv.sockets.imhs.*` → `sv.socket0.imh0.*`; `thermtrip_config_cfg` same on NWP; ⚠️ THERMTRIP is destructive — run with recovery plan**

**Priority**: High — `NGA_MAIN`, `plc.feature.p1`; MEMTRIP→THERMTRIP escalation is the last line of defense against DIMM overtemperature damage
