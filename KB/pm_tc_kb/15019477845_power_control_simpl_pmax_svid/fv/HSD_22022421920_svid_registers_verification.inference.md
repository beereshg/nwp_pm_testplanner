# Deep Analysis: SVID Registers Verification

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421920 |
| **Title** | SVID Registers Verification |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | SVID |
| **Sub-Feature** | SVID register state verification (SVID control, status, vendor, capability registers) |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

Verifies SVID-related registers match expected power-on defaults and spec. Template content incomplete in source HSD.

Tags: `DMR_PO`, `plc.feature.p2`, `PMSS_NWP_READINESS_CHECK`.

---

## Section B: NWP-Specific Test Procedure

### NWP Command
```bash
python runPmx.py -x nwp.xml -p svid -p core_power -tM 60 -M 5
```

### Key NWP Register Paths
```python
# NWP: single IMH → imh0 only
sv.socket0.imh0.pcudata.svid_control
sv.socket0.imh0.pcudata.svid_status
# CBB SVID registers
sv.socket0.cbb[0].base.pcudata.svid_control
sv.socket0.cbb[1].base.pcudata.svid_control
```

### Pass Criteria
- All SVID registers match spec defaults at boot
- SVID control and status registers reflect correct operating mode
- PMx SVID plugin register checks pass

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; single IMH → `imh0` only; 2 CBBs; template content incomplete — rely on PMx assertions**

**Priority**: High — `PMSS_NWP_READINESS_CHECK`; register state verification is foundational
