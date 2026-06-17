# Core C-States > Fast C1E

> **Status**: Enriched — HW/FW/OS touchpoints + KPI & Timing added (2026-05-28)
> **Parent**: [Core C-States](core_c_states_main.md)

## Baseline (DMR)

C1E (C1 Enhanced) drops core voltage and frequency to a **minimum VCC operating point** (LFM Work Point) while the core is in C1 idle. This saves power without power-gating the core. PNC introduces **three distinct C1E mechanisms**:

## HW Touchpoints

| IP Block | Die | Role | Key Signals / Wires | HAS Reference |
|----------|-----|------|---------------------|---------------|
| ACP / PMA | CBB | Runs Fast C1E FSM: detects MC1E condition, applies pre-populated LFM WP locally without PUnit; handles statistical HW C1E promotion (8-entry sliding window) | ~CoreActive monitor; cfcclk partial gate; C1E WP request | PNC PM HAS §8.10 |
| FIVR | CBB | Drops to LFM voltage on C1E entry (fast GV-down); restores on exit; abort possible after GV-down but before voltage applied | VCCcore → LFM_VCC; fast GV-down signal; abort point after GV-down | PNC PM HAS §8.10.5 |
| PLL (per module) | CBB (DCM) | Reduces frequency to LFM on C1E entry for the whole DCM (shared PLL per module, not per-core) | PLL frequency request from PMA; module-level scope | PNC PM HAS §8.10 |
| CTC (incidency counter) | CBB | Measures C1 residency per window (4 µs granularity); feeds 8-entry sliding window for HW C1E promotion decision | CTC count per C1 window; CORE_PMA_CR_CONFIG_0 limit register | PNC PM HAS §8.10.5 |

## FW Touchpoints

| Agent | Location | Role | Key Functions / Handlers | Source |
|-------|----------|------|--------------------------|--------|
| Acode (Tensilica ACP) | CBB core perimeter | Runs Fast C1E FSM and HW C1E promotion algorithm; calculates LFM WP; manages hysteresis timer; applies C1E voltage/frequency locally | C1E FSM states (detect MC1E, check hysteresis, apply WP, abort); 8-entry incidency buffer management | PNC PM HAS §8.10 |
| PCode (CBB) | CBB | Slow C1E path: detects C1E condition after 64–250 µs; propagates WISH_ALLOW with C1E WP; maintains C1E enable state from MSR 0x1FC | Slow C1E detection; WP propagation; POWER_CTL MSR 0x1FC handling | PNC PM HAS §8.10.3 |
| uCode (PantherCove) | CBB core | Issues MWAIT sub-state 1 (C1E / lose VR) when OS requests explicit C1E; reads CORE_PMA_CR_CONFIG_0 C1E enable bit before entry | MWAIT EAX sub-state 1 dispatch; C1E enable check; WISH_ALLOW read | PNC PM HAS §8.5.4; §8.10 |
| BIOS / UEFI | Platform | Programs MSR 0x1FC (POWER_CTL.C1E_ENABLE) at boot; programs Fast C1E BIOS knob | control_c1e.enable BIOS knob; MSR 0x1FC programming | BIOS PM HAS |

## OS Interfaces

| Interface | ID / Address | Access | Description | Spec Reference |
|-----------|-------------|--------|-------------|----------------|
| MWAIT sub-state 1 (explicit C1E) | CPU instruction, EAX[7:4]=0x0, EAX[3:0]=1 | W | Explicit OS request for C1E (lose VR sub-state); PMA applies Fast C1E WP locally | IA-32 SDM; PNC PM HAS §8.1.2 |
| MSR POWER_CTL | 0x1FC | RW | bit[0] C1E_ENABLE — enables C1→C1E promotion; propagated by PUnit to all PMAs | PNC PM HAS §8.10 |
| CORE_PMA_CR_CONFIG_0 | CR (internal) | RO to OS | C1E enable bit read by uCode before C1E entry; C1 incidency limit register | PNC PM HAS §8.5.4 |
| MSR CC1 Residency | 0x778 | RO | Crystal cycles in CC1 (includes C1E — no distinction between C1 and C1E) | PNC PM HAS §8.3 |
| CORE_ACODE_CR_UCODE_CFG.WISH_ALLOW | CR (Acode-written) | RO to OS | Contains C1E demotion result from PUnit+Acode merge (C1E appears as WISH_ALLOW=0001) | PNC PM HAS §8.6 |

## KPI & Timing

| Parameter | Value | Units | Condition / Notes | Source |
|-----------|-------|-------|-------------------|--------|
| Slow C1E entry delay | 64–250 | µs | PUnit detects C1E condition → waits before reducing fmax (legacy path) | PNC PM HAS §8.10.3 |
| Fast C1E exit to first instruction (server) | ~2 | µs | High-voltage LFM WP; VR already at adequate level; no ramp delay | PNC PM HAS §8.10.2 |
| HW C1E promotion window | 8 entries | — | Sliding buffer of C1 incidency counts; sum ≥ 8 triggers C1→C1E promotion | PNC PM HAS §8.10.5 |
| HW C1E C1 limit granularity | 4 | µs | Time resolution per C1 incidency counter entry (4-bit saturating counter, max 60 µs) | PNC PM HAS §8.10.5 |
| HW C1E hysteresis range | 0–32 | µs | Post-C1E-exit hold-off before next statistical promotion (6 discrete encodings) | PNC PM HAS §8.10.5 |
| Fast C1E abort window | After GV-down, before voltage applied | — | Last chance abort point in Fast C1E entry flow; VR changes cannot be undone after | PNC PM HAS §8.10.5 |

## NWP Delta

**Fast C1E is supported on NWP** — same PantherCove (PNC) core; Acode still manages WP calculation.

### Architecture Changes
- NWP uses the same PantherCove (PNC) core as DMR — **Acode (ACP) still calculates Fast C1E WP**
- Module-level C1E scope (MC1E): confirm shared PLL per module on NWP — **TBD** from NWP PM MAS
- If module PLL is shared (same as DMR DCM): MC1E requires all cores in module to reach C1E

### Validation Impact
- Same Fast C1E test scenarios as DMR (same Acode-managed WP flow)
- Verify module scope (MC1E) if NWP uses shared module PLL as DMR
- **No PkgC6 × C1E cross-product** tests needed (PkgC6 removed)

## Legacy (Human-Curated Reference)

### Architecture Summary

C1E (C1 Enhanced) drops core voltage and frequency to a **minimum VCC operating point** (LFM Work Point) while the core is in C1 idle. This saves power without power-gating the core. PNC introduces **three distinct C1E mechanisms**:

#### C1E Terminology *(confirmed: [PNC PM HAS §8.10.1](c:\github\NWP\PNC%20PM%20HAS%200.5_text.txt))*

| Term | Definition |
|------|-----------|
| **Direct/Explicit C1E** | OS/SW asks specifically to enter C1E via MWAIT(sub-state=1, lose VR) |
| **Thread C1E** | Per-thread decision affected by `C1E_PROMOTION_ENABLE` bit |
| **Core C1E** | When one thread in C1E and all others in C1E or deeper → enables lower P-state (C1E WP) |
| **Module C1E (MC1E)** | One core in C1E, the other in C1E or deeper |
| **Slow C1E (PC1E)** | PUnit detects core in C1E → after 64-250µs reduces fmax → enforces C1E WP |
| **Fast C1E (Autonomous C1E)** | **PMA locally** transitions core to pre-populated C1E WP (no PUnit involvement) |
| **HW C1E Promotion** | After core rests in C1 long enough, PMA statistically promotes C1 → C1E |
| **C1E WP** | Low P-state work point (LFM); reachable via Fast C1E or other throttling means |

#### Slow C1E vs Fast C1E *(confirmed: [PNC PM HAS §8.10.3–8.10.4](c:\github\NWP\PNC%20PM%20HAS%200.5_text.txt))*

**Slow C1E** (legacy): PUnit detects core in C1E, waits 64-250µs, then reduces fmax. PMA responds to WP.1 fmax reduction but is not directly aware it's C1E. Exit latency: 25-50µs to restore P-state.

**Fast C1E** (PNC new): PMA **locally** transitions the module to a pre-populated Fast-C1E WP when one thread in C1E and all others in C1E or deeper. No PUnit involvement → much faster entry/exit.
- **Goal**: Lower power and increase residency in low-voltage states with quick exit time
- **Key for latency-sensitive customers** who disable C6 and/or Package C1E but still need QnR reliability (voltage residency targets)

#### C1E LFM Work Point — Server vs Client *(confirmed: [PNC PM HAS §8.10.2](c:\github\NWP\PNC%20PM%20HAS%200.5_text.txt))*

- **Server**: Keeps enough voltage for highest license (e.g., TUML) → can execute first instruction at full voltage immediately on exit. Exit time: ~2µs to first instruction.
- **Client**: Drops to minimal Vmin → maximum power savings but longer wake latency.
- **Hybrid Mode (PNC new)**: Acode defines LFM WP as maximum *valid* license (not maximum *applied* license) — balances power savings with exit latency.

#### HW C1E Promotion Algorithm *(confirmed: [PNC PM HAS §8.10.5](c:\github\NWP\PNC%20PM%20HAS%200.5_text.txt))*

Statistical promotion of C1 → C1E based on observed C1 residency:

```
1. CoreInC1 detection: PMA monitors ~CoreActive signal (C1 = not active AND not C6)

2. C1 Incidency Counter (per C1 window):
   ├── Starts counting on C1 entry (rising edge of CoreInC1)
   ├── Each count = CR_C1_LIMIT × 4µs (granularity 4µs, 4-bit width → max 60µs)
   ├── Saturates at 3 (2-bit counter)
   └── Stops on C1 exit or saturation

3. Average Incidency Buffer (sliding window of 8 entries):
   ├── Each C1 window shifts its count (0-3) into next buffer entry
   ├── 0 is meaningful — records short C1 windows as "insufficient"
   └── Sliding window tracks last 8 C1 events

4. Promotion Decision:
   ├── Sum all 8 entries → if SUM ≥ 8 → C1E eligible
   └── Max possible sum = 24 (8 entries × 3 max each)

5. Hysteresis:
   ├── After exiting C1E, PMA waits for Hysteresis counter to expire
   └── Hysteresis time: {0, 2, 4, 8, 16, 32} µs (encoded in CR)

6. Entry Flow:
   ├── Check feature enabled
   ├── Check average latency sufficient (above limit)
   ├── Check hysteresis expired
   ├── Prevent conflicts with S1, TT1, CPD, C6
   ├── Abort point: after fast GV-down but before voltage applied
   └── Apply C1E voltage/frequency

7. Exit Flow:
   ├── Run exit as soon as possible
   ├── Only blocking condition: conflicting flow
   └── Restore prior voltage/frequency
```

### Key Registers & Interfaces

| Register | Description | Source |
|----------|-------------|--------|
| `CORE_PMA_CR_CONFIG_0[C1E]` | C1E enable bit — read by uCode during entry | ✅ PNC PM HAS §8.5.4 |
| MSR `0x1FC` (POWER_CTL) | C1E enable — written by uCode, propagated by PUnit to PMAs | ✅ PNC PM HAS §8.10 |
| `control_c1e.enable` | Fast C1E BIOS knob | ⚠ Inferred from TC |
| `io_c1e_wp` | C1E work point configuration | ⚠ Inferred from TC |
| `acp_state` | ACP state during C1E (deprecated fields) | ⚠ Inferred from TC |
| `CORE_ACODE_CR_UCODE_CFG.WISH_ALLOW` | Contains C1E demotion from PUnit+Acode merge | ✅ PNC PM HAS §8.6 |
| C1E CR Limit | C1 average residency threshold (4µs granularity, 4-bit) | ✅ PNC PM HAS §8.10.5 |
| C1E Hysteresis CR | Post-C1E-exit wait time (6 encodings: 0-32µs) | ✅ PNC PM HAS §8.10.5 |

 