# Deep Analysis: [Memhot] Memhot Disables MR4-based

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421415 |
| **Title** | [Memhot] Memhot Disables MR4-based |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Memory Thermal Management |
| **Sub-Feature** | Memhot disable — verify MEMHOT sense/output can be disabled per config field |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies that MEMHOT can be optionally disabled at each threshold by zeroing the appropriate `mh_mainctl_cfg` fields. Disabling MEMHOT sense means MEMHOT_IN pin asserted will NOT cause MC throttle.

Tags: `plc.ti_gate.b0`, `plc.feature.p1`, `PMSS_NWP_READINESS_CHECK`.

---

## Section B: NWP-Specific Test Procedure

### Memhot Disable Fields (NWP)

```python
# NWP: disable all MEMHOT functions
mh_cfg = sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.mh_mainctl_cfg
mh_cfg.mh_sense_en.write(0)                         # Disable MEMHOT sense
mh_cfg.mh_output_en.write(0)                         # Disable MEMHOT output
mh_cfg.unidir_memhot_in_en.write(0)                  # Disable MEMHOT_IN propagation
mh_cfg.unidir_memhot0_to_memhot_out_en.write(0)      # Disable MEMHOT0 → output
mh_cfg.unidir_memhot1_to_memhot_out_en.write(0)      # Disable MEMHOT1 → output
```

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Run `mt_basic_checks` | `python runPmx.py -x nwp.xml -p mt_basic_checks -tM 60 --retry_count 2` |
| 2 | Disable all MEMHOT fields in `mh_mainctl_cfg` | Set all to 0 per NWP register path |
| 3 | Assert MEMHOT_IN pin (or inject) | Should NOT propagate to MC throttle |
| 4 | Verify no throttle occurs | MC bandwidth unchanged despite MEMHOT_IN |
| 5 | Warm DIMM above threshold | Should NOT trigger MEMHOT_OUT (output disabled) |
| 6 | Verify MEMHOT_OUT stays de-asserted | GPIO not driven |
| 7 | Re-enable MEMHOT | Restore defaults |

### Pass Criteria
- With `mh_sense_en = 0`: MEMHOT_IN assertion causes no MC throttle
- With `mh_output_en = 0`: MEMHOT_OUT not driven even when temp crossed threshold
- Re-enable restores full MEMHOT functionality

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; `sv.sockets.imhs.*` → `sv.socket0.imh0.*`; MEMHOT disable mechanism same on NWP**

**Priority**: Medium — `plc.feature.p1`; MEMHOT disable is needed for configurations where platform does not have MEMHOT GPIO wired
