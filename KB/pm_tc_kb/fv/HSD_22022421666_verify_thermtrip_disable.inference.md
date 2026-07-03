# Deep Analysis: [Thermtrip] Verify Thermtrip Disable

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421666 |
| **Title** | [Thermtrip] Verify Thermtrip Disable |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | SoC Thermal Management |
| **Sub-Feature** | ThermTrip — disable mechanisms (fuse/TAP register) |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies the multiple methods to **disable THERMTRIP** and confirms the disable takes effect (THERMTRIP pin not asserted even when temperature conditions are met). ThermTrip is a hardware safety shutdown; NWP has the same fuse and TAP register disable mechanisms as DMR.

Tags: `Ready_for_testing`, `NGA_MAIN`, `plc.feature.p1`, `PMSS_NWP_READINESS_CHECK`

The test steps reference GNR register paths (noted as "Update with DMR registers - copied from GNR"). For NWP: adapt compute paths → `sv.socket0.cbb0/cbb1.*`; TAP DTS registers adapt similarly. Thermtrip disable logic is applicable on NWP silicon.

---

## Section B: NWP-Specific Test Procedure

### ThermTrip Disable Methods

| Method | NWP Register Path |
|--------|-------------------|
| TAP register disable | `sv.socket0.cbb[0-1].taps.<dts_reg>.dtsfusecfg.cattripdisable` |
| Fuse disable | `sv.socket0.imh0.fuses.punit.*thermtrip_enable = 0` |
| Software override | Pcode MSR or Punit register |

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Disable THERMTRIP via method (a): TAP register | `sv.socket0.cbb0.taps.<dts_reg>.dtsfusecfg.cattripdisable.write(1)` |
| 2 | OR Disable THERMTRIP via method (b): fuse override | Fuse field at `sv.socket0.imh0.fuses.punit.*` |
| 3 | Run thermtrip PMx test | `python runPmx.py -x nwp.xml -p therm_trip -tM 30 -M 6` |
| 4 | Inject thermtrip condition | Simics or signal injection (platform-specific) |
| 5 | Verify THERMTRIP pin NOT asserted (disable effective) | `ipc.power_status()` remains True; system remains alive |
| 6 | Re-enable THERMTRIP and verify normal operation | Restore register; repeat thermtrip → pin asserts |
| 7 | Verify ALL disable methods independently | Repeat steps 1–6 for each method |

### NWP Adaptations
- `runPmx.py -x nwp.xml` (not `dmr.xml`)
- 2 CBBs: validate disable on `cbb0` and `cbb1`
- Single `imh0`: fuse path `sv.socket0.imh0.fuses.punit.*`
- Implementation in `ThermTrip.py` (frameworks.validation.pythonsv.projects.diamondrapids)

### Pass Criteria
- All disable methods prevent THERMTRIP pin assertion
- `ipc.power_status()` returns True (system alive) when THERMTRIP disabled
- Re-enabling THERMTRIP restores normal thermtrip behavior

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; adapt register paths to 2 CBBs + single iMH**

1. `python runPmx.py -x nwp.xml -p therm_trip -tM 30 -M 6`
2. NWP: `cbb0`, `cbb1` TAP DTS registers; `imh0` fuse paths
3. Leverage existing `ThermTrip.py` NWP-adapted implementation

**Priority**: High — `plc.feature.p1`; ThermTrip disable is critical safety validation
