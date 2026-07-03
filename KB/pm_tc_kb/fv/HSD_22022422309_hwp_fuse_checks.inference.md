# Deep Analysis: HWP Fuse Checks

| Field | Value |
|-------|-------|
| **HSD ID** | 22022422309 |
| **Title** | HWP Fuse Checks |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | Pstate Stack |
| **Sub-Feature** | HWP enabling fuse verification |
| **NWP Disposition** | **Runnable_On_N-1** |

---

### Test Case Intent

Verify **HWP enabling fuses** are correctly programmed and propagated: `HWP_ENABLE` fuse must be set on NWP for HWP to be activatable by BIOS. This is a boot-time fuse verification test — no runtime workload needed. `ti_gate.b0` / `PMSS_NWP_READINESS_CHECK`.

---

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| SV session | `sv.socket0.imh0.fuses` accessible |
| Platform S0 | Fully booted post-PH6 |
| PMx | `python flexconPM.py -i NWPSV.ini` |

---

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|----------------------|-------------------|
| 1 | Read HWP enable fuse from IMH. `hwp_fuse = sv.socket0.imh0.fuses.punit.hwp_enable.read()` | = 1 (HWP hardware support fused on) | = 0 — HWP not fused; BIOS cannot enable HWP |
| 2 | Verify fuse propagated: enable HWP via BIOS (HWPMEnable=1); confirm IA32_PM_ENABLE[0]=1. `rdmsr 0x770` | IA32_PM_ENABLE[0]=1; fuse allows HWP activation | = 0 after BIOS enable — fuse blocking HWP |
| 3 | Read CPUID leaf 0x6: verify HWP capability bit (bit 7) = 1. | CPUID.0x6.EAX[7] = 1 (HWP supported) | = 0 — HWP capability not advertised; check fuse |
| 4 | Run flexconPM fuse checkout. `python flexconPM.py -i NWPSV.ini` | flexconPM PASS | flexconPM FAIL |

---

### Pass / Fail Criteria

- **PASS**: HWP fuse=1; IA32_PM_ENABLE[0] settable; CPUID advertises HWP; flexconPM PASS.
- **FAIL**: Fuse=0; IA32_PM_ENABLE not sticky; CPUID bit clear; flexconPM FAIL.

---

### Health Checks

| Register / Log | Access | Pass/Fail Criteria |
|----------------|--------|-------------------|
| hwp_enable fuse | sv.socket0.imh0.fuses.punit.hwp_enable | = 1 |
| CPUID.6.EAX[7] | CPUID leaf 6 | = 1 (HWP hardware coordination) |
| IA32_PM_ENABLE | MSR 0x770 | Settable when fuse=1 |

---

### Post-Process

Read-only fuse test. Collect fuse dump on failure.

---

### References

- [Core P-state HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Core_Pstates/Core_Pstate_HAS.html) — HWP fuse; CPUID.0x6.EAX[7]; IA32_PM_ENABLE sticky behavior
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) — NWP HWP fuse configuration

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies three HWP-related fuses:
1. `fw_fuses_hwp_enable` — HWP feature enabled fuse
2. `fw_fuses_hwp_interrupt_enable` — HWP interrupt capability fuse
3. `fw_fuses_hwp_peci_support` — HWP PECI (OOB mode) support fuse

Uses `pm.Active_PM.Pstate_Stack.hwp_fuses.fuse_check()` Python function. Also supports fusedump XML via `sv.socket0.fuses.export_xml("path")`.

On NWP, the same HWP enabling fuses are expected (same PrimeCode fuse naming convention with NWP-specific fuse hierarchy).

**Key Justification:**
- HWP fuses present on NWP
- `DMR_PO` tag: silicon validation bring-up priority (fuse check is bring-up gate)
- `PMSS_NWP_READINESS_CHECK` tag: evaluated for NWP

---

## Section B: NWP-Specific Test Procedure

### Expected Fuse Values

| Fuse Name | Expected Value | Function |
|-----------|----------------|----------|
| `fw_fuses_hwp_enable` | 1 (enabled) | HWP feature gate fuse |
| `fw_fuses_hwp_interrupt_enable` | 1 (enabled) | HWP interrupt capability gate |
| `fw_fuses_hwp_peci_support` | 1 (enabled) | PECI OOB mode support gate |

### Adapted Test Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Run flexcon HWP fuse check | `flexcon` with NWP config |
| 2 | Read HWP fuses directly | `pm.Active_PM.Pstate_Stack.hwp_fuses.fuse_check()` |
| 3 | Export fusedump XML | `sv.socket0.fuses.export_xml("nwp_fuses.xml")` |
| 4 | Parse fusedump for HWP fuse values | Same script; verify fuse names on NWP |

### NWP Fuse Read

```python
# NWP HWP Fuse Verification

try:
    hwp_enable = sv.socket0.imh0.fuses.punit.fw_fuses_hwp_enable.read()
    print(f"fw_fuses_hwp_enable: {hwp_enable} (expected 1)")
except Exception as e:
    print(f"fw_fuses_hwp_enable: {e}")

try:
    hwp_int = sv.socket0.imh0.fuses.punit.fw_fuses_hwp_interrupt_enable.read()
    print(f"fw_fuses_hwp_interrupt_enable: {hwp_int} (expected 1)")
except Exception as e:
    print(f"fw_fuses_hwp_interrupt_enable: {e}")

try:
    hwp_peci = sv.socket0.imh0.fuses.punit.fw_fuses_hwp_peci_support.read()
    print(f"fw_fuses_hwp_peci_support: {hwp_peci} (expected 1)")
except Exception as e:
    print(f"fw_fuses_hwp_peci_support: {e}")

# Generate fusedump
try:
    sv.socket0.fuses.export_xml("c:/temp/nwp_fuses.xml")
    print("Fusedump saved to c:/temp/nwp_fuses.xml")
except Exception as e:
    print(f"Fusedump: {e}")
```

### NWP Pass Criteria
- All three HWP fuses = 1 (enabled) on production NWP parts
- HWP feature accessible (CPUID Leaf 6 EAX bit 7 = 1)
- Fusedump XML contains correct HWP fuse values

---

## Section F: Recommendation

**Recommendation: ADOPT — fuse names likely same on NWP; verify NWP namednodes path**

HWP fuse check is directly applicable on NWP. Fuse names may differ slightly (NWP vs DMR naming).

Required adaptations:
1. Verify NWP fuse names: `fw_fuses_hwp_enable`, `fw_fuses_hwp_interrupt_enable`, `fw_fuses_hwp_peci_support`
2. NWP fuse path: `sv.socket0.imh0.fuses.*` (not `imh1` — NWP has single iMH)
3. Verify `hwp_fuses.fuse_check()` Python module works on NWP

**Priority**: High — `DMR_PO`; fuse check is bring-up gate for HWP feature
