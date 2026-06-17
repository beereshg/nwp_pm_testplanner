# Core C-States > PLR

> **Status**: Enriched — HW/FW/OS touchpoints + KPI & Timing added (2026-05-28)
> **Parent**: [Core C-States](core_c_states_main.md)

## Baseline (DMR)

Performance Limit Reasons (PLR) tracks why a core is not running at its maximum frequency. During C-state transitions, PLR status registers reflect whether C-state residency is the limiting factor. PLR is reported via **TPMI** interface and specific MSRs.

## HW Touchpoints

| IP Block | Die | Role | Key Signals / Wires | HAS Reference |
|----------|-----|------|---------------------|---------------|
| PCode internal (CBB) | CBB | Maintains 67 PLR report entries (32 CCP coarse + 32 CCP fine-grain + ring + die); aggregates limit reasons per slow-loop | PLR report registers; TPMI write path | PCode source plr.h |
| TPMI (Topology-Aware PM Interface) | IMH | PLR registers written by PCode CBB via TPMI opcode; read by OS via TPMI interface; IMH-side PLR init runs but is disabled | TPMI PLR opcode; OOBMSM bridge | PLR HAS (GNR) |
| OOBMSM | IMH | Bridges TPMI accesses between OS software and PCode/PrimeCode firmware registers | TPMI read/write path via OOBMSM | DMR SoC PM HAS |

## FW Touchpoints

| Agent | Location | Role | Key Functions / Handlers | Source |
|-------|----------|------|--------------------------|--------|
| PCode (CBB) | CBB | Primary PLR producer: updates 67 TPMI PLR report entries each slow-loop; encodes active limit reasons | plr.h PLR enum definitions; slow-loop PLR update; TPMI write per slow-loop | PCode source plr.h |
| PrimeCode (IMH) | IMH | IMH PLR TPMI init runs at boot but report fields are not populated (IMH PLR ZBB on current DUTs) | perf_reasons_common.cpp IMH PLR init; ZBB status | PrimeCode perf_reasons_common.cpp |
| BIOS / UEFI | Platform | No BIOS PLR action — TPMI is a post-boot OS interface; BIOS enables OOBMSM for TPMI access | OOBMSM enable; TPMI interface exposure | BIOS PM HAS |

## OS Interfaces

| Interface | ID / Address | Access | Description | Spec Reference |
|-----------|-------------|--------|-------------|----------------|
| TPMI PLR Interface | TPMI opcode (IMH MMIO) | RO | OS reads PLR report from TPMI; contains 67 limit reason entries updated each PCode slow-loop | PLR HAS (GNR); DMR SoC PM HAS |
| intel-speed-select (ISS) tool | Linux sysfs | RO | Reads PLR via TPMI; reports active performance limit reason categories to userspace | Linux kernel ISS driver |
| turbostat | Linux utility | RO | Displays PLR bit field decoded names alongside C-state residency counters | Linux perf tooling |
| MSR PERF_STATUS | 0x198 | RO | P-state actuals; compared with PLR to distinguish C-state vs P-state limits | IA-32 SDM |

## KPI & Timing

| Parameter | Value | Units | Condition / Notes | Source |
|-----------|-------|-------|-------------------|--------|
| PLR reports per CBB | 67 | count | 32 CCP coarse + 32 CCP fine-grain + ring + die level report entries | PCode source plr.h |
| PLR update rate | Per slow-loop | — | PCode updates TPMI PLR registers each slow-loop iteration (≈1–2 ms period) | PCode source |
| IMH PLR status | Disabled (ZBB) | — | PLR TPMI init runs on IMH but report fields are not populated | PrimeCode perf_reasons_common.cpp |
| PLR during C6 | No active limit | — | Core intentionally idle; PLR should not show a performance limit during C6 residency | C-states + PLR interaction |
| PLR C-state exit observation | Brief limit | — | PLR may briefly show a performance limit during C6 exit until core reaches target P-state | PSS TC description |

## NWP Delta

**PLR (Performance Limit Reasons) for C-states is supported on NWP** — same PNC core; PCode CBB manages PLR as on DMR.

### Architecture Changes
- NWP uses the same PantherCove (PNC) core as DMR — **PCode CBB manages PLR CRs** as on DMR
- `CORE_PERF_LIMIT_REASONS` and `RING_PERF_LIMIT_REASONS` reporting: same agent (PCode CBB), unchanged
- **No PkgC6-related PLR bits** (PkgC6 removed on NWP)

### Validation Impact
- Same PLR test scenarios as DMR (same PCode CBB flow)
- Skip PkgC6-related PLR tests (PkgC6 removed)
- Verify PLR observability for C1, C6, MC6 transitions on NWP
