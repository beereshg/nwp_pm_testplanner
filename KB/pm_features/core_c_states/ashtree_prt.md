# Core C-States > AshTree PRT

> **Status**: Enriched — HW/FW/OS touchpoints + KPI & Timing added (2026-05-28)
> **Parent**: [Core C-States](core_c_states_main.md)

## Baseline (DMR)

AshTree PRT (Performance, Reliability, Timing) tests validate **TSC (Time Stamp Counter) monotonicity** across C-state and P-state transitions. The TSC must remain monotonic (never go backward) even during:

## HW Touchpoints

| IP Block | Die | Role | Key Signals / Wires | HAS Reference |
|----------|-----|------|---------------------|---------------|
| CTC (Crystal Time Counter) | CBB | Saved before C6 entry by PMA; restored by PMA on CC6 exit before uCode reads TSC; enables monotonic TSC continuity | CTC_count save/restore; PMA controls restore timing pre-reset-handler | PNC PM HAS §8.12 |
| ARAT-TTT (timer) | CBB | Wake deadline timer; validated for accurate firing after long C6 residency (AshTree long-idle test) | CORE_PMA_CR_ARAT_TTT; CTC-based comparison; no drift requirement | PNC PM HAS §8.5.3 |
| TSC (Time Stamp Counter) | CBB | Architectural monotonicity requirement: must never go backward across any C-state or P-state transition | MSR 0x10; CTC-backed; updated from residency counter on CC6 exit | IA-32 SDM |
| SCF / Fabric | CBB + IMH | For DVFS (MeshGV) cross-product: fabric frequency change must not introduce TSC discontinuity | MeshGV — not applicable on NWP | DMR SoC PM HAS |

## FW Touchpoints

| Agent | Location | Role | Key Functions / Handlers | Source |
|-------|----------|------|--------------------------|--------|
| uCode (PantherCove) | CBB core | TSC update on CC6 exit: reads CTC value restored by PMA, updates CC6 residency counter (MSR 0x3FD), ensures TSC monotonicity | CC6 exit reset handler: CTC sync wait → MSR 0x3FD update → TSC continuity; WAKEUP_INFO.RESET_TYPE check | PNC PM HAS §8.12 |
| Acode (Tensilica ACP) | CBB core perimeter | CTC save before C6 entry; CTC restore on exit (before core reset handler runs); ARAT-TTT accuracy maintained across C6 residency | CTC save/restore sequence; PMA manages CTC restore timing | PNC PM HAS §8.12 |
| PCode (CBB) | CBB | ARAT-TTT programming accuracy; no TSC-related firmware action but contributes correct ARAT-TTT deadline | CRWr ARAT-TTT; clock domain accuracy | PNC PM HAS §8.5.3 |
| BIOS / UEFI | Platform | TSC invariance guaranteed by BIOS at platform init; TSC sync across cores ensured at boot | TSC invariant CPUID enumeration; no per-C-state BIOS action | BIOS PM HAS |

## OS Interfaces

| Interface | ID / Address | Access | Description | Spec Reference |
|-----------|-------------|--------|-------------|----------------|
| MSR TSC | 0x10 | RO | Time Stamp Counter — must be monotonic; validated by AshTree PRT | IA-32 SDM |
| MSR CC6 Residency | 0x3FD | RO | Crystal cycles spent in CC6; updated on CC6 exit; used to verify no TSC gap | PNC PM HAS §8.3 |
| CORE_PMA_CR_ARAT_TTT | CR (uCode-written) | WO | Wake deadline timer; validated for accurate firing after long C6 idle | PNC PM HAS §8.5.3 |
| CPUID.15H | Leaf 0x15, EAX/EBX | RO | TSC/CTC frequency ratio; required for correct TSC → wall-clock conversion | IA-32 SDM |

## KPI & Timing

| Parameter | Value | Units | Condition / Notes | Source |
|-----------|-------|-------|-------------------|--------|
| TSC monotonicity requirement | Guaranteed | — | TSC must never go backward across C-state or P-state transitions | IA-32 SDM |
| CTC restore accuracy on CC6 exit | ± 1 crystal cycle | — | CTC value is saved pre-C6 and restored by PMA; uCode reads correct elapsed time | PNC PM HAS §8.12 |
| CC6 residency counter update | On CC6 exit | — | MSR 0x3FD updated with crystal cycles elapsed in C6 before thread resumes | PNC PM HAS §8.3 |
| ARAT-TTT firing accuracy | ≤ 1 crystal cycle | — | Wake deadline timer must fire within 1 crystal cycle of programmed value | PNC PM HAS §8.5.3 |
| Long-idle TSC validation | No drift | — | AshTree validates TSC continuity after extended C6 residency (no turbo, no DVFS) | PSS TC description |

## NWP Delta

**Ashtree PRT is supported on NWP** — same PantherCove (PNC) core as DMR; no architecture change.

### Architecture Changes
- NWP uses the same PantherCove (PNC) P-core as DMR — ACP/Acode manages PRT as on DMR
- TSC monotonicity requirement and CTC save/restore flow: unchanged
- **PkgC6 removed** on NWP — long-idle PkgC6 × PRT cross-product not applicable

### Validation Impact
- Same AshTree PRT test cases apply as DMR
- Skip PkgC6-related long-idle scenarios

 