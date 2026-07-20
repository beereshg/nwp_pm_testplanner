# Deep Analysis: [GPIO Interface] Verify GPIO_BUMP Thermals Fuses

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421480 |
| **Title** | [GPIO Interface] Verify GPIO_BUMP Thermals Fuses |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | SoC Thermal Management > GPIO Interface |
| **NWP Disposition** | **Runnable_On_N-1** |

---


## Test Case Intent

Validates the GPIO bump thermal fuse enable/disable checkout scenario defined in [TCD 22022420589 -- GPIO Interface](https://hsdes.intel.com/appstore/article-one/#/22022420589) S5. Environment: NWP post-silicon, FV.

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies that the GPIO bump thermal enable fuses are correctly programmed: `iMH0` should have them set (1) and `iMH1` (if present) should have them clear (0). The fuses checked are `ENABLE_XXPROCHOT_N_FUSE`, `ENABLE_XXMEMHOT_IN_N_FUSE`, `ENABLE_XXMEMHOT_OUT_N_FUSE`, `ENABLE_XXMEMTRIP_N_FUSE` in the PTPCFSMS GPIO_BUMP_ENABLES register. On NWP, these GPIO thermal pins are supported and the fuse enables exist. The adaptation is updating the fuse read path for NWP's single-IMH topology (`imh0` only; no `imh1` to check as clear).

**Key Justification:**
- GPIO bump thermal enable fuses (PROCHOT/MEMHOT/MEMTRIP) are present on NWP
- NWP has single IMH (`imh0`); the "iMH0 set, iMH1 clear" rule becomes "iMH0 set" only
- `flexcon_pm.py` gpio_fuse_check plugin adapts to NWP single-IMH
- `DMR_PO` tag: silicon validation test

---

## Section B: NWP-Specific Test Procedure

### Pre-Conditions
- NWP platform (silicon or VP with correct fuse programming)
- PythonSv access to `sv.socket0.imh0.punit.ptpcfsms.ptpcfsms`
- `flexcon_pm.py` with NWP config (or direct PythonSv fuse read)

### Adapted Test Steps

| Step | Action | NWP Adaptation |
|------|--------|----------------|
| 1 | Read `GPIO_BUMP_ENABLES` register on `imh0` | NWP: single IMH; `sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.gpio_bump_enables` |
| 2 | Verify `ENABLE_XXPROCHOT_N_FUSE` = 1 on `imh0` | Same expected value; NWP only has imh0 |
| 3 | Verify `ENABLE_XXMEMHOT_IN_N_FUSE` = 1 on `imh0` | Same |
| 4 | Verify `ENABLE_XXMEMHOT_OUT_N_FUSE` = 1 on `imh0` | Same |
| 5 | Verify `ENABLE_XXMEMTRIP_N_FUSE` = 1 on `imh0` | Same |
| 6 | (DMR only) Verify `imh1` has all four fuses = 0 | **NWP: SKIP** — NWP has single IMH; `imh1` does not exist |

### Alternative: flexcon_pm plugin
```bash
# Run gpio_fuse_check via flexcon_pm plugin (adapt for NWP single-IMH)
python pysvext.diamondrapids_flexcon.plugins.flexcon_pm.py --function gpio_fuse_check --xml nwp.xml
```

### NWP Pass Criteria
- All four GPIO_BUMP_ENABLES fuses are set (1) on `imh0`
- No `imh1` to check (NWP single-IMH — this step passes by topology)

---

## Section C: NWP Delta Impact Analysis

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| IMH count | 2 (imh0, imh1) | 1 (imh0 only) | Test step 6 (imh1=0 check) becomes N/A |
| Fuse names | Same register path | Same on NWP | Direct reuse |
| flexcon_pm plugin | `diamondrapids_flexcon` | May need NWP variant | Check if NWP plugin exists |

---

## Section D: Key Registers & Validation Points

### PythonSv Validation Commands (NWP)

```python
# Read GPIO BUMP ENABLES fuses on NWP single IMH
ptpcfsms = sv.socket0.imh0.punit.ptpcfsms.ptpcfsms

try:
    gpio_bump = ptpcfsms.gpio_bump_enables.read()
    print(f"GPIO_BUMP_ENABLES: 0x{gpio_bump:08X}")

    # Check individual fuse bits
    prochot_en = ptpcfsms.gpio_bump_enables.enable_xxprochot_n_fuse.read()
    memhot_in_en = ptpcfsms.gpio_bump_enables.enable_xxmemhot_in_n_fuse.read()
    memhot_out_en = ptpcfsms.gpio_bump_enables.enable_xxmemhot_out_n_fuse.read()
    memtrip_en = ptpcfsms.gpio_bump_enables.enable_xxmemtrip_n_fuse.read()

    print(f"PROCHOT_N fuse: {prochot_en} (expected 1)")
    print(f"MEMHOT_IN_N fuse: {memhot_in_en} (expected 1)")
    print(f"MEMHOT_OUT_N fuse: {memhot_out_en} (expected 1)")
    print(f"MEMTRIP_N fuse: {memtrip_en} (expected 1)")
except Exception as e:
    print(f"GPIO_BUMP_ENABLES: {e}")
```

---

## Section E: Risk Assessment & Open Items

| # | Risk/Open Item | Severity | Notes |
|---|----------------|----------|-------|
| 1 | **flexcon_pm plugin NWP support** — `pysvext.diamondrapids_flexcon` may not have NWP equivalent; PythonSv direct fuse read is the fallback | Low | Use PythonSv fallback if plugin unavailable |
| 2 | **GPIO_BUMP_ENABLES register path** — NWP namednodes path needs bring-up validation | Low | Estimate above matches PTPCFSMS pattern |

---

## Section F: Recommendation

**Recommendation: ADOPT with topology simplification**

This test trivially simplifies on NWP: check only `imh0` fuses (imh1 does not exist). The fuse values and register path are the same.

Required adaptations:
1. Remove `imh1` step (N/A on NWP)
2. Update `flexcon_pm.py` command for NWP config, or use PythonSv direct fuse read
3. Confirm NWP `GPIO_BUMP_ENABLES` register path in PTPCFSMS namednodes

**Priority**: Medium — Fuse checkout is a bring-up validation step; foundational for GPIO thermal tests
