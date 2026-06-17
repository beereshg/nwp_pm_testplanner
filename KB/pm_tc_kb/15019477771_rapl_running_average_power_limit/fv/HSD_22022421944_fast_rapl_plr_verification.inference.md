# Deep Analysis: Fast RAPL - PLR Verification

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421944 |
| **Title** | Fast RAPL - PLR Verification |
| **Date** | 2026-05-28 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | Socket RAPL > Fast RAPL |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test validates Fast RAPL operation and verifies that the PLR (Performance Limit Reason) bit associated with Fast RAPL is correctly asserted in the PLR mailbox when Fast RAPL throttling is active. When power exceeds the Fast RAPL threshold and the firmware reduces frequency, the corresponding PLR bit in the CBB TPMI PLR mailbox should be set, allowing software to distinguish Fast RAPL throttling from standard PL1/PL2 throttling. This is a critical diagnostic capability for understanding power headroom events on NWP.

**Key Justification:**
- Fast RAPL (PEM/UFS feature) is **Supported** on NWP per NWP PM feature table
- PLR (Performance Limit Reasons) mailbox at the CBB TPMI level is supported on NWP
- PLR is checked per CBB: `sv.socket0.cbb{idx}.base.tpmi.plr_mailbox_interface` — NWP has 2 CBBs
- PMSS_NWP_READINESS_CHECK + DMR_PO tagged — critical priority for NWP validation

---

## Section B: NWP-Specific Test Procedure

### Pre-Conditions
- NWP silicon or VP at SVOS boot
- PMX framework with `nwp.xml`; cpu_rapl module configured to exercise Fast RAPL
- PythonSv accessible for PLR mailbox register read
- BIOS power limit locks disabled

### Adapted Test Steps

| Step | Action | NWP Adaptation |
|------|--------|----------------|
| 1 | Read PLR mailbox baseline on both CBBs | `sv.socket0.cbb0.base.tpmi.plr_mailbox_interface.read()` and `cbb1` |
| 2 | Run cpu_rapl PMX to trigger Fast RAPL throttling | `python runPmx.py -x nwp.xml -p cpu_rapl -tM 6 -M 3` |
| 3 | During throttle: read PLR mailbox on each CBB | Confirm Fast RAPL bit is set in PLR response |
| 4 | Also read `plr_mailbox_data` for the Fast RAPL reason code | `sv.socket0.cbb{idx}.base.tpmi.plr_mailbox_data.read()` |
| 5 | Confirm PLR bit clears when power returns below Fast RAPL threshold | Verify bit is self-clearing or clears on threshold exit |
| 6 | Cross-check with `perf_limit_reasons` at IMH level | `sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.perf_limit_reasons` |

### Register Expected Values

| Register | Field | Idle State | During Fast RAPL | Notes |
|----------|-------|-----------|-----------------|-------|
| `cbb{idx}.base.tpmi.plr_mailbox_interface` | fast_rapl bit | 0 | 1 | Per CBB |
| `cbb{idx}.base.tpmi.plr_mailbox_data` | reason_code | 0 | Fast RAPL code | Check NWP PLR spec for code |
| `imh0.ptpcfsms.perf_limit_reasons` | rapl / fast_rapl | 0 | 1 | IMH-level cross-check |

### NWP Pass Criteria
- PMX cpu_rapl reports PASS
- PLR mailbox on at least one CBB shows Fast RAPL throttle reason during workload
- PLR clears when throttle exits
- No firmware MCA

---

## Section C: NWP Delta Impact Analysis

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| CBBs | 4 | 2 | PLR check loop: `range(2)` not `range(4)` |
| PLR path | `cbb{0..3}.base.tpmi.plr_mailbox_interface` | `cbb{0,1}.base.tpmi.plr_mailbox_interface` | Fewer CBBs |
| PMX XML | `dmr.xml` | `nwp.xml` | Mandatory |
| Fast RAPL PLR bit encoding | DMR-specific code | NWP may differ | Confirm from NWP TPMI/PLR spec |

---

## Section D: Key Registers & Validation Points

### Register Check Table (NWP)

| Category | Register | Field | Expected | Verify On |
|----------|----------|-------|----------|-----------|
| PLR mailbox | `sv.socket0.cbb0.base.tpmi.plr_mailbox_interface` | `fast_rapl` | Set during Fast RAPL | CBB0 |
| PLR mailbox | `sv.socket0.cbb1.base.tpmi.plr_mailbox_interface` | `fast_rapl` | Set during Fast RAPL | CBB1 |
| PLR data | `sv.socket0.cbb0.base.tpmi.plr_mailbox_data` | `reason_code` | Fast RAPL code | CBB0 |
| Perf limit | `sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.perf_limit_reasons` | `fast_rapl` | Set | IMH |

### PythonSv Validation Commands (NWP)

```python
# Fast RAPL PLR verification on NWP (2 CBBs)
# Read PLR mailbox per CBB
for cbb_idx in range(2):   # NWP has 2 CBBs
    plr_if = sv.socket0.getbypath(f"cbb{cbb_idx}.base.tpmi.plr_mailbox_interface")
    plr_data = sv.socket0.getbypath(f"cbb{cbb_idx}.base.tpmi.plr_mailbox_data")
    print(f"CBB{cbb_idx} PLR interface: 0x{plr_if.read():08x}")
    print(f"CBB{cbb_idx} PLR data:      0x{plr_data.read():08x}")

# IMH-level perf limit reasons
rapl = sv.socket0.imh0.punit.ptpcfsms.ptpcfsms
print("perf_limit_reasons:", hex(rapl.perf_limit_reasons.read()))
print("energy_status:", hex(rapl.socket_rapl_energy_status.read()))
```

---

## Section E: Risk Assessment & Open Items

| # | Risk/Open Item | Severity | Notes |
|---|----------------|----------|-------|
| 1 | **PLR bit encoding for Fast RAPL** — exact bit position in `plr_mailbox_interface` for Fast RAPL may differ between DMR and NWP | High | Read from NWP TPMI PLR spec before writing test assertions |
| 2 | **PLR mailbox access protocol** — PLR mailbox may require a specific read protocol (write address then read data); confirm NWP mailbox access sequence | Medium | Use `.show()` first to understand register structure |
| 3 | **Fast RAPL trigger** — cpu_rapl PMX must exercise the Fast RAPL path, not just PL1/PL2 | Medium | Confirm PMX module configuration exercises sub-ms power limiting |

---

## Section F: Recommendation

**Recommendation: ADAPT — Update XML, loop CBBs over range(2), confirm PLR bit encoding**

Fast RAPL PLR verification is fully valid on NWP. The CBB-level PLR mailbox architecture is the same; only the CBB count (2 vs 4) and XML change. The PLR bit encoding for Fast RAPL should be confirmed from NWP TPMI spec before writing hard-coded assertions.

Required adaptations:
1. Replace `-x dmr.xml` with `-x nwp.xml`
2. PLR check loop: `for cbb_idx in range(2)`
3. Confirm Fast RAPL PLR bit field name and encoding from NWP spec
4. Verify PLR mailbox read protocol on NWP matches DMR

**Priority**: High — PMSS_NWP_READINESS_CHECK + DMR_PO; p2 priority
