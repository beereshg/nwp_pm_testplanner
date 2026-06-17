# Deep Analysis: SVID Addressing Verification

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421922 |
| **Title** | SVID Addressing Verification |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | SVID |
| **Sub-Feature** | SVID bus addressing — VR address assignment for each die (CBB, IMH) |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

Verifies SVID bus addressing: each die (CBB, IMH) has a unique assigned VR address accessible via SVID. NWP has 2 CBBs + 1 IMH vs DMR's 4 CBBs + 2 IMHs — fewer SVID addresses.

Reference: NWP SOC PM HAS for SVID address map (steps link to DMR HAS; use NWP HAS equivalent).

Tags: `DMR_PO`, `plc.feature.p2`, `PMSS_NWP_READINESS_CHECK`.

---

## Section B: NWP-Specific Test Procedure

### NWP Command
```bash
python runPmx.py -x nwp.xml -p svid -p core_power -tM 60 -M 5
```

### NWP SVID Address Map
```python
# NWP topology: 2 CBBs + 1 IMH → verify only these addresses
# Expected SVID addresses per NWP HAS
for cbb_idx in range(2):  # NWP: 2 CBBs (not 4)
    addr = sv.socket0.cbb[cbb_idx].base.pcudata.svid_address
    # Verify matches NWP HAS assignment

# IMH (single on NWP)
imh0_addr = sv.socket0.imh0.pcudata.svid_address
```

### Pass Criteria
- Each SVID address unique across all 3 NWP dies
- SVID responses received from correct addresses (no collision, no silent fail)

---

## Section F: Recommendation

**Recommendation: ADOPT — NWP: 2 CBBs + 1 IMH → 3 SVID addresses (not 6 as in DMR); `nwp.xml`; verify against NWP HAS SVID address table**

**Priority**: High — `PMSS_NWP_READINESS_CHECK`; SVID addressing errors cause silent power management failures
