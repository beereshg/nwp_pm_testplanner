# Deep Analysis: Flex Ratio Configuration and Functionality

| Field | Value |
|-------|-------|
| **HSD ID** | 22022422287 |
| **Title** | Flex ratio configuration and functionality |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | Pstate Stack |
| **Sub-Feature** | Flex Ratio — BIOS-programmable P1 ratio clip |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

**Flex Ratio** allows BIOS to clip the common P1 ratio (Guaranteed ratio) on device reset exit. The value is sent from iMH PrimeCode to CBB PCode in the HPM message `DISTRIBUTE_STRAPS_CBB.DATA_OFFSET=1`. The feature is enabled by the `FLEX_RATIO_DISABLE` fuse (fuse = 0 → Flex Ratio enabled).

On NWP, the same Flex Ratio mechanism exists: iMH PrimeCode sends flex ratio to CBB PCode via HPM message. Primary adaptation: `flexcon` command may need NWP platform config.

**Key Justification:**
- Flex Ratio via HPM `DISTRIBUTE_STRAPS_CBB` present on NWP
- `FLEX_RATIO_DISABLE` fuse present on NWP
- `DMR_PO` tag: silicon validation bring-up priority
- `PMSS_NWP_READINESS_CHECK` tag: evaluated for NWP

---

## Section B: NWP-Specific Test Procedure

### Flex Ratio Mechanism

```
BIOS → writes Flex Ratio to BIOS mailbox
iMH PrimeCode → reads from BIOS mailbox
iMH PrimeCode → sends to CBB PCode via HPM: DISTRIBUTE_STRAPS_CBB.DATA_OFFSET=1
CBB PCode → clips P1 ratio to min(fused_P1, flex_ratio)
```

### Adapted Test Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Verify `FLEX_RATIO_DISABLE` fuse = 0 (flex ratio enabled) | `sv.socket0.imh0.fuses.punit.flex_ratio_disable.read()` |
| 2 | Set Flex Ratio BIOS knob to value X (below fused P1) | BIOS knob sets the clip value |
| 3 | Reboot | Platform reboot |
| 4 | Verify P1 ratio clipped to X after reset | Read resolved P1 from `PLATFORM_INFO` and CBB registers |
| 5 | Verify HPM message `DISTRIBUTE_STRAPS_CBB` contains flex ratio | iMH → CBB communication verified |
| 6 | Run flexcon to verify flex ratio configuration | `flexcon` command |
| 7 | Set Flex Ratio > fused P1; verify clamped to fused P1 | Flex Ratio cannot exceed fused value |

### Key Registers (NWP)

```python
# NWP Flex Ratio Verification

# Check FLEX_RATIO_DISABLE fuse
try:
    flex_dis = sv.socket0.imh0.fuses.punit.flex_ratio_disable.read()
    print(f"FLEX_RATIO_DISABLE fuse: {flex_dis} (0=enabled, 1=disabled)")
except Exception as e:
    print(f"FLEX_RATIO_DISABLE fuse: {e}")

# Read resolved P1 ratio from iMH (after flex ratio applied)
try:
    platform_info = sv.socket0.imh0.punit.ptpcioregs.ptpcioregs.platform_info.read()
    p1_ratio = (platform_info >> 8) & 0xFF
    print(f"PLATFORM_INFO.P1_RATIO: {p1_ratio} (expected = min(fused_P1, flex_ratio))")
except Exception as e:
    print(f"PLATFORM_INFO: {e}")

# Verify CBB received flex ratio via HPM
for cbb_idx in range(2):
    cbb = getattr(sv.socket0, f'cbb{cbb_idx}')
    try:
        cbb_p1 = cbb.base.punit_regs.punit_gpsb.gpsb_infvnn_crs.p1_ratio.read()
        print(f"CBB{cbb_idx} P1 ratio: {cbb_p1}")
    except Exception as e:
        print(f"CBB{cbb_idx} P1: {e}")
```

### NWP Pass Criteria
- `FLEX_RATIO_DISABLE = 0` → Flex Ratio feature active
- Configured flex ratio correctly clips P1 (iMH P1 = min(fused P1, flex ratio))
- CBB PCode receives clipped P1 via HPM `DISTRIBUTE_STRAPS_CBB`
- Flex ratio > fused P1 → clamped to fused P1 (no amplification)

---

## Section C: NWP Delta Impact Analysis

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| Flex Ratio mechanism | iMH → CBB via HPM | Same on NWP | Direct reuse |
| `FLEX_RATIO_DISABLE` fuse | DMR fuse | NWP fuse | Verify NWP fuse name/value |
| HPM message | `DISTRIBUTE_STRAPS_CBB.DATA_OFFSET=1` | Same on NWP | Direct reuse |
| `flexcon` command | DMR platform | NWP platform config | May need NWP flexcon config |

---

## Section F: Recommendation

**Recommendation: ADOPT — flex ratio mechanism is iMH→CBB HPM, same on NWP**

Flex Ratio verification is directly applicable on NWP. Primary risk: `flexcon` platform config for NWP.

Required adaptations:
1. Verify `flexcon` works with NWP platform configuration
2. Get NWP-specific fused P1 value for test range setup
3. `FLEX_RATIO_DISABLE` fuse name on NWP (may differ slightly)

**Priority**: High — `DMR_PO`; Flex Ratio clips P1 and affects all workloads on platform
