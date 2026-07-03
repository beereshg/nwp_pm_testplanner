# Deep Analysis: ICCP — AMX License Request and Grant Flow

| Field | Value |
|-------|-------|
| **HSD ID** | 22022422262 |
| **Title** | ICCP: AMX License request and grant flow |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | Pstate Stack |
| **Sub-Feature** | ICCP — AMX (Advanced Matrix Extensions) license grant and frequency limit |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies that when a core executes **AMX** instructions (highest cdyn level), the frequency is limited to the AMX turbo ratio limit table, and `IA_PERF_LIMIT_REASONS.AVX_STATUS` bit is set. The ICCP (Intel Core Current Processor) license grant flow:
1. Core requests AMX license
2. PCode grants license
3. Core frequency limited to AMX turbo ratio table entry
4. PLR AVX status bit reflects the frequency clip

On NWP, AMX is supported (not in ZBB list), and ICCP license mechanism is the same.

**Key Justification:**
- AMX instructions supported on NWP (not in ZBB list)
- ICCP AMX license grant mechanism present on NWP
- `DMR_PO` tag: silicon validation bring-up priority
- `PMSS_NWP_READINESS_CHECK` tag: evaluated for NWP

---

## Section B: NWP-Specific Test Procedure

### Adapted Test Steps

| Step | Action | NWP Adaptation |
|------|--------|----------------|
| 1 | Configure BIOS: TurboMode = 1 (Enabled), EETurbo = 1 (Enabled) | Same BIOS knobs |
| 2 | Reboot NWP | Standard reboot |
| 3 | Verify turbo granted at baseline | `python runPmx.py -x nwp.xml -p turbo -tM 60` |
| 4 | Run AMX workload on target core | AMX instruction sequence (via turbo test plug-in) |
| 5 | Verify ICCP AMX license request issued and granted | Read ICCP license grant register |
| 6 | Verify core frequency clamped to AMX turbo ratio limit | `IA32_PERF_STATUS` per core |
| 7 | Verify `IA_PERF_LIMIT_REASONS.AVX_STATUS` set | PLR bit 18 or platform-specific bit |

### AMX License Flow

```
Core executes AMX (TMUL) instruction
    → ICCP request: AMX cdyn level
    → PCode grants AMX license
    → Frequency limited to AMX turbo ratio table
    → IA_PERF_LIMIT_REASONS.AVX_STATUS = 1 (if clipped)
```

### NWP AMX Turbo Ratio Table

```python
# NWP AMX turbo ratio limit table (PLATFORM_INFO or TURBO_RATIO_LIMIT_CORES)
try:
    amx_trl = sv.socket0.imh0.punit.ptpcioregs.ptpcioregs.amx_turbo_ratio_limit.read()
    print(f"AMX Turbo Ratio Limit: 0x{amx_trl:08X}")
except Exception as e:
    print(f"AMX TRL: {e}")

# Check ICCP license grant status per core
for cbb_idx in range(2):
    cbb = getattr(sv.socket0, f'cbb{cbb_idx}')
    try:
        iccp_status = cbb.base.punit_regs.punit_gpsb.gpsb_infvnn_crs.iccp_avx_license_status.read()
        print(f"CBB{cbb_idx} ICCP AVX license status: 0x{iccp_status:08X}")
    except Exception as e:
        print(f"CBB{cbb_idx} ICCP: {e}")
```

### NWP Pass Criteria
- AMX license requested and granted by PCode
- Core frequency ≤ AMX turbo ratio limit when AMX active
- `IA_PERF_LIMIT_REASONS.AVX_STATUS = 1` when frequency clipped by AMX limit
- Frequency restores to normal turbo when AMX instructions stop

---

## Section C: NWP Delta Impact Analysis

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| AMX support | Yes | Yes (NWP not in ZBB list) | Direct reuse |
| ICCP mechanism | DMR ICCP | NWP ICCP (same architecture) | Same verification |
| AMX turbo ratio table | DMR fuse values | NWP-specific values | Verify NWP AMX TRL fuse values |
| Script XML | `dmr.xml` | `nwp.xml` | **Required change** |

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; AMX supported on NWP**

ICCP AMX license verification is directly applicable on NWP. Script adapts via XML change.

Required adaptations:
1. `python runPmx.py -x nwp.xml -p turbo -tM 60`
2. Get NWP AMX turbo ratio limit table values from NWP HAS
3. Verify PLR AVX_STATUS bit position (same on NWP)

**Priority**: High — `DMR_PO`; AMX ICCP license grant is critical for NWP AI workload validation
