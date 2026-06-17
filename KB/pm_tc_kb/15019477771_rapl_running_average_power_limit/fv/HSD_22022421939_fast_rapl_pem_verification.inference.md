# Deep Analysis: Fast RAPL - PEM Verification

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421939 |
| **Title** | Fast RAPL - PEM Verification |
| **Date** | 2026-05-28 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | Socket RAPL > Fast RAPL |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test validates Fast RAPL operation and verifies that the PEM (Power Excursion Monitor) bit is set correctly when Fast RAPL throttling is active. Fast RAPL is a sub-millisecond power limiting mechanism that acts faster than the standard PL1/PL2 control loop. When power exceeds the Fast RAPL threshold, the PEM bit in the CBB TPMI register is asserted, signaling that a power excursion was detected and Fast RAPL responded. The test drives the cpu_rapl PMX module to trigger Fast RAPL and then reads the PEM status register to confirm the bit is set.

**Key Justification:**
- Fast RAPL (PEM/UFS) is explicitly listed as **Supported** on NWP (not ZBB)
- PEM status is at the CBB level (`sv.socket0.cbb{idx}.base.tpmi.pem_status`) — NWP has 2 CBBs (not 4)
- DMR command `runPmx.py -x dmr.xml -p cpu_rapl` adapts to `nwp.xml`
- PMSS_NWP_READINESS_CHECK tagged — high priority for NWP bring-up

---

## Section B: NWP-Specific Test Procedure

### Pre-Conditions
- NWP silicon or VP at SVOS boot
- PMX framework with `nwp.xml`; cpu_rapl module present
- PythonSv / namednodes accessible for PEM status register read
- BIOS knobs `TurboPowerLimitLock` and `TurboPowerLimitCsrLock` **disabled**

### Adapted Test Steps

| Step | Action | NWP Adaptation |
|------|--------|----------------|
| 1 | Run cpu_rapl PMX to exercise Fast RAPL | `python runPmx.py -x nwp.xml -p cpu_rapl -tM 6 -M 3` |
| 2 | Read PEM status per CBB before running workload | `sv.socket0.cbb0.base.tpmi.pem_status.read()` and `cbb1` — NWP has 2 CBBs |
| 3 | Apply power load to exceed Fast RAPL threshold | PTU or PMX workload module |
| 4 | Read PEM status per CBB during/after workload | Confirm `pem_bit` (or equivalent field) is set |
| 5 | Verify PEM clears after power drops below threshold | Confirm bit self-clears or clears on read per spec |
| 6 | Confirm no MCA or firmware hang | Monitor nlog / SVOS console |

### Register Expected Values

| Register | Field | Pre-workload | During Fast RAPL | Notes |
|----------|-------|-------------|-----------------|-------|
| `cbb{0,1}.base.tpmi.pem_status` | `pem_excursion_bit` | 0 (cleared) | 1 (set) | Verify on both CBBs |
| `imh0.ptpcfsms.perf_limit_reasons` | `fast_rapl` | 0 | 1 | IMH-level perf limit |
| `imh0.ptpcfsms.socket_rapl_energy_status` | `total_energy` | N | N+δ (incrementing) | Confirm energy counting |

### NWP Pass Criteria
- PMX reports PASS for cpu_rapl module
- PEM status bit is set in at least one CBB during power excursion
- Bit clears correctly after excursion (per spec — sticky vs. clear-on-read)
- No firmware MCA

---

## Section C: NWP Delta Impact Analysis

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| CBBs | 4 | 2 | PEM check loop: `range(2)` not `range(4)` |
| PEM register path | `cbb{0..3}.base.tpmi.pem_status` | `cbb{0,1}.base.tpmi.pem_status` | Fewer CBBs to check |
| PMX XML | `dmr.xml` | `nwp.xml` | Mandatory substitution |
| Platform RAPL | Supported | ZBB | Not relevant to Fast RAPL test |
| Fast RAPL feature | Supported | Supported | No algorithm change |

---

## Section D: Key Registers & Validation Points

### Register Check Table (NWP)

| Category | Register | Field | Expected | Verify On |
|----------|----------|-------|----------|-----------|
| PEM status | `sv.socket0.cbb0.base.tpmi.pem_status` | `pem_excursion_bit` | Set during excursion | Per CBB |
| PEM status | `sv.socket0.cbb1.base.tpmi.pem_status` | `pem_excursion_bit` | Set during excursion | Per CBB |
| PEM control | `sv.socket0.cbb0.base.tpmi.pem_control` | `pem_enable` | 1 (enabled) | Per CBB |
| Perf limit | `sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.perf_limit_reasons` | `fast_rapl` | Set during Fast RAPL | IMH |
| Energy status | `sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.socket_rapl_energy_status` | `total_energy` | Monotone increasing | IMH |

### PythonSv Validation Commands (NWP)

```python
# Fast RAPL PEM verification on NWP (2 CBBs)
rapl = sv.socket0.imh0.punit.ptpcfsms.ptpcfsms

# Pre-workload: read PEM status on both CBBs
for cbb_idx in range(2):   # NWP has 2 CBBs
    pem = sv.socket0.getbypath(f"cbb{cbb_idx}.base.tpmi.pem_status")
    print(f"CBB{cbb_idx} PEM status (pre): 0x{pem.read():08x}")
    pem_ctrl = sv.socket0.getbypath(f"cbb{cbb_idx}.base.tpmi.pem_control")
    print(f"CBB{cbb_idx} PEM control: 0x{pem_ctrl.read():08x}")

# Read perf_limit_reasons to check Fast RAPL bit
print("perf_limit_reasons:", hex(rapl.perf_limit_reasons.read()))

# Post-workload: re-read PEM status
for cbb_idx in range(2):
    pem = sv.socket0.getbypath(f"cbb{cbb_idx}.base.tpmi.pem_status")
    print(f"CBB{cbb_idx} PEM status (post): 0x{pem.read():08x}")
```

---

## Section E: Risk Assessment & Open Items

| # | Risk/Open Item | Severity | Notes |
|---|----------------|----------|-------|
| 1 | **PEM register field name** — confirm exact field name for PEM excursion bit in `pem_status` on NWP silicon (may differ from DMR field layout) | High | Read spec or use `.show()` to discover fields |
| 2 | **PEM sticky vs. clear-on-read** — NWP PEM bit behavior (sticky? clear-on-read? SW-clear?) must be confirmed from NWP TPMI spec | Medium | Affects test step ordering |
| 3 | **nwp.xml Fast RAPL module** — confirm cpu_rapl PMX module on NWP exercises Fast RAPL path (vs. only standard PL1/PL2) | High | If not, need dedicated Fast RAPL test stimulus |

---

## Section F: Recommendation

**Recommendation: ADAPT — Substitue `nwp.xml`, update CBB loop to range(2)**

Fast RAPL and PEM are both supported on NWP. Adaptation is straightforward: replace DMR XML with NWP XML and verify PEM across 2 CBBs (not 4). The key risk is confirming exact register field names and PEM bit behavior from the NWP TPMI spec before silicon bring-up.

Required adaptations:
1. Replace `-x dmr.xml` with `-x nwp.xml`
2. PEM check loop: `for cbb_idx in range(2)` (not range(4))
3. Confirm `pem_status` field name matches NWP TPMI register layout
4. Verify PEM bit clear behavior (sticky vs. read-clear)

**Priority**: High — PMSS_NWP_READINESS_CHECK + DMR_PO tagged; p2 priority
