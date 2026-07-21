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

Validates the ITD global disable path — compensation zeroed across all domains scenario defined in [TCD 16031170075 — ITD Common Controls](https://hsdes.intel.com/appstore/article-one/#/16031170075) §5. Environment: NWP post-silicon, FV.

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

### Adapted Test Steps (from itd_pmx.py mainTest — disable loop via set_itdSlope)

| Step | Action | NWP Adaptation |
|------|--------|----------------|
| 1 | Run baseline ITD verification: for all domains (CCF slices, cores, IMH RCs, UCIe, VccInf), collect current voltage, temperature, ratio, and fuse coefficients | `python runPmx.py -x nwp.xml -p itd_thermal -tM 9 -M 3` |
| 2 | Record baseline voltages with ITD active — confirm non-zero ITD offset is being applied to at least one domain | Establishes reference for comparison after disable |
| 3 | Disable ITD: search all IMH pcudata slope registers and write each to zero; save original values in a dictionary for restoration | `set_itdSlope(setZero=True)` — iterates `imh.pcudata.search("slope_")` and zeroes each |
| 4 | Wait for FW thermal update cycle to process the slope change | Sleep/cycle delay for FW to recalculate compensation with zeroed slopes |
| 5 | For each domain: re-read actual voltage; calculate expected voltage as base VF curve voltage only (no ITD offset since all slopes are zero) | Same mainTest loop but with zero-slope fuse inputs → expected offset = 0 |
| 6 | Compare expected (base-only) voltage against actual voltage for each domain | Delta must be ≤ guardband (26 mV for IMH/core, 100 mV for CCF/UCIe) |
| 7 | Re-enable ITD: restore original slope values from saved dictionary | `set_itdSlope(setZero=False, setToPrev=True)` |
| 8 | Wait for FW to resume compensation; re-read voltages across all domains | Verify compensation has resumed — voltage should now include ITD offset again |
| 9 | Log results in tabulated per-domain table with columns: IP, base volt, slope, offset, guardband, delta, expected, actual, result | Script outputs formatted grid table per IP class |

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
