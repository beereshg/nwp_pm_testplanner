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
