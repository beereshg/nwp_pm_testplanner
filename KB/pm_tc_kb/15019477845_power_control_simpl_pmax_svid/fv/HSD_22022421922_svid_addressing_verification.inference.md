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
### Test Case Intent

Verify SVID bus addressing: each NWP die has a **unique VR address** on the SVID bus and responds correctly at that address. NWP has **2 CBBs + 1 IMH = 3 SVID-addressable dies** (vs DMR’s 4 CBBs + 2 IMHs = 6). Key NWP delta: **VCCC2C added at SVID0/05h**; VCCFA_EHV removed. Address collisions or silent failures would cause Punit to target the wrong VR during VID changes.

**NWP SVID rail address map (NWP PAS):**

| Rail | SVID Address | Notes |
|------|-------------|-------|
| PVCCIN_EHV0 | 01h | Main input rail |
| PVCCANA0 | 02h | Analog |
| PVCCINF | 03h | Infrastructure |
| **PVCCC2C** | **05h** | **New on NWP** |
| PVDD0 | TBD | LPDDR6 |
| PVDD1 | TBD | LPDDR6 |
| PVCC3P3_AUX | 0Dh | Psys sensor |
| VCCFA_EHV | **ABSENT** | Removed from NWP |

---

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| SV session | `sv.socket0.imh0` reachable |
| Platform S0 | Fully booted; BIOS SVID address table initialized |
| Imports | `import time` |
| Namespace | `imh0 = sv.socket0.imh0` alias |
| NWP topology | 2 CBBs (cbb0, cbb1) + 1 IMH (imh0) — no cbb2/cbb3 or imh1 |

---

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|----------------------|-------------------|
| 1 | Read SVID addresses for IMH0 and both CBBs. `imh0_addr = sv.socket0.imh0.pcudata.svid_address.read(); cbb0_addr = sv.socket0.cbb[0].base.pcudata.svid_address.read(); cbb1_addr = sv.socket0.cbb[1].base.pcudata.svid_address.read(); print(f'IMH0={hex(imh0_addr)} CBB0={hex(cbb0_addr)} CBB1={hex(cbb1_addr)}')` | All 3 addresses unique; match NWP HAS SVID address table | Duplicate addresses or unexpected values — BIOS address table misconfigured |
| 2 | Verify PVCCC2C responds at SVID address 05h (new NWP rail). `# Issue GetVID to SVID0/05h via Primecode SVID interface; verify ACK received` | ACK at 05h; valid VID code returned for VCCC2C | NACK at 05h — VCCC2C MBVR not responding; check BIOS SVID table |
| 3 | Verify VCCFA_EHV is absent (no SVID ACK at its former DMR address). `# Legacy DMR VCCFA_EHV address should return NACK on NWP` | NACK (no response) at VCCFA_EHV legacy address | ACK received — old DMR address leftover; BIOS VR table not updated for NWP |
| 4 | Run PMx SVID addressing test. `python runPmx.py -x nwp.xml -p svid -p core_power -tM 60 -M 5` | PMx PASS; all address assertions validated | PMx FAIL — collect run log |

---

### Pass / Fail Criteria

- **PASS**: All 3 NWP die addresses unique; VCCC2C responds at 05h; VCCFA_EHV absent (NACK); PMx SVID PASS.
- **FAIL**: Address collision; VCCC2C NACK at 05h; VCCFA_EHV ACK (old config); PMx FAIL.

---

### Health Checks

| Register / Log | Access | Pass/Fail Criteria |
|----------------|--------|-------------------|
| svid_address IMH0 | sv.socket0.imh0.pcudata.svid_address | Matches NWP HAS assignment |
| svid_address CBB0/1 | sv.socket0.cbb{0,1}.base.pcudata.svid_address | Unique; match NWP HAS table |
| VCCC2C at 05h | SVID GetVID at address 05h | ACK; valid VID |
| VCCFA_EHV | SVID at legacy DMR address | NACK — rail absent on NWP |
| NLOG SVID | peg_client --nlog --filter SVID | No address collision or SVID errors |

---

### Post-Process

No writes performed. Collect NLOG on any SVID error. Report address values if VCCC2C/VCCFA_EHV check fails.

---

### References

- [NWP PAS VR Table](https://docs.intel.com/documents/custom-xeon/newport-docs/platform/pas/NwpPAS.html) — NWP SVID address map: PVCCIN_EHV0/01h, PVCCANA0/02h, PVCCINF/03h, PVCCC2C/05h, PVCC3P3_AUX/0Dh
- [NWP HAS Impact §2.1 — VCCC2C SVID Rail](c:\github\nwp_testplan\KB\pm_features\nwp_architecture\nwp_has_impact_on_pm_fv.md) — VCCC2C at SVID0/05h (HSD 14027373379); VCCFA_EHV removed (HSD 14027235624)
- [DMR SVID HAS](https://docs.intel.com/documents/pm_doc/src/server/dmr/pm_features/svid/svid.html) — SVID addressing protocol; NACK behavior; address uniqueness requirements

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
