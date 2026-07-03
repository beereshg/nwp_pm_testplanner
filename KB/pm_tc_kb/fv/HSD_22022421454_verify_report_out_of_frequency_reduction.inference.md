# Deep Analysis: [ACP] Verify Report out of Frequency Reduction Reason

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421454 |
| **Title** | [ACP] Verify Report out of Frequency Reduction Reason |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | SoC Thermal Management > ACP (Autonomous Core Perimeter) |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies that Pcode correctly propagates the Core Thermal Status bit from ACP telemetry to the Performance Limit Reason (PLR) reporting path. When a core reduces its frequency due to a thermal event, it signals via `PMSB_PCU_CR_ACP_PERF_LIMIT[THERMAL]` to Pcode. Pcode must update the PLR mailbox thermal bit and the Perf Limit Reason register visible to software. On NWP, this ACP→PLR thermal reason reporting path is supported. The test requires adapting loop bounds from DMR (4 CBBs × 32 cores) to NWP (2 CBBs × 48 cores) and updating the script config.

**Key Justification:**
- ACP Perf Limit reporting (`PMSB_PCU_CR_ACP_PERF_LIMIT[THERMAL]`) feeds PLR on NWP
- PLR thermal bit visibility via TPMI PLR mailbox exists on NWP
- NWP core count (96 total) and CBB count (2) differ from DMR; verification scope changes
- `thermalManagement.py.thermTest` adapts to NWP with topology config substitution

---

## Section B: NWP-Specific Test Procedure

### Pre-Conditions
- NWP platform with thermal stress capability (VP with DTS injection or silicon)
- PythonSv access to `sv.socket0.cbb{0,1}` PMSB and IMH TPMI registers

### Adapted Test Steps

| Step | Action | NWP Adaptation |
|------|--------|----------------|
| 1 | Run `thermalManagement.py.thermTest` with NWP config | Update to NWP topology (2 CBBs × 48 cores) |
| 2 | Trigger thermal event on a core (workload or DTS injection) | Same mechanism |
| 3 | Verify core reduces frequency due to thermal | Same; check per-core ratio limit via slow limits |
| 4 | Read `PMSB_PCU_CR_ACP_PERF_LIMIT[THERMAL]` for the affected core | Verify register is set for the hot core; loop over `range(2)` CBBs, `range(48)` cores |
| 5 | Verify PLR mailbox `THERMAL` bit (bit 3) is set at CBB TPMI | Loop over both CBBs: `cbb{0,1}.base.tpmi.plr_mailbox_interface` |
| 6 | Verify thermal event cleared → PLR clears | Same acceptance criterion |

### NWP Pass Criteria
- `PMSB_PCU_CR_ACP_PERF_LIMIT[THERMAL]` set when core ACP reduces frequency
- TPMI PLR mailbox THERMAL bit (bit 3) set on the CBB hosting the throttled core
- PLR clears within one slow-loop cycle after thermal condition resolves

---

## Section C: NWP Delta Impact Analysis

### Topology Changes

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| CBB count | 4 | 2 | PLR mailbox verified on 2 CBBs (not 4) |
| Cores per CBB | 32 | 48 | PMSB ACP_PERF_LIMIT read across 48 cores/CBB |
| Script XML | `dmr.xml` | `nwp.xml` | Direct substitution |

### PLR Bit Assignment

| PLR Bit | Meaning | NWP | Impact |
|---------|---------|-----|--------|
| Bit 3: THERMAL | Core ACP thermal throttle active | Same on NWP | No change |

---

## Section D: Key Registers & Validation Points

### Register Check Table (NWP)

| Category | Register | Field | Expected | Verify On |
|----------|----------|-------|----------|-----------|
| ACP perf limit | `PMSB_PCU_CR_ACP_PERF_LIMIT` | `THERMAL` | 1 during core thermal throttle | Per-core, both CBBs |
| PLR mailbox | `cbb{i}.base.tpmi.plr_mailbox_interface` | Bit 3 (THERMAL) | 1 during throttle | Per CBB |
| Package PLR | `PERF_LIMIT_REASONS` | `THERMAL` | 1 during throttle | Package (TPMI) |

### PythonSv Validation Commands (NWP)

```python
# Check PLR THERMAL bit on both CBBs
for cbb_idx in range(2):  # NWP has 2 CBBs
    plr = sv.socket0.getbypath(f"cbb{cbb_idx}.base.tpmi.plr_mailbox_interface").read()
    thermal_bit = (plr >> 3) & 1
    print(f"CBB{cbb_idx} PLR THERMAL bit: {thermal_bit}")

# Package-level perf limit reasons
ptpcfsms = sv.socket0.imh0.punit.ptpcfsms.ptpcfsms
pkg_plr = ptpcfsms.perf_limit_reasons.read()
print(f"Package PLR: 0x{pkg_plr:08X}")

# Per-core ACP perf limit check (spot check first core of each CBB)
for cbb_idx in range(2):
    cbb = sv.socket0.getbypath(f"cbb{cbb_idx}")
    try:
        acp_limit = cbb.getbypath("compute0.module0.pmsb_pcu_cr_acp_perf_limit").thermal.read()
        print(f"CBB{cbb_idx} core0: ACP_PERF_LIMIT.THERMAL={acp_limit}")
    except Exception as e:
        print(f"CBB{cbb_idx}: {e}")
```

---

## Section E: Risk Assessment & Open Items

| # | Risk/Open Item | Severity | Notes |
|---|----------------|----------|-------|
| 1 | **PMSB ACP_PERF_LIMIT register path** — may not be directly accessible via NWP namednodes; PLR mailbox TPMI path is the primary observable | Low | Use TPMI PLR mailbox as primary; PMSB path as secondary if accessible |
| 2 | **PLR THERMAL bit definition** — verify bit 3 definition is same on NWP PLR mailbox (not just DMR) | Low | Check NWP PM HAS PLR section |

---

## Section F: Recommendation

**Recommendation: ADAPT — topology update + PLR path confirmation needed**

This TC is straightforward on NWP — the ACP thermal→PLR reporting path exists. Primary adaptations are the CBB/core loop bounds and script config. The PLR mailbox TPMI path is the primary observable and is accessible on NWP.

Required adaptations:
1. Update `thermalManagement.py.thermTest` to NWP topology (2 CBBs × 48 cores)
2. Verify NWP PLR bit 3 = THERMAL (confirm in NWP PM HAS)
3. Update PMSB register read to use NWP namednodes path

**Priority**: Medium — PLR thermal reason reporting is important for OS-level telemetry validation
