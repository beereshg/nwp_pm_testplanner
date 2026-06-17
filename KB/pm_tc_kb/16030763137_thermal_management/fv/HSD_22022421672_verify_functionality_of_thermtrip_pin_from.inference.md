# Deep Analysis: [Thermtrip] Verify Functionality of Thermtrip Pin from Various Sources

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421672 |
| **Title** | [Thermtrip] Verify functionality of thermtrip pin from various sources |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | SoC Thermal Management |
| **Sub-Feature** | ThermTrip pin — multiple trigger sources (DTS, CATTRIP, external) |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies that the **THERMTRIP pin** can be triggered from **multiple independent sources** (compute die DTS overtemp, CGU DTS, external thermtrip input, etc.) and that each source correctly asserts the THERMTRIP pin. NWP has the same source architecture (DTS per die, CGU, external).

Tags: `Ready_for_testing`, `plc.feature.p1`, `PMSS_NWP_READINESS_CHECK`

Fuse requirements map directly to NWP fuse hierarchy: `sv.socket0.imh0.fuses.punit.*` for fuse fields.

---

## Section B: NWP-Specific Test Procedure

### Thermtrip Sources on NWP

| Source | NWP Enable Fuse | Description |
|--------|-----------------|-------------|
| Compute die DTS CATTRIP | `hwrs_eb_fuse_dword0_cattrip_enable=0x1` | CBB core overheat |
| Compute die DTS THERMTRIP | `hwrs_eb_fuse_dword0_thermtrip_enable=0x1` | CBB primary thermtrip |
| YY-THERMTRIP | `hwrs_eb_fuse_dword0_yythermtrip_enable` | Secondary source |
| CGU DTS | `dts_cgu.dtsenable=0x1`, `dtsenableovrd=0x1` | CGU thermal monitoring |

### NWP Fuse Paths
```python
# Enable fuses (NWP paths)
sv.socket0.imh0.fuses.punit.hwrs_eb_fuse_dword0_cattrip_enable.write(0x1)
sv.socket0.imh0.fuses.punit.hwrs_eb_fuse_dword0_thermtrip_enable.write(0x1)

# Enable DTS for all CBBs
for cbb_idx in range(2):
    sv.socket0.getbypath(f"cbb{cbb_idx}.<dts_path>.dtsenable").write(0x1)
    sv.socket0.getbypath(f"cbb{cbb_idx}.<dts_path>.dtsenableovrd").write(0x1)
```

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Set thermtrip enable fuses for all sources to test | Per-source fuse at `imh0.fuses.punit.*` |
| 2 | Enable DTS on all compute dies and CGU | `dtsenable=1`, `dtsenableovrd=1` |
| 3 | Run thermtrip PMx | `python runPmx.py -x nwp.xml -p therm_trip -tM 30 -M 6` |
| 4 | For each source: inject thermtrip condition | Source-specific injection |
| 5 | Verify THERMTRIP pin asserts | `ipc.power_status()` → False |
| 6 | Power cycle; repeat for next source | Cover all sources |

### NWP: 2 CBBs
- Verify thermtrip from cbb0 DTS asserts pin
- Verify thermtrip from cbb1 DTS asserts pin
- Verify thermtrip from CGU/IO die DTS asserts pin

### Pass Criteria
- Each independent source (compute DTS, CGU, external) can independently assert THERMTRIP pin
- `ipc.power_status()` False confirms assertion
- All sources verified; no false-negative paths

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; adapt fuse paths to NWP; test both CBBs (cbb0, cbb1)**

1. `python runPmx.py -x nwp.xml -p therm_trip -tM 30 -M 6`
2. NWP: `sv.socket0.imh0.fuses.punit.*` for thermtrip enable fuses
3. 2 CBBs: cover both compute dies as sources
4. CGU and external sources applicable on NWP

**Priority**: High — `plc.feature.p1`; multi-source thermtrip coverage is critical safety validation
