# Deep Analysis: AVX P1 Level BIOS Knob Check

| Field | Value |
|-------|-------|
| **HSD ID** | 22022422293 |
| **Title** | Avx P1 Level BIOS knob check |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | Pstate Stack |
| **Sub-Feature** | AVX P1 Level BIOS knob (AvxP1Level) |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies the **AvxP1Level** BIOS knob (0x1 or 0x2), which sets the AVX Guaranteed (P1) ratio level. The two levels correspond to different guaranteed frequency behaviors for AVX workloads. The test verifies:
1. BIOS knob value persists after reboot
2. The desired AVX P1 level is granted (effective P1 for AVX workloads)

Related: Ring P1 should follow `PPPx_SST_PP_INFO_11[P1_FABRIC_RATIO]` (OPEN item in steps — this may be relevant for NWP SST feature). On NWP, the `AvxP1Level` BIOS knob is expected to be present.

**Key Justification:**
- AVX P1 Level BIOS knob applicable on NWP
- `PMSS_NWP_READINESS_CHECK` tag: evaluated for NWP
- Same BIOS knob mechanism expected on NWP

---

## Section B: NWP-Specific Test Procedure

### AVX P1 Level Mapping

| AvxP1Level | Description | Effect |
|------------|-------------|--------|
| 0x0 | Default (no AVX P1 clip) | P1 = fused P1 regardless of AVX |
| 0x1 | AVX P1 Level 1 | P1 guaranteed at Level 1 during AVX |
| 0x2 | AVX P1 Level 2 | P1 guaranteed at Level 2 during AVX |

### Adapted Test Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Set `AvxP1Level = 0x1` in BIOS; reboot | Same BIOS knob on NWP |
| 2 | Verify knob persisted | `xmlcli` or BIOS read-back |
| 3 | Verify AVX P1 Level 1 is resolved | Read platform P1 ratio registers |
| 4 | Run flexcon verification | `flexcon` command |
| 5 | Repeat with `AvxP1Level = 0x2` | Same verification steps |
| 6 | Verify Ring P1 follows `PPPx_SST_PP_INFO_11[P1_FABRIC_RATIO]` if applicable | Per open item; NWP-specific investigation |

### NWP Register Check

```python
# NWP AVX P1 Level Verification

# Read current P1 ratio from PLATFORM_INFO
try:
    platform_info = sv.socket0.imh0.punit.ptpcioregs.ptpcioregs.platform_info.read()
    p1_ratio = (platform_info >> 8) & 0xFF
    print(f"P1 ratio from PLATFORM_INFO: {p1_ratio}")
except Exception as e:
    print(f"PLATFORM_INFO: {e}")

# Read AVX P1 config from iMH (actual AVX P1 level programmed)
try:
    avx_p1_cfg = sv.socket0.imh0.punit.ptpcioregs.ptpcioregs.avx_p1_level.read()
    print(f"AVX P1 Level config: 0x{avx_p1_cfg:02X}")
except Exception as e:
    print(f"AVX P1 Level: {e}")
```

### NWP Pass Criteria
- `AvxP1Level` BIOS knob persists across reboot
- Configured AVX P1 level reflected in hardware registers
- Guaranteed ratio for AVX workloads matches `AvxP1Level` setting
- Ring P1 (if applicable) follows fabric ratio specification

---

## Section C: NWP Delta Impact Analysis

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| `AvxP1Level` BIOS knob | Present | Expected on NWP | Verify knob name |
| AVX P1 ratio levels | DMR-specific values | NWP-specific values | Get from NWP HAS |
| Ring P1 open item | SST-PP based | SST-PP ZBB on NWP | Investigate NWP non-SST ring P1 |
| `flexcon` | DMR platform | NWP platform config | Update config |

---

## Section F: Recommendation

**Recommendation: ADOPT — verify AvxP1Level BIOS knob name and values on NWP**

AVX P1 Level BIOS knob verification is applicable on NWP.

Required adaptations:
1. Verify `AvxP1Level` BIOS knob present on NWP with same name and value encoding
2. Get NWP-specific AVX P1 ratio values for level 1 and level 2
3. Investigate Ring P1 for NWP (not SST-PP since ZBB)

**Priority**: Low-Medium — no `DMR_PO` tag; AVX P1 guaranteed ratio BIOS knob validation
