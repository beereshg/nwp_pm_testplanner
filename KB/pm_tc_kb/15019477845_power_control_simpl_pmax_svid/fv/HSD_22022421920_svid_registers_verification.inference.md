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

### Test Case Intent

Verify SVID-related registers (control, status, vendor, capability) contain correct power-on defaults and match spec after BIOS initialization. This is a foundational register-state checkout confirming BIOS SVID init sequence programmed the correct values before OS handoff. NWP: single IMH0; 2 CBBs (cbb0+cbb1). `NGA_MAIN` priority.

---

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| SV session | `sv.socket0.imh0` reachable without timeout |
| Platform S0 | Fully booted to SVOS; BIOS SVID init complete |
| Namespace | `imh0 = sv.socket0.imh0` alias set |
| PMx available | `python runPmx.py -x nwp.xml -p svid -p core_power -tM 60 -M 5` |
| BIOS | Normal boot; SVID VR table initialized; no SVID errors at boot |

---

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|----------------------|-------------------|
| 1 | Read IMH0 SVID control register and verify default state. `imh0 = sv.socket0.imh0; svid_ctrl = imh0.pcudata.svid_control.read(); print(f'IMH0 SVID_CONTROL=0x{svid_ctrl:08X}')` | SVID_CONTROL = expected default per NWP SVID HAS; no error bits set | SVID_CONTROL has unexpected value — BIOS SVID init failed |
| 2 | Read IMH0 SVID status register and verify no error flags. `svid_sts = imh0.pcudata.svid_status.read(); print(f'IMH0 SVID_STATUS=0x{svid_sts:08X}'); assert not (svid_sts & 0xF000), 'SBE/timeout bits set'` | SVID_STATUS = valid operating state; SBE/NACK/timeout bits clear | Error bits set — SVID bus communication failure post-boot |
| 3 | Read CBB0 and CBB1 SVID control registers; verify both have correct defaults. `for i in [0,1]: ctrl=sv.socket0.cbb[i].base.pcudata.svid_control.read(); print(f'CBB{i} SVID_CONTROL=0x{ctrl:08X}')` | Both CBB SVID_CONTROL registers match expected defaults; CBB2/3 absent on NWP | Any CBB register differs from expected — BIOS did not program CBB SVID init |
| 4 | Run PMx SVID plugin end-to-end register checks. `python runPmx.py -x nwp.xml -p svid -p core_power -tM 60 -M 5` | PMx SVID + core_power plugins PASS all register assertions | PMx FAIL — collect run log; check which register assertion failed |

---

### Pass / Fail Criteria

- **PASS**: All SVID registers contain correct power-on defaults; no error bits; PMx SVID PASS.
- **FAIL**: Any register differs from spec default; SBE/timeout bits set; PMx FAIL.

---

### Health Checks

| Register / Log | Access | Pass/Fail Criteria |
|----------------|--------|-------------------|
| svid_control | sv.socket0.imh0.pcudata.svid_control | Matches BIOS-programmed SVID default state |
| svid_status | sv.socket0.imh0.pcudata.svid_status | Error bits (SBE/NACK/timeout) = 0 |
| CBB svid_control | sv.socket0.cbb{0,1}.base.pcudata.svid_control | Both CBBs match spec defaults |
| NLOG SVID | peg_client --nlog --filter SVID | No SVID errors at boot or during test |

---

### Post-Process

Read-only test — no writes. Collect NLOG if any error bits observed: `peg_client --nlog --filter SVID`. Report register dump on PMx failure.

---

### References

- [NWP PAS VR Table](https://docs.intel.com/documents/custom-xeon/newport-docs/platform/pas/NwpPAS.html) — NWP SVID rail map; register defaults after BIOS SVID init
- [DMR SVID HAS](https://docs.intel.com/documents/pm_doc/src/server/dmr/pm_features/svid/svid.html) — SVID control/status/vendor register definitions; error bit encoding
- [NWP HAS Impact §2.1](c:\github\nwp_testplan\KB\pm_features\nwp_architecture\nwp_has_impact_on_pm_fv.md) — VCCFA_EHV removed; VCCC2C added; update register map
- [Primecode RAPL DMR](https://docs.intel.com/documents/primecode/primecode_two/firmware_architecture/ip_drivers_and_libraries/rapl_dmr.html) — SVID register state required for RAPL power accounting

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
