# Deep Analysis: RAPL MSR Checks - Negative Test Case

| Field | Value |
|-------|-------|
| **HSD ID** | 22022422029 |
| **Title** | RAPL MSR checks - Negative test case |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Socket RAPL |
| **Sub-Feature** | Deprecated RAPL MSRs — verify they have no effect on RAPL algorithm |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies that **legacy RAPL MSRs are deprecated and have no effect** on the RAPL algorithm:
- DMR (and NWP) dropped MSR-based RAPL interface
- Deprecated MSRs: `IA32_PKG_POWER_SKU_UNIT`, `PACKAGE_POWER_INFO`, `PACKAGE_RAPL_LIMIT`, `PACKAGE_ENERGY_STATUS`
- Test confirms: writing to these deprecated MSRs does NOT affect CSR or TPMI registers
- Most are read-only (writes silently ignored)

On NWP: same architecture — RAPL is via TPMI/CSR only; MSR interface deprecated. Tags: `DMR_PO`, `plc.feature.p2`, `PMSS_NWP_READINESS_CHECK`.

---

## Section B: NWP-Specific Test Procedure

### Deprecated RAPL MSRs (NWP)

| MSR | Name | Expected on NWP |
|-----|------|-----------------|
| 0x606 | IA32_PKG_POWER_SKU_UNIT | Deprecated — writes ignored |
| 0x614 | PACKAGE_POWER_INFO | Deprecated — read-only or deprecated |
| 0x610 | PACKAGE_RAPL_LIMIT | Deprecated — writes have no effect on TPMI |
| 0x611 | PACKAGE_ENERGY_STATUS | Deprecated — not updated by HW |

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Read current TPMI RAPL state before MSR test | `socket_rapl_pl1_control.pl1_power` baseline |
| 2 | Write to deprecated RAPL MSR (e.g., MSR 0x610 with new PL1) | `wrmsr 0x610 <new_pl1_encoding>` |
| 3 | Read TPMI `socket_rapl_pl1_control` | Should be unchanged (MSR write had no effect) |
| 4 | Read CSR `package_rapl_limit_cfg` | Should be unchanged |
| 5 | Repeat for each deprecated RAPL MSR | Confirm none affect RAPL algorithm |
| 6 | Verify MSRs are read-only or return fixed values | Read back shows fixed value or 0 |

### Pass Criteria
- Writing to any deprecated RAPL MSR has no effect on TPMI/CSR RAPL registers
- Deprecated MSRs return fixed values or 0 on read (not live RAPL values)
- No system fault or #GP when accessing deprecated MSRs (graceful handling)
- RAPL algorithm continues operating only via TPMI/CSR interface

---

## Section D: Key Registers & Validation Points

```python
# NWP: Read TPMI state before MSR write
pl1_tpmi_before = sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.socket_rapl_pl1_control.pl1_power.read()

# Write deprecated RAPL MSR (in OS)
# wrmsr 0x610 0x00DD_8000_00EA_8000  (example PL1/PL2 encoding)

# Verify TPMI unchanged
pl1_tpmi_after = sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.socket_rapl_pl1_control.pl1_power.read()
assert pl1_tpmi_before == pl1_tpmi_after, "MSR write should not affect TPMI"
```

---

## Section F: Recommendation

**Recommendation: ADOPT — RAPL MSRs deprecated on NWP same as DMR; verify no TPMI/CSR effect**

1. `python runPmx.py -x nwp.xml -p cpu_rapl -tM 6 -M 3`
2. Write to each deprecated RAPL MSR; verify no change in TPMI or CSR RAPL registers
3. Confirms NWP correctly ignores MSR-based RAPL interface

**Priority**: Medium — `plc.feature.p2`; negative test validates that deprecated MSR paths are truly non-functional — important for software compatibility
