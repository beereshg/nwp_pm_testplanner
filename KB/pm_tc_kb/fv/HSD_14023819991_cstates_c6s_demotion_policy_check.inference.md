# Deep Analysis: CStates: C6S Demotion policy check

| Field | Value |
|-------|-------|
| **HSD ID** | 14023819991 |
| **Title** | CStates: C6S Demotion policy check |
| **Date** | 2026-05-28 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | Core C-States |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

C6S demotion policy governs when the PMA/Acode suppresses C6S (cache-flush C6) entry to protect MC6 budget and reduce demotion overhead. The demotion decision chain (PUnit → PMA_CR_RESOLUTION_CONTROL → Acode → uCode) is architecturally identical on NWP; only CBB and core loop bounds change. Currently blocked on DMR — likely a pre-silicon tool/environment issue that resolves on silicon.

**Key Justification:**
- C6S demotion algorithm runs in Acode (`CORE_ACODE_CR_ACODE_ALGO_VALUES0.C6_DEMOTION`) — same IP on NWP
- BIOS knobs `AcpiC2Enumeration`, `C1AutoDemotion`, `MonitorMWait` map to the same MSR 0xE2 fields on NWP
- NWP CBB count (2) and core count (48/CBB) require loop adaptation only

---

## Section B: NWP-Specific Test Procedure

### Pre-Conditions
- NWP silicon at SVOS (or VP for intent check)
- BIOS knob access via `biosknob` tool
- PythonSv/namednodes access for register verification

### Adapted Test Steps

| Step | Action | NWP Adaptation |
|------|--------|----------------|
| 1 | Set BIOS knobs for C6S as ACPI C2 | `biosknob write AcpiC2Enumeration 3` — same knob on NWP |
| 2 | Disable ACPI C3: `AcpiC3Enumeration = 0` | Same |
| 3 | Enable MonitorMWait: `MonitorMWait = 1` | Same |
| 4 | Enable C1AutoDemotion: `C1AutoDemotion = 1` | Same |
| 5 | Drive cores to C6S via workload/MWAIT 0x23 | Same MWAIT encoding on NWP |
| 6 | Read Acode demotion register on 2 NWP CBBs | Loop `range(2)` not `range(4)` |
| 7 | Verify demotion bit set/clear per policy | `CORE_ACODE_CR_ACODE_ALGO_VALUES0.C6_DEMOTION` |

### NWP Pass Criteria
- When demotion conditions met: `C6_DEMOTION=1` in Acode; uCode shows C6S demoted to C1
- When conditions not met: `C6_DEMOTION=0`; C6S entry proceeds and MSR 0x3FD increments
- No firmware hang or MCA on either CBB

---

## Section C: NWP Delta Impact Analysis

### Topology

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| CBBs | 4 | 2 | Loop over `cbb{0,1}` only |
| Cores/CBB | 32 | 48 | More cores to poll; increase per-CBB validation coverage |
| C6S flavor | Supported | Supported | No change |
| MC6 (module C6) | Supported | Supported | C6S enables MC6 on NWP equally |

---

## Section D: Key Registers & Validation Points

### Complete Register/Signal Check Table (NWP)

| Category | Register | Field | Expected | Verify On |
|----------|----------|-------|----------|-----------|
| Demotion policy | `CORE_ACODE_CR_ACODE_ALGO_VALUES0` | `C6_DEMOTION` | 1 when demoting | Per core |
| uCode cfg | `CORE_ACODE_CR_UCODE_CFG` | `WISH_ALLOW[2:0]` | 0x001 when demoted | Per core |
| PMA resolution | `PMA_CR_RESOLUTION_CONTROL` | `WISH_ALLOW` | Demote signal | Per core |
| C6 residency | MSR `0x3FD` | Full | Stops incrementing when demoted | Per core |
| BIOS knob effect | MSR `0xE2` | `C6_ENABLE` | Mirrors BIOS knob | Per socket |

### PythonSv Validation Commands (NWP)

```python
# Check C6S demotion status on NWP (2 CBBs, 48 cores each)
for cbb_idx in range(2):   # NWP has 2 CBBs
    cbb = sv.socket0.getbypath(f"cbb{cbb_idx}")
    for mod_idx in range(6):
        for core_idx in range(8):
            path = f"cbb{cbb_idx}.compute{mod_idx}.module{core_idx}"
            # Read Acode demotion register
            # sv.socket0.getbypath(path).acode_algo_values0.c6_demotion.read()
            print(f"{path}: read CORE_ACODE_CR_ACODE_ALGO_VALUES0.C6_DEMOTION")
```

---

## Section E: Risk Assessment & Open Items

| # | Risk/Open Item | Severity | Notes |
|---|----------------|----------|-------|
| 1 | **TC blocked on DMR** — environment/tool issue, not architectural | Medium | Resolve DMR blocker first; then NWP run should be straightforward |
| 2 | **AcpiC2Enumeration knob name** — may differ on NWP BIOS | Low | Verify NWP BIOS knob names match DMR; aliases common between generations |
| 3 | **Demotion trigger conditions** — may need NWP-specific traffic to trigger | Medium | Characterize workload pattern that reliably triggers C6S demotion on NWP |

---

## Section F: Recommendation

**Recommendation: ADAPT — CBB loop bounds + resolve DMR blocker**

Architecturally identical to DMR. Unblock on DMR first (environment issue), then port to NWP by updating loop bounds from `range(4)` to `range(2)` for CBB iteration. BIOS knob names and register paths are the same.

Required adaptations:
1. Resolve DMR blocker (status: blocked)
2. Update CBB loops to NWP count (2 CBBs)
3. Verify NWP BIOS knob naming for AcpiC2Enumeration

**Priority**: Medium — C6S demotion is a functional correctness gate; important for power efficiency validation
