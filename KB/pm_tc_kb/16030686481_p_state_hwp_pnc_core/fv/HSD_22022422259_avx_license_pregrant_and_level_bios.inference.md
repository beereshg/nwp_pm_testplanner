# Deep Analysis: AVX License PreGrant and Level BIOS Knob Checks

| Field | Value |
|-------|-------|
| **HSD ID** | 22022422259 |
| **Title** | AVX License PreGrant and Level BIOS Knob checks |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | Pstate Stack |
| **Sub-Feature** | ICCP — AVX License Pre-Grant and AVX Level BIOS knobs |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies **AVX License Pre-Grant** and **AVX ICCP Level** BIOS knobs:
1. `AvxLicensePreGrant = 0x1` (Enabled) — pre-grants AVX license before any code requests it
2. `AvxIccpLevel = 0x3` (256 Heavy) — sets the AVX license level (default = 128 Heavy; test must set to non-default)

The test uses `flexcon` and checks that the calculated offset for ITD equals 0 after disabling ITD (pass criterion mentioned in steps). On NWP, the same ICCP/AVX license mechanism exists.

**Key Justification:**
- ICCP AVX license mechanism is present on NWP
- `Ready_for_testing` tag: confirmed ready for silicon validation
- `PMSS_NWP_READINESS_CHECK` tag: evaluated for NWP
- Same BIOS knobs expected on NWP BIOS

---

## Section B: NWP-Specific Test Procedure

### BIOS Knobs

| Knob | Test Value | Default | Function |
|------|-----------|---------|----------|
| `AvxLicensePreGrant` | 0x1 (Enabled) | 0x0 | Pre-grant AVX license to all cores at boot |
| `AvxIccpLevel` | 0x3 (256 Heavy) | 0x2 (128 Heavy) | AVX ICCP license level selection |

### Adapted Test Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Set BIOS knobs: `AvxLicensePreGrant = 0x1`, `AvxIccpLevel = 0x3` | Same BIOS knobs on NWP |
| 2 | Reboot NWP silicon | Standard reboot |
| 3 | Verify knobs persisted (post-reboot read) | `xmlcli` or BIOS read-back |
| 4 | Verify AVX license pre-grant effective | Check PCode ICCP AVX license registers |
| 5 | Verify AvxIccpLevel = 0x3 (256 Heavy) programmed | Register cross-check |
| 6 | Run flexcon validation | `flexcon` command; verify ICCP state |
| 7 | Check ITD offset = 0 after disabling ITD (pass criterion) | Same verification |

### ICCP AVX License Registers (NWP)

```python
# NWP AVX License Pre-Grant verification
# ICCP license state registers in PCode/iMH

try:
    # Read ICCP AVX license pregrant status
    iccp_cfg = sv.socket0.imh0.punit.ptpcioregs.ptpcioregs.iccp_avx_pregrant_cfg.read()
    print(f"ICCP AVX PreGrant config: 0x{iccp_cfg:08X}")
except Exception as e:
    print(f"ICCP AVX cfg: {e}")

# Verify license level
try:
    avx_license_level = sv.socket0.imh0.punit.ptpcioregs.ptpcioregs.avx_license_level.read()
    print(f"AVX License Level: 0x{avx_license_level:02X} (expected 0x3 = 256 Heavy)")
except Exception as e:
    print(f"AVX License Level: {e}")
```

### NWP Pass Criteria
- BIOS knobs programmed correctly post-reboot
- ICCP AVX license pre-granted to all cores (`AvxLicensePreGrant = 1`)
- AVX license level = 0x3 (256 Heavy) as configured
- ITD offset = 0 after disabling ITD (flexcon pass criterion)

---

## Section C: NWP Delta Impact Analysis

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| BIOS knobs | `AvxLicensePreGrant`, `AvxIccpLevel` | Same on NWP BIOS | Verify knob names match |
| ICCP mechanism | DMR ICCP | NWP ICCP (same architecture) | Direct reuse |
| flexcon | DMR platform config | NWP platform config | May need NWP flexcon config |
| AVX license levels | 128-Heavy=2, 256-Heavy=3 | Same encoding | Direct reuse |

---

## Section F: Recommendation

**Recommendation: ADOPT — verify BIOS knob names and flexcon NWP config**

AVX License Pre-Grant and Level BIOS knob verification is directly applicable on NWP.

Required adaptations:
1. Verify NWP BIOS has `AvxLicensePreGrant` and `AvxIccpLevel` knobs with same names
2. `flexcon` command may need NWP platform specification
3. Verify ICCP AVX register paths on NWP (`sv.socket0.imh0.*`)

**Priority**: Medium — `Ready_for_testing`; ICCP AVX license BIOS knob bring-up verification
