# Core C-States > Demotion

> **Status**: Enriched — HW/FW/OS touchpoints + KPI & Timing added (2026-05-28)
> **Parent**: [Core C-States](core_c_states_main.md)

## Baseline (DMR)

C6 demotion prevents the core from entering C6 when conditions suggest the exit latency cost outweighs the power savings. The demotion decision is a **three-way merge** between PUnit, Acode, and MSR 0xE2 (SW control).

## HW Touchpoints

| IP Block | Die | Role | Key Signals / Wires | HAS Reference |
|----------|-----|------|---------------------|---------------|
| ACP / PMA | CBB | Hosts RESOLUTION_CONTROL.WISH_ALLOW; merges PUnit + Acode demotion inputs; exposes merged result to uCode via CORE_ACODE_CR_UCODE_CFG | CORE_PMA_CR_RESOLUTION_CONTROL, CORE_ACODE_CR_UCODE_CFG.WISH_ALLOW | PNC PM HAS §8.6 |
| SEB (Sideband) | CBB | Carries C6 demotion indication from PUnit to Nucleolus-Core; carries MSR 0xE2 reflection to RESOLUTION_CONTROL | SEB demotion wire; MSR 0xE2 reflection | PNC PM HAS §8.6.5 |
| CTC / Crystal Clock | CBB | Provides timing reference for TTT-based break-event window analysis used in demotion decisions | CTC_count; minTTT calculation before C6 entry | PNC PM HAS §8.12 |

## FW Touchpoints

| Agent | Location | Role | Key Functions / Handlers | Source |
|-------|----------|------|--------------------------|--------|
| Acode (Tensilica ACP) | CBB core perimeter | Generates C6_DEMOTION bit in CORE_ACODE_CR_ACODE_ALGO_VALUES0; feeds into PMA merge logic; overrides PUnit WISH_ALLOW when demotion needed | ACODE_ALGO_VALUES0.C6_DEMOTION; ACP capability vector bit 5 | PNC PM HAS §8.6.2 |
| uCode (PantherCove) | CBB core | Reads merged WISH_ALLOW from CORE_ACODE_CR_UCODE_CFG before every MWAIT/HLT; uses it to determine actual C-state target | Read UCODE_CFG.WISH_ALLOW before each C-state entry; apply demotion result | PNC PM HAS §8.6.3 |
| PCode (CBB) | CBB | Computes RESOLUTION_CONTROL.WISH_ALLOW from workload characterization + MSR 0xE2; sends C6 demotion via SEB | RESOLUTION_CONTROL.WISH_ALLOW programming; MSR 0xE2 → RESOLUTION_CONTROL reflection | PNC PM HAS §8.6.1; §8.6.5 |
| BIOS / UEFI | Platform | Configures MSR 0xE2 at boot with C6/C1 demotion/undemotion enables per platform policy | MSR 0xE2 programming at boot; C3_DEM_EN, C1_DEM_EN, UNDEMOTION enables | BIOS PM HAS |

## OS Interfaces

| Interface | ID / Address | Access | Description | Spec Reference |
|-----------|-------------|--------|-------------|----------------|
| MSR CLOCK_CST_CONFIG_CONTROL | 0xE2 | RW | SW C6 demotion control: bit[26] C1_DEM_EN, bit[25] C3_DEM_EN, bit[28] C1_UNDEM_EN, bit[27] C3_UNDEM_EN, bit[10] IO_MWAIT_REDIR | PNC PM HAS §8.6.5 |
| CORE_ACODE_CR_UCODE_CFG.WISH_ALLOW | CR (internal) | RO to OS | Merged demotion result read by uCode — final effective C-state cap | PNC PM HAS §8.6.3 |
| CORE_PMA_CR_RESOLUTION_CONTROL.WISH_ALLOW | CR (PUnit-written) | RO to OS | PUnit-computed WISH_ALLOW (includes MSR 0xE2 reflection) | PNC PM HAS §8.6.1 |
| CORE_ACODE_CR_ACODE_ALGO_VALUES0.C6_DEMOTION | CR (Acode-written) | RO to OS | Acode demotion recommendation: 1 = demote to C1 | PNC PM HAS §8.6.2 |

## KPI & Timing

| Parameter | Value | Units | Condition / Notes | Source |
|-----------|-------|-------|-------------------|--------|
| WISH_ALLOW evaluation frequency | Per-MWAIT | — | uCode reads merged WISH_ALLOW before every C-state entry attempt | PNC PM HAS §8.6.3 |
| C6_DEMOTION assert → effect | Immediate | — | Acode setting ACODE_ALGO_VALUES0.C6_DEMOTION=1 takes effect on next MWAIT | PNC PM HAS §8.6.2 |
| WISH_ALLOW C1 code | 0001 | — | Clock-gate only; no cache flush, no PLL shutdown, no voltage reduction | PNC PM HAS §8.6.4 |
| WISH_ALLOW C6 code | 0011 | — | Power-gate; flush local cache, save C6SRAM; Vinf stays on (retention) | PNC PM HAS §8.6.4 |
| WISH_ALLOW C10 code | 0111 | — | C6 + flush shared cache + Vinf can be powered down; state to DRAM | PNC PM HAS §8.6.4 |
| Undemotion latency | Next MWAIT | — | No explicit undemotion event; new WISH_ALLOW takes effect on next C-state entry | PNC PM HAS §8.6.5 |

## NWP Delta

**C-state demotion is supported on NWP** — same architecture as DMR (PNC core; Acode manages C6 demotion).

### Architecture Changes
- NWP uses the same PantherCove (PNC) core as DMR — **Acode (ACP) still implements C6 demotion**
- `CORE_PMA_CR_RESOLUTION_CONTROL.WISH_ALLOW` merge logic (PUnit + Acode inputs): unchanged
- MSR 0xE2 (`CLK_CST_CONFIG_CONTROL`) demotion bits apply as on DMR
- **No PkgC auto-demotion** (PkgC6 removed on NWP)

### Validation Impact
- Same C6→C1 demotion test scenarios as DMR
- Verify `C1_DEMOTION_ENABLE` and `UNDEMOTION_ENABLE` bits (MSR 0xE2) work correctly on NWP
- Skip PkgC auto-demotion tests (PkgC6 removed)

## Legacy (Human-Curated Reference)

### Architecture Summary

C6 demotion prevents the core from entering C6 when conditions suggest the exit latency cost outweighs the power savings. The demotion decision is a **three-way merge** between PUnit, Acode, and MSR 0xE2 (SW control).

#### Demotion Decision Chain *(confirmed: [PNC PM HAS §8.6](c:\github\NWP\PNC%20PM%20HAS%200.5_text.txt))*

```
PUnit Algorithm + MSR 0xE2 guidance
       │
       ▼
PMA_CR_RESOLUTION_CONTROL.WISH_ALLOW  ──┐
                                         │ PMA merges
Acode CORE_ACODE_CR_ACODE_ALGO_VALUES0  ─┤
           .C6_DEMOTION                   │
                                         ▼
                              CORE_ACODE_CR_UCODE_CFG.WISH_ALLOW[2:0]
                                         │
                                         ▼
                              uCode reads before C-state entry
```

#### Merge Logic *(confirmed: [PNC PM HAS §8.6.3](c:\github\NWP\PNC%20PM%20HAS%200.5_text.txt))*

```
if (Acode C6_DEMOTION == 1):
    UCODE_CFG.WISH_ALLOW = 0x001  // Demote to C1
else:
    UCODE_CFG.WISH_ALLOW = RESOLUTION_CONTROL.WISH_ALLOW  // PUnit controls
```

#### WISH_ALLOW Encoding *(confirmed: [PNC PM HAS §8.6.4](c:\github\NWP\PNC%20PM%20HAS%200.5_text.txt))*

| Code | State | Meaning |
|------|-------|---------|
| 0001 | C1 | Clock gate only. No cache flush, no PLL shutdown, no voltage reduction |
| 0010 | C3 | Flush local cache, shutdown clock, reduce voltage to retention. No power-gate |
| 0011 | C6 | Power-gate allowed. Flush local cache, save state to C6SRAM. Vinf stays on (retention) |
| 0100 | C7 | C6 + flush shared (cross-module) cache. Vinf stays on |
| 0101–0110 | C8–C9 | Same as C7 |
| 0111 | C10 | C6 + flush shared cache + Vinf can be powered down. Save state to DRAM |

#### MSR 0xE2 (CLOCK_CST_CONFIG_CONTROL) *(confirmed: [PNC PM HAS §8.6.5](c:\github\NWP\PNC%20PM%20HAS%200.5_text.txt))*

SW-accessible MSR that enables/disables C6 demotion. In LNC/PNC, some bits are reflected via `RESOLUTION_CONTROL` CR. PUnit may disable its own C6 demotion algorithm, but MSR 0xE2 is still reflected in RESOLUTION_CONTROL bits, so PMA always uses PUnit input.

#### Undemotion

When demotion conditions no longer apply (e.g., MSR 0xE2 re-enables C6), the next MWAIT will use the new WISH_ALLOW value. There is no explicit "undemotion" event — uCode simply reads the updated WISH_ALLOW before each C-state entry.

#### C6A Demotion Policy

C6A (autonomous) demotion policy may differ from standard C6 because C6A does not release electrical budget. The exact policy for C6A demotion requires clarification (noted in TC 14023715625).

### Key Registers & Interfaces

| Register | Description | Source |
|----------|-------------|--------|
| MSR `0xE2` | CLOCK_CST_CONFIG_CONTROL — SW C6 demotion control | ✅ PNC PM HAS §8.6.5 |
| `PMA_CR_RESOLUTION_CONTROL.WISH_ALLOW` | PUnit-computed demotion (includes MSR 0xE2) | ✅ PNC PM HAS §8.6.1 |
| `CORE_ACODE_CR_ACODE_ALGO_VALUES0.C6_DEMOTION` | Acode demotion recommendation (1=demote to C1) | ✅ PNC PM HAS §8.6.2 |
| `CORE_ACODE_CR_UCODE_CFG.WISH_ALLOW` | Merged result read by uCode — final demotion control | ✅ PNC PM HAS §8.6.3 |
