# Deep Analysis: [Thermtrip] Verify Thermtrip Shuts Down All FIVRs and MBVRs

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421671 |
| **Title** | [Thermtrip] Verify Thermtrip shuts down all FIVRs and MBVRs |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | SoC Thermal Management |
| **Sub-Feature** | ThermTrip — FIVR and MBVR power rail shutdown on thermtrip |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies that when a **THERMTRIP** event occurs, all FIVRs and MBVRs in the SoC are properly shut down (power removed from all voltage domains). This is a fundamental hardware safety requirement. NWP has the same FIVR/MBVR architecture mapped to 2 CBBs and single iMH.

Tags: `DMR_PO`, `plc.feature.p1`, `PMSS_NWP_READINESS_CHECK`

Implementation: uses `ipc.power_status() is True` as the primary health indicator. Steps reference GNR but note "Update with DMR Registers"; same principle applies to NWP with adapted register paths.

---

## Section B: NWP-Specific Test Procedure

### FIVR/MBVR Domains on NWP

| Domain | Count | Notes |
|--------|-------|-------|
| CBB FIVRs | 2 CBBs (cbb0, cbb1) | Per-CBB FIVR domains |
| iMH MBVRs | 1 iMH (imh0) | External MBVR stack |
| IO/Fabric FIVRs | Platform-specific | NWP IO die |

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Configure thermtrip enable fuses | `hwrs_eb_fuse_dword0_thermtrip_enable=0x1` via NWP fuse paths |
| 2 | Enable DTS on all dies | `sv.socket0.cbb[0-1].<dts_path>.dtsenable=0x1` |
| 3 | Run thermtrip PMx | `python runPmx.py -x nwp.xml -p therm_trip -tM 30 -M 6` |
| 4 | Trigger THERMTRIP condition | Platform thermtrip injection |
| 5 | Verify `ipc.power_status()` is False → system shutdown | Confirms all FIVRs/MBVRs powered off |
| 6 | Power cycle and verify clean recovery | Platform brings up all rails normally |

### NWP Key Notes
- `ipc.power_status()` is the current implementation approach (replaces register-level FIVR status polling)
- NWP: 2 CBBs; single iMH with external MBVR stack
- Thermtrip event → PUnit signals all CBBs and iMH → FIVRs/MBVRs shut down
- `runPmx.py -x nwp.xml` (not `dmr.xml`)

### Pass Criteria
- `ipc.power_status()` returns False immediately after THERMTRIP
- All voltage domains (FIVRs + MBVRs) confirm shutdown
- Platform recovers cleanly on power cycle

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; NWP 2 CBBs; `ipc.power_status()` primary check**

1. `python runPmx.py -x nwp.xml -p therm_trip -tM 30 -M 6`
2. NWP: validate shutdown of cbb0, cbb1 FIVRs and imh0 MBVR stack
3. Use `ipc.power_status() is False` as primary shutdown confirmation

**Priority**: High — `plc.feature.p1`; critical safety path — THERMTRIP must kill all rails
