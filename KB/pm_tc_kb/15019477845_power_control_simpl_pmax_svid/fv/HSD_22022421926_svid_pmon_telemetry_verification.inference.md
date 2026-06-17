# Deep Analysis: SVID Pmon Telemetry Verification

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421926 |
| **Title** | SVID Pmon Telemetry Verification |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | SVID |
| **Sub-Feature** | SVID Pmon (power monitor) telemetry accuracy — per-VR power readings |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

Verifies SVID Pmon (power monitor) telemetry from each VR. Pmon combines Vmon and Imon to compute per-VR power (P = V × I). Template content incomplete in source HSD.

Tags: `DMR_PO`, `plc.feature.p2`, `PMSS_NWP_READINESS_CHECK`.

---

## Section B: NWP-Specific Test Procedure

### NWP Command
```bash
python runPmx.py -x nwp.xml -p svid -p core_power -tM 60 -M 5
```

### NWP Pmon Register Paths
```python
# NWP: 2 CBBs + 1 IMH
for cbb_idx in range(2):
    pmon = sv.socket0.cbb[cbb_idx].base.pcudata.pmon_reading
    print(f"CBB{cbb_idx} Pmon: {pmon}")

imh0_pmon = sv.socket0.imh0.pcudata.pmon_reading
print(f"IMH0 Pmon: {imh0_pmon}")
```

### Pass Criteria
- Pmon readings non-zero under active workload
- Pmon consistent with known TDP/power estimates
- PMx SVID plugin Pmon assertions pass

---

## Section F: Recommendation

**Recommendation: ADOPT — `nwp.xml`; NWP 2 CBBs + 1 IMH Pmon paths; template incomplete — rely on PMx assertions; Pmon used for RAPL energy accounting accuracy**

**Priority**: High — `PMSS_NWP_READINESS_CHECK`; Pmon accuracy is foundational for RAPL power reporting
