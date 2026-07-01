# TCD: SVID Mapping/Priority Verification

| Field | Value |
|-------|-------|
| **TCD ID** | [22022420775](https://hsdes.intel.com/appstore/article-one/#/22022420775) |
| **Title** | SVID Mapping/Priority Verification |
| **Parent TPF** | [15019477949](https://hsdes.intel.com/appstore/article-one/#/15019477949) |
| **Feature** | SVID |
| **NWP Disposition** | Runnable_On_N-1 |
| **KB last updated** | 2026-07-01 |

## Section 1: Architecture / Micro-architecture and Functionality

**SVID Mapping/Priority** verifies the SVID bus address table — each die has a unique address, VCCC2C responds at 05h, VCCFA_EHV is absent. NWP has 2 CBBs + 1 IMH = 3 compute die addresses (vs DMR 6). Address mapping errors cause silent VID mismatches.

### Block Diagram

```
NIO SVID master scans:
  01h PVCCIN_EHV0 -> ACK
  02h PVCCANA0    -> ACK
  03h PVCCINF     -> ACK
  05h PVCCC2C     -> ACK (NEW)
  0Dh PVCC3P3_AUX -> ACK
  (legacy VCCFA_EHV) -> NACK (removed)
NWP compute dies: IMH0, CBB0, CBB1 (unique addresses per NWP HAS)
```

### TC Coverage Map

| TC ID | Title | NWP Disposition |
|-------|-------|----------------|
| [22022421922](https://hsdes.intel.com/appstore/article-one/#/22022421922) | SVID Addressing Verification | Runnable_On_N-1 |

---

## Section 2: Interfaces and Protocols

| Interface | Register / Path | Purpose |
|-----------|----------------|---------|
| svid_address IMH0 | sv.socket0.imh0.pcudata.svid_address | IMH0 die SVID address |
| svid_address CBB0/1 | sv.socket0.cbb{0,1}.base.pcudata.svid_address | Per-CBB SVID addresses |
| VCCC2C GetVID | SVID command to 05h | ACK + valid VID = C2C VR present |

---

## Section 3: Reset, Power, and Clocking

- BIOS programs address table from fuse/strap values at CPL3
- Each die address must be unique; collisions cause wrong-VR VID targeting

---

## Section 4: Programming Model

- Verify GetVID ACK at each expected address; NACK at legacy VCCFA_EHV address
- PMx svid plugin validates addressing end-to-end with `nwp.xml`

---

## Section 5: Operational Behavior

1. BIOS writes address table; Primecode scans via GetVID at boot
2. VCCC2C/05h must return ACK; VCCFA_EHV legacy addr must return NACK
3. All 3 compute die addresses (IMH0, CBB0, CBB1) verified unique

---

## Section 6: Corner Cases & Error Handling

| Scenario | Expected Behavior |
|----------|-----------------|
| Address collision | Undefined VID; both VRs respond simultaneously |
| VCCC2C NACK at 05h | C2C VR uncontrolled; fix BIOS VR table |
| VCCFA_EHV ACK | DMR config leftover; critical to fix for NWP |

---

## Section 7: Security / Safety / Policy

- Address table is BIOS/fuse controlled; not OS-accessible
- Mapping errors classified safety-critical (silent voltage errors)

---

## Section 8: References

- [NWP PAS VR Table](https://docs.intel.com/documents/custom-xeon/newport-docs/platform/pas/NwpPAS.html) — NWP SVID address map: PVCCIN_EHV0/01h, PVCCANA0/02h, PVCCINF/03h, PVCCC2C/05h, PVCC3P3_AUX/0Dh
- [10nm SVID HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SVID/10nm%20SVID%20HAS.html) — SVID addressing; NACK behavior; 4-bit address space; uniqueness
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) — VCCC2C at SVID0/05h (HSD 14027373379); VCCFA_EHV removed (HSD 14027235624)
- [SVID Standalone IP HAS](https://docs.intel.com/documents/sysip_pm/HAS_gen4/IPPUNIT-177_Feature_HAS.html) — Gen4 SVID enumeration; address assignment; SVID inventory
