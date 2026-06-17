# Deep Analysis: SVID Basic Commands Functionality Verification

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421917 |
| **Title** | SVID Basic commands functionality Verification |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | SVID |
| **Sub-Feature** | SVID basic commands (GetVID, SetVID, SetPS) via PMx plugin |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

SVID (Serial VID interface) basic commands are functional on NWP. The PMx SVID plugin validates GetVID, SetVID, SetPS, and SVID command response correctness. Template content incomplete in source HSD — steps field contains only the unfilled mandatory section template.

Tags: `DMR_PO`, `plc.feature.p2`, `NGA_MAIN`, `PMSS_NWP_READINESS_CHECK`.

---

## Section B: NWP-Specific Test Procedure

### NWP Command
```bash
# DMR → NWP: dmr.xml → nwp.xml
python runPmx.py -x nwp.xml -p svid -p core_power -tM 60 -M 5
```

### Adapted Steps

| Step | Action | Details |
|------|--------|---------|
| 1 | Boot to SVOS | Normal platform boot |
| 2 | Run SVID PMx plugin | `runPmx.py -x nwp.xml -p svid -p core_power -tM 60 -M 5` |
| 3 | Verify GetVID commands succeed | SVID GetVID returns valid voltage codes |
| 4 | Verify SetVID commands succeed | Voltage transitions without MCA |
| 5 | Verify SetPS (power state) commands | PM state transitions via SVID |
| 6 | Check no SVID command errors | No SVID Bus Error (SBE) or SVID timeout |

### Pass Criteria
- All SVID basic commands execute without errors
- Voltage transitions complete in-spec timing
- `runPmx.py` SVID plugin passes all assertions

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; SVID functional on NWP; source TC has empty steps template — rely on PMx SVID plugin assertions**

**Priority**: High — `PMSS_NWP_READINESS_CHECK`; SVID basic functionality is a P0 bring-up gate
