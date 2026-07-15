# TCD: CCF PM Interface Check (Merged)

| Field | Value |
|-------|-------|
| **Merged TCDs** | [22022421165](https://hsdes.intel.com/appstore/article-one/#/22022421165) · [22022421168](https://hsdes.intel.com/appstore/article-one/#/22022421168) · [22022421171](https://hsdes.intel.com/appstore/article-one/#/22022421171) |
| **Title** | CCF PM Interface Check |
| **Status** | open |
| **Owner** | bg3 |
| **Parent TP** | [22022420512 -- CBB CCF Feature Enabling](https://hsdes.intel.com/appstore/article-one/#/22022420512) |
| **Feature** | CBB CCF Active States -- GV management |
| **KB last updated** | 2026-07-13 |
| **Merge note** | Consolidated from: BIOS Configuration (22022421165), PEGA (22022421168), TPMI Interface (22022421171) |

---

## Overview

This merged TCD covers the three external interface paths used to configure and exercise CBB CCF ring frequency GV:

| Sub-TCD | ID | Interface | Primary Register | Validation Scenario |
|---------|----|-----------|-----------------|---------------------|
| BIOS Configuration | 22022421165 | BIOS CPL3 → TPMI | `UFS_CONTROL` (boot-time write) | MAX/MIN ratio limits, ELC thresholds set at TPMI_INIT |
| PEGA | 22022421168 | B2P Mailbox | `pega_mailbox.pega_pstate(meshgv=...)` | Synthetic P-state injection bypassing BW heuristic |
| TPMI Interface | 22022421171 | Runtime TPMI R/W | `UFS_CONTROL` (runtime write) | Ratio lock (MAX=MIN), autonomous restore |

All three paths converge on the CBB PCode GVFSM; they differ only in **who sets the frequency request and when**.

---

## Section 1: Architecture / Micro-architecture and Functionality

### CCF GV Interface Architecture

```
Boot Time (BIOS)          Runtime (TPMI)         PSS/PythonSV (PEGA)
      │                         │                         │
      │  TpmiSetUfsControl()    │  sv.cbbN.tpmi           │  pega_mailbox
      │  MAX_RATIO, MIN_RATIO   │  .ufs_control           │  .pega_pstate(meshgv)
      │  ELC thresholds         │  .max_ratio = N          │
      ▼                         ▼                         ▼
┌─────────────────────── TPMI UFS_CONTROL (per CBB) ──────────────────────┐
│  MAX_RATIO [14:8]  MIN_RATIO [21:15]  UFS_THROTTLE_MODE [1:0]          │
│  ELC_LOW_RATIO     ELC_HIGH_THRESHOLD                                    │
└───────────────────────────────┬─────────────────────────────────────────┘
                                 │  PCode reads per slow-loop (~1ms)
                    ┌────────────▼──────────────┐
                    │     CBB PCode GVFSM        │
                    │  freq = f(BW, MAX, MIN)     │
                    │  V-first / PLL-first GV     │
                    └────────────┬──────────────┘
                                 │
                    ┌────────────▼──────────────┐
                    │  UFS_STATUS.CURRENT_RATIO  │  ← observed output
                    │  HPM 0x1b DESIRED_RATIO    │  ← to IMH Primecode
                    │  PLR_DIE_LEVEL             │  ← Perf Limit Reason
                    └───────────────────────────┘
```

### 1A — BIOS Configuration (TCD 22022421165)

BIOS writes `UFS_CONTROL` during TPMI_INIT (PH1.x) to establish the CCF frequency operating envelope:

| Knob | Register Field | Default |
|------|---------------|---------|
| CBB CCF GV Max Ratio | `UFS_CONTROL.MAX_RATIO` | P0 from fuse (2.2 GHz / ratio 0x16) |
| CBB CCF GV Min Ratio | `UFS_CONTROL.MIN_RATIO` | Pm from fuse (800 MHz / ratio 0x08) |
| CCF ELC Low Threshold | `UFS_CONTROL.ELC_LOW_THRESHOLD` | 10% C0 utilization |
| CCF ELC High Threshold | `UFS_CONTROL.ELC_HIGH_THRESHOLD` | 95% C0 utilization |
| CCF Throttle Mode | `UFS_CONTROL.UFS_THROTTLE_MODE` | 0 = autonomous |

> **NWP note:** 2 CBBs; BIOS must program UFS_CONTROL on both independently via `TpmiSetUfsControlRegPerHub()`.

### 1B — PEGA Injection (TCD 22022421168)

PEGA bypasses the BW-heuristic slow loop and injects a synthetic P-state directly via B2P mailbox:

```
pega_mailbox.pega_pstate(meshgv=0)    # → P0 (2.2 GHz)
pega_mailbox.pega_pstate(meshgv=N)    # → specific ratio floor
pega_mailbox.pega_pstate(meshgv='rand') # → random stress
```

Requires: `ProcessorHWPMEnable=1` BIOS knob. After injection, GVFSM processes request → UFS_STATUS.CURRENT_RATIO settles → HPM 0x1b updated.

### 1C — TPMI Runtime Interface (TCD 22022421171)

Runtime TPMI writes allow ratio pinning without a reboot:

```
# Pin CCF at 1.8 GHz (ratio lock)
sv.socket0.cbbN.base.tpmi.ufs_control.max_ratio = 0x12
sv.socket0.cbbN.base.tpmi.ufs_control.min_ratio = 0x12
# Wait ~5M cycles for GVFSM convergence
# Verify: sv.socket0.cbbN.base.tpmi.ufs_status.current_ratio == 0x12

# Restore autonomous
sv.socket0.cbbN.base.tpmi.ufs_control.max_ratio = 0x16
sv.socket0.cbbN.base.tpmi.ufs_control.min_ratio = 0x08
```

---

## Section 2: Interfaces and Protocols

| Interface | Register / Path | Sub-TCD | Purpose |
|-----------|----------------|---------|---------|
| BIOS CPL3 write | `TpmiSetUfsControlRegPerHub()` | 22022421165 | Boot-time envelope setup |
| B2P Mailbox | `pega_mailbox.pega_pstate(meshgv=N)` | 22022421168 | Runtime synthetic P-state injection |
| TPMI UFS_CONTROL | `sv.socket0.cbbN.base.tpmi.ufs_control` | 22022421171 | Runtime ratio lock / unlock |
| TPMI UFS_STATUS | `sv.socket0.cbbN.base.tpmi.ufs_status.current_ratio` | all | Observed CCF ratio after GVFSM |
| TPMI UFS_HEADER | `sv.socket0.cbbN.base.tpmi.ufs_header` | 22022421165/171 | Fused P0/Pm caps |
| TPMI PLR_DIE_LEVEL | `sv.socket0.cbbN.base.tpmi.plr_die_level` | 22022421168/171 | Perf Limit Reason (expect 0x0) |
| HPM 0x1b | `UPSTREAM_CCF_DESIRED_RATIO` | 22022421168 | CCF desired ratio → IMH Primecode |

---

## Section 3: Reset, Power, and Clocking

- CCF GV state resets on warm reset; BIOS re-programs `UFS_CONTROL` during TPMI_INIT at next boot
- RING PLL and FIVR initialize to boot ratio; PCode GVFSM takes control after PH6
- `UFS_STATUS.CURRENT_RATIO` reflects live PLL state (no caching)
- V-first for frequency increase; PLL-first for frequency decrease — mandatory for stable operation
- TPMI runtime writes take effect at next GVFSM slow-loop (~1 ms latency)

---

## Section 4: Programming Model

- **BIOS path:** `TpmiSetUfsControlRegPerHub()` → called during CPL3 TPMI_INIT phase
- **PEGA path:** `diamondrapids.pm.pss.mailbox.pega_mailbox.pega_pstate()` — requires `ProcessorHWPMEnable=1`
- **TPMI path:** Direct namednodes write via `sv.socket0.cbbN.base.tpmi.ufs_control`; on emulation wait 5M cycles before readback

---

## Section 5: Operational Behavior

The GVFSM slow-loop (~1 ms) processes all interface inputs in priority order:
1. Reads `UFS_CONTROL` MAX_RATIO / MIN_RATIO (BIOS or TPMI last write)
2. Reads PEGA B2P request (if present, overrides BW heuristic)
3. Reads BW telemetry (CBO/SBO lookup counter) for autonomous mode
4. Computes target ratio, clamps to [MIN, MAX]
5. Executes GV transition (V-first up / PLL-first down)
6. Updates `UFS_STATUS.CURRENT_RATIO` and `HPM 0x1b`

---

## Section 6: Corner Cases & Error Handling

| Scenario | Expected Behavior |
|----------|-----------------|
| BIOS programs MAX < MIN | PCode reverts to fuse defaults; GVFSM disabled |
| Ratio above P0 fuse cap | Silently clamped to `UFS_HEADER.MAX_RATIO_CAP` |
| Ratio below Pm fuse floor | Silently clamped to `UFS_HEADER.MIN_RATIO_CAP` |
| PEGA injection with HWP disabled | B2P mailbox rejects — requires BIOS HWP enable |
| GVFSM stuck (busy bit set) | System hang risk; detect via `UFS_STATUS` GVFSM status bits |
| TPMI write on wrong CBB | Each CBB has independent UFS_CONTROL; per-CBB writes required |

---

## Section 7: TC Coverage Map

| TC | HSD | Interface Under Test | Key Checks |
|----|-----|---------------------|-----------|
| CBB CCF GV BIOS Configuration | [22022422850](https://hsdes.intel.com/appstore/article-one/#/22022422850) | BIOS → UFS_CONTROL | Field accessibility, PCode enforcement of BIOS-programmed limits |
| CBB CCF GV PEGA Injection | [22022422851](https://hsdes.intel.com/appstore/article-one/#/22022422851) | B2P Mailbox | PEGA injection, GVFSM ratio change, PLR clean, autonomous recovery |
| CBB CCF GV TPMI Request | [22022422859](https://hsdes.intel.com/appstore/article-one/#/22022422859) | TPMI UFS_CONTROL | Ratio lock (MAX=MIN), boundary clamping, autonomous restore |
