# Deep Analysis: [ITD] Verify ITD Disable

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421528 |
| **Title** | [ITD] Verify ITD disable |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | SoC Thermal Management > ITD |
| **Sub-Feature** | ITD Disable (debug mechanism) |
| **NWP Disposition** | **Runnable_On_N-1** |

---


## Test Case Intent

Validates that disabling ITD zeroes compensation across all domains and that re-enabling restores it. Collects baseline voltages with ITD active, writes all IMH pcudata slope registers to zero (global disable), waits for FW update cycle, verifies all domains return to base-only voltage (no ITD offset) within guardband, then restores original slopes and confirms compensation resumes.

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

ITD for any domain can be **disabled** by setting its `ITD_SLOPE` and `ITD_SLOPE_2` (if applicable) to 0. This causes the ITD algorithm to always calculate a voltage compensation of 0V, passing through uncompensated voltage. This is a debug-only feature used for electrical correctness testing. On NWP, the same disable mechanism applies to all ITD-controlled domains. The test is fully portable: same sequence of `itd.print_itd_info()`, zero-out slope via `pcudata.itd_slope=0`, verify compensation goes to zero. Primary adaptation: `dmr.xml` → `nwp.xml`.

**Key Justification:**
- ITD disable via slope zero is a firmware-level mechanism identical on NWP
- `ready_for_execution` tag in sub_feature: test is already validated for execution (DMR-side ready)
- `PMSS_NWP_READINESS_CHECK` tag: explicitly evaluated for NWP
- No domain-specific topology dependencies — this is a cross-domain mechanism

---

## Section B: NWP-Specific Test Procedure

### Pre-Conditions
- NWP silicon or VP with ITD active (non-zero slope fuses)
- PythonSv access to `sv.socket0.imh0.punit.*` and CBB punit
- `pm.focus.itd` module available
- Test command: `python runPmx.py -x nwp.xml -p itd_thermal -tM 9 -M 3`

### Adapted Test Steps (from itd_pmx.py mainTest — disable loop via set_itdSlope)

| Step | Action | Expected Result (PASS) | Failure Indication |
|------|--------|----------------------|-------------------|
| 1 | Collect baseline: for all domains, read current voltage, temperature, ratio, and fuse coefficients | All domains have readable non-zero ITD compensation active | No active compensation before test starts |
| 2 | Record baseline voltages with ITD active — confirm non-zero offset on at least one domain | At least one domain shows voltage > base VF (ITD offset present) | All domains at base VF — ITD may not be active |
| 3 | Disable ITD: write all IMH pcudata slope registers to zero; save originals for restoration | All slope registers written to 0 successfully | Write failure on any slope register |
| 4 | Wait for FW thermal update cycle to process the slope change | FW recalculates within one thermal loop iteration | Timeout waiting for voltage update |
| 5 | For each domain: re-read voltage; calculate expected as base VF only (no offset since slopes=0) | Expected voltage = base VF curve value (no ITD component) | Calculation error or read failure |
| 6 | Compare expected (base-only) against actual voltage per domain | Delta ≤ guardband (26 mV IMH/core, 100 mV CCF/UCIe) | Delta > guardband — residual compensation after disable |
| 7 | Re-enable ITD: restore original slope values from saved dictionary | All slopes restored to pre-test values | Restore failure |
| 8 | Wait for FW to resume; re-read voltages to confirm compensation resumed | Voltage includes ITD offset again (matches pre-disable baseline) | Compensation does not resume after re-enable |
| 9 | Log per-domain results table: IP, base volt, slope, offset, guardband, delta, expected, actual, PASS/FAIL | All rows show PASS | Any row shows FAIL |

### ITD Disable Methods on NWP

| Method | Scope | Effect |
|--------|-------|--------|
| `ITD_SLOPE` + `ITD_SLOPE_2` = 0 | Per-domain | Zero compensation |
| `ITD_CUTOFF_TJ` = 0 | All domains | No temp delta → zero compensation |
| `NEGATIVE_ITD_DISABLED=1` | TTD only | Disables negative compensation |
| OC Mailbox 0x18/0x19 bit 3 | TTD only | Dynamic disable |
| `CORE_PMA_CR_CONFIG_10[TRUE_TD_EN]=0` | Core TTD only | ACP true TD disable |

### NWP Pass Criteria
- After `itd_slope=0`: `itd.print_itd_info` shows all domains with 0V compensation
- All domains operate at base voltage (no ITD offset)
- Power consumption increases (voltage not reduced at high temp); verify safe margin
- Restore: power cycle restores fuse-based slope values

---

## Section C: NWP Delta Impact Analysis

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| `pcudata` interface | Available | Same on NWP | Direct reuse |
| Domain scope | All ITD domains affected | Same | Same disable mechanism |
| `itd.print_itd_info` | Shows DMR domain list | Shows NWP domain list | Verify NWP domain names shown |
| XML config | `dmr.xml` | `nwp.xml` | **Must update** |

---

## Section D: Key Registers & Validation Points

### PythonSv Validation Commands (NWP)

```python
from pm.focus import itd

SockNum = 0

# Step 2: Baseline
print("=== Baseline ITD Info ===")
itd.print_itd_info(SockNum, 0)

# Step 3: Disable (example — set slope to 0 via pcudata)
# NOTE: Exact pcudata path for NWP needs validation
# pcudata.itd_slope = 0  # apply for specific domain

# Step 4: Verify disabled
print("\n=== ITD After Disable ===")
itd.print_itd_info(SockNum, 0)

# Verify via RC offset register (should read 0)
try:
    vccinf_itd = sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.vccinf_itd_comp.read()
    print(f"VccInf ITD compensation: {vccinf_itd} (expected 0 when disabled)")
except Exception as e:
    print(f"VccInf ITD: {e}")
```

---

## Section E: Risk Assessment & Open Items

| # | Risk/Open Item | Severity | Notes |
|---|----------------|----------|-------|
| 1 | **`pcudata` interface on NWP** — `pcudata.itd_slope` mailbox path needs NWP validation | Low | Verify with NWP PM team; same concept, may have different path |
| 2 | **Electrical risk** — disabling ITD removes voltage guardband; run only on cool silicon to avoid reliability issues | Medium | Use VP if possible; limit on-silicon ITD disable to short test windows |

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; verify `pcudata` path**

ITD disable mechanism is architecture-level and identical on NWP. `ready_for_execution` on DMR means test methodology is stable.

Required adaptations:
1. `python runPmx.py -x nwp.xml -p itd_thermal -tM 9 -M 3`
2. Verify NWP `pcudata.itd_slope` interface path with NWP PM team
3. Use VP for extended ITD-disabled operation (electrical safety)

**Priority**: Medium — readiness check for debug capability; validates correct ITD framework functioning
