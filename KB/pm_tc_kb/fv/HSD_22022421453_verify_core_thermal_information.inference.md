# Deep Analysis: [ACP] Verify Core Thermal Information

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421453 |
| **Title** | [ACP] Verify Core Thermal Information |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | SoC Thermal Management > ACP (Autonomous Core Perimeter) |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test case verifies that Pcode correctly receives and processes Core thermal information from the ACP subsystem via the sideband interface. Specifically, Core EMTTM exposes the maximum allowed operating ratio to Pcode through `IO_ACODE_ALGO_VALUES1[MAX_ALLOWED_RATIO]`, and Pcode must reflect this as the core frequency limit in the slow-limits path. On NWP, this ACP→Pcode thermal information interface is supported. The test requires adapting for NWP's 2-CBB topology (4 CBBs on DMR) and 48 cores per CBB (32 on DMR).

**Key Justification:**
- ACP `IO_ACODE_ALGO_VALUES1[MAX_ALLOWED_RATIO]` sideband interface to Pcode is present on NWP
- Pcode slow-limits path reflecting core EMTTM limit is the same on NWP
- NWP has 48 cores per CBB (96 total across 2 CBBs); verification scope changes from DMR's 4×32 layout
- `thermalManagement.py` test driver adapts to NWP with config substitution

---

## Section B: NWP-Specific Test Procedure

### Pre-Conditions
- NWP platform; PythonSv access to `sv.socket0.cbb{0,1}` and IMH punit registers
- `thermalManagement.py.thermTest` available for NWP config
- Thermal load generator available (or VP thermal injection)

### Adapted Test Steps

| Step | Action | NWP Adaptation |
|------|--------|----------------|
| 1 | Run `thermalManagement.py.thermTest` with NWP config | Substitute NWP config; scope CBBs to `range(2)` |
| 2 | Read `IO_ACODE_ALGO_VALUES1[MAX_ALLOWED_RATIO]` for each core | Loop over 2 CBBs × 48 cores (DMR: 4 × 32) |
| 3 | Verify Pcode reads the per-core max_allowed_ratio via ACP sideband | Same verification — observe CBB PCode slow-limits PMA_CR |
| 4 | Apply thermal stress to push core EMTTM to throttle | Same; use NWP workload generator |
| 5 | Verify Pcode reflects the ACP-reported limit as the core frequency ceiling in slow-limits | Same acceptance criterion |
| 6 | Verify when thermal clears, MAX_ALLOWED_RATIO returns to nominal | Same |

### NWP Pass Criteria
- `IO_ACODE_ALGO_VALUES1[MAX_ALLOWED_RATIO]` reflects core EMTTM PID output per core
- Pcode consumes MAX_ALLOWED_RATIO and uses it as the core slow-limits frequency ceiling
- Pcode slow-limits update within one slow-loop cycle (~1ms) of ACP change

---

## Section C: NWP Delta Impact Analysis

### Topology Changes

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| CBB count | 4 | 2 | Monitoring scope: `range(2)` |
| Cores per CBB | 32 | 48 | Inner loop: `range(48)` |
| ACP interface | Per-core SB from ACP to Pcode | Same | No change |

### Data Path

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| `MAX_ALLOWED_RATIO` sideband | Via ACP SB → CBB PCode | Same path on NWP | No adaptation needed |
| Slow-limits PMA_CR update | Per-CCP from Pcode | Same | No adaptation needed |

---

## Section D: Key Registers & Validation Points

### Register Check Table (NWP)

| Category | Register | Field | Expected | Verify On |
|----------|----------|-------|----------|-----------|
| ACP output | `IO_ACODE_ALGO_VALUES1` | `MAX_ALLOWED_RATIO` | Nominal ratio or throttle limit | Per-core, both CBBs |
| Slow limits | CBB Pcode slow-limits PMA_CR | Core ratio ceiling | == MAX_ALLOWED_RATIO | Per-core |
| PLR | TPMI PLR mailbox | `THERMAL[bit 3]` | Set when throttle active | Per CBB |

### PythonSv Validation Commands (NWP)

```python
# Read MAX_ALLOWED_RATIO from all NWP cores
for cbb_idx in range(2):  # NWP has 2 CBBs
    cbb = sv.socket0.getbypath(f"cbb{cbb_idx}")
    for core_idx in range(48):  # NWP has 48 cores per CBB
        try:
            max_ratio = cbb.getbypath(
                f"compute{core_idx // 8}.module{core_idx % 8}.io_acode_algo_values1"
            ).max_allowed_ratio.read()
            print(f"CBB{cbb_idx} core{core_idx}: MAX_ALLOWED_RATIO={max_ratio}")
        except Exception as e:
            pass  # Some cores may not expose this via namednodes directly

# Check package slow limits via TPMI PMT
ptpcfsms = sv.socket0.imh0.punit.ptpcfsms.ptpcfsms
print("Perf limit reasons:", hex(ptpcfsms.perf_limit_reasons.read()))
```

---

## Section E: Risk Assessment & Open Items

| # | Risk/Open Item | Severity | Notes |
|---|----------------|----------|-------|
| 1 | **`IO_ACODE_ALGO_VALUES1` accessibility via namednodes** — this is an Acode IO register; may not be directly accessible via PythonSv namednodes (may require Acode sideband read) | Medium | Check NWP CBB namednodes; alternative: use thermalManagement.py which handles this internally |
| 2 | **VP thermal injection** — if running on VP, requires a mechanism to inject DTS temperatures to trigger core EMTTM action | Low | VP thermal injection support must be confirmed for NWP |

---

## Section F: Recommendation

**Recommendation: ADAPT — topology update + register access verification needed**

The core thermal information interface is architecturally the same on NWP. Primary adaptations: update CBB/core loop bounds (4×32 → 2×48) and verify that `IO_ACODE_ALGO_VALUES1` is accessible via the NWP PythonSv namednodes hierarchy (it may require an Acode sideband read path rather than direct CR access).

Required adaptations:
1. Update `thermalManagement.py.thermTest` config to NWP topology
2. Adjust verification loops: 2 CBBs × 48 cores
3. Confirm `IO_ACODE_ALGO_VALUES1` namednodes path on NWP

**Priority**: Medium — Core thermal info reception is implicit in EMTTM functionality; covered by related throttle-verification TCs
