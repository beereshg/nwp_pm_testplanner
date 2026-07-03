# Deep Analysis: [Thermal Reporting] Verify CORE_PERF_LIMIT_REASONS

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421640 |
| **Title** | [Thermal Reporting] Verify CORE_PERF_LIMIT_REASONS |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | SoC Thermal Management > Thermal Reporting |
| **Sub-Feature** | CORE_PERF_LIMIT_REASONS (MSR 0x64F) |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies the **CORE_PERF_LIMIT_REASONS** register (MSR 0x64F, address `0x64f`), which reports per-core performance limit reasons including thermal throttle, PROCHOT, and VR_HOT events. The TC notes it is **covered by 3 existing scripts** (emttm, prochot, and vr_hot TCs with PLR check) — there is no dedicated command for this TC; it is a composite verification. On NWP, the same MSR exists. NWP is non-SMT (single thread per core), so the PLR is read per physical core (not per logical thread). Primary adaptation: scope to NWP 96-core topology.

**Key Justification:**
- `CORE_PERF_LIMIT_REASONS` MSR 0x64F is present on NWP (x86 architectural)
- Coverage provided by existing test scripts (emttm, prochot, vr_hot TCs)
- `DMR_PO` tag: silicon validation bring-up priority
- NWP non-SMT: 1 thread per core (96 cores, 2 CBBs × 48 cores)

---

## Section B: NWP-Specific Test Procedure

### Pre-Conditions
- NWP silicon with cores active
- Tests 22022421444 (EMTTM), 22022421484 (PROCHOT), and VR_HOT TC already running

### Key Register Fields

| Bits | Field | Description | NWP |
|------|-------|-------------|-----|
| 0 | `PROCHOT` | Frequency reduced due to PROCHOT assertion | Same |
| 1 | `THERMAL` | Frequency reduced due to thermal throttle (TM1/TM2) | Same |
| 4 | `POWER_LIMIT1` | Frequency reduced due to Package PL1 | Same |
| 5 | `POWER_LIMIT2` | Frequency reduced due to Package PL2 | Same |
| 8 | `CURRENT_LIMIT` | Frequency reduced due to current limit | Same |
| 9 | `CROSS_DOMAIN_LIMIT` | Frequency reduced due to cross-domain limit | Same |
| 12 | `VR_THERM_ALERT` | Frequency reduced due to VR thermal alert | Same |
| 13 | `VR_VOLTAGE_DROOP` | Frequency reduced due to VR voltage droop | Same |
| 21 | `RAMP_LIMIT` | Frequency limited during ramp transitions | Same |

### Adapted Test Steps

| Step | Action | NWP Adaptation |
|------|--------|----------------|
| 1 | Verify PROCHOT PLR bit via PROCHOT TC (22022421484) | Check `CORE_PERF_LIMIT_REASONS.PROCHOT` = 1 during assertion |
| 2 | Verify THERMAL PLR bit via EMTTM TC (22022421444) | Check `CORE_PERF_LIMIT_REASONS.THERMAL` = 1 during throttle |
| 3 | Verify VR_THERM_ALERT PLR bit via VR_HOT TC | Check VR hot event updates PLR |
| 4 | Read per-core PLR on NWP (96 cores total) | Loop over `cbb0/cbb1`, 48 cores each |
| 5 | Verify sticky log bits persist after event clears | Same |

### NWP Core PLR Read

```python
# NWP: 2 CBBs × 48 cores = 96 physical cores (no SMT)
for cbb_idx in range(2):
    cbb = getattr(sv.socket0, f'cbb{cbb_idx}')
    for compute_idx in range(4):
        for module_idx in range(12):  # 48 cores = 4 computes × 12 modules
            try:
                # Read PLR for this core
                plr = cbb.getbypath(
                    f"compute[{compute_idx}].module[{module_idx}].core0.pcu_cr_perf_limit_reasons"
                ).read()
                if plr != 0:
                    print(f"CBB{cbb_idx} C{compute_idx} M{module_idx} PLR: 0x{plr:08X}")
            except Exception:
                pass
```

### NWP Pass Criteria
- Each PLR bit correctly set during the corresponding throttle event
- PLR sticky log bits set and cleared by SW write
- No unexpected PLR bits set in baseline (no-load) condition

---

## Section C: NWP Delta Impact Analysis

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| MSR 0x64F | Per-logical-thread (2 threads/core) | Per-physical-core (1 thread/core, non-SMT) | Loop count differs; same register |
| Core count | 4 CBBs × 32 cores × 2 threads | 2 CBBs × 48 cores × 1 thread | 192 DMR threads → 96 NWP cores |
| Coverage source | 3 existing scripts | Same 3 scripts adapted for NWP | Scripts must be adapted (emttm, prochot, vr_hot) |

---

## Section F: Recommendation

**Recommendation: ADOPT — coverage provided by existing NWP-adapted scripts**

CORE_PERF_LIMIT_REASONS is an architectural MSR present on NWP. Coverage comes from emttm, prochot, and vr_hot TCs when adapted for NWP. No dedicated script needed.

Required adaptations:
1. Ensure emttm (22022421444), prochot (22022421484), and VR_HOT TCs check `CORE_PERF_LIMIT_REASONS`
2. Update per-core loop: 2 CBBs × 48 cores (not 4 CBBs × 32 × 2 threads)
3. NWP non-SMT: read per-physical-core only (no thread index)

**Priority**: Medium — DMR_PO; PLR reporting is a key thermal throttle observability check
