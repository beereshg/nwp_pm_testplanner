# Deep Analysis: SVID Imon Telemetry Verification

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421924 |
| **Title** | SVID Imon telemetry Verification |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | SVID |
| **Sub-Feature** | SVID Imon (current monitor) telemetry accuracy — per-VR current readings |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

Verifies SVID Imon (current monitor) telemetry readings from each VR. Imon values should be accurate and within tolerance vs actual measured current. Template content incomplete in source HSD.

Tags: `DMR_PO`, `plc.feature.p2`, `PMSS_NWP_READINESS_CHECK`.

---

## Section B: NWP-Specific Test Procedure

### NWP Command
```bash
python runPmx.py -x nwp.xml -p svid -p core_power -tM 60 -M 5
```

### NWP Imon Register Paths
```python
# NWP: 2 CBBs + 1 IMH
for cbb_idx in range(2):
    imon = sv.socket0.cbb[cbb_idx].base.pcudata.imon_reading
    print(f"CBB{cbb_idx} Imon: {imon}")

imh0_imon = sv.socket0.imh0.pcudata.imon_reading
print(f"IMH0 Imon: {imh0_imon}")
```

### Pass Criteria
- Imon readings non-zero under active workload
- Readings within ±20% of measured/expected values
- PMx SVID plugin Imon assertions pass

---

## Section F: Recommendation

**Recommendation: ADOPT — `nwp.xml`; NWP 2 CBBs + 1 IMH Imon paths; template incomplete — rely on PMx assertions for tolerance checks**

**Priority**: High — `PMSS_NWP_READINESS_CHECK`; Imon accuracy is required for RAPL power accounting and IccMax enforcement
