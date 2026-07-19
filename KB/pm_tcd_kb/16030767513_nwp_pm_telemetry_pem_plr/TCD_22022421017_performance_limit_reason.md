# TCD: PLR (Performance Limit Reason)

| Field | Value |
|-------|-------|
| **TCD ID** | [22022421017](https://hsdes.intel.com/appstore/article-one/#/22022421017) |
| **Title** | Performance Limit Reason |
| **Status** | open |
| **Owner** | mps |
| **Parent TPF** | [16030767513 — [NWP PM] PLR (Performance Limit Reasons)](https://hsdes.intel.com/appstore/article-one/#/16030767513) |
| **Feature** | Telemetry — PLR (Performance Limit Reason) / Platform Limit Reason |
| **Validation Phase** | **Alpha / Beta** — Feature enabling + functional validation |
| **Child TCs** | [22022422383](https://hsdes.intel.com/appstore/article-one/#/22022422383) — Platform Limit Reason Check |
| **KB last updated** | 2026-07-19 |

## Section 1: Architecture / Micro-architecture and Functionality

> **Architecture overview:** See [TPF 16030767513 — PLR](https://hsdes.intel.com/appstore/article-one/#/16030767513) §2 Design Details for full-stack cross-layer diagram, PLR coarse/fine bitfield tables, PLR architecture flow, and interface matrix.

**Performance Limit Reason (PLR)** validates that PCode correctly identifies and reports the active throttle source via PLR reason bits whenever processor frequency is limited below maximum turbo. PLR runs in the PCode slow loop (every ~1 ms), collecting limiting reasons from Slow Limits, Fast Limits/WP4, and TRL, then resolving and reporting per CCP and for the ring via the TPMI interface (MSR/PCS interfaces are deprecated).

### Functional Scope

- **PLR reason bit correctness**: correct reason bit is set when a specific limiter is active
- **Reason bit clears**: reason bit clears when the limiter is removed (within next slow loop)
- **Priority ordering**: PLR 1-hot priority — PlatPL2 > PlatPL1 > FastRAPL > SktPL2 > SktPL1
- **Multiple simultaneous limiters**: all applicable reason bits are set when multiple limiters active
- **Coarse vs fine grain consistency**: fine-grain PLR bits roll up correctly into coarse-grain bits
- **Cross-interface consistency**: TPMI PLR_DIE_LEVEL aligns with MSR 0x19C per-core reason bits
- **RW0C semantics**: log bits set by PCode when limit occurs; cleared only by SW write-0; write-1 ignored

### Spec Refs

- PLR HAS §"PLR_DIE_LEVEL" — coarse (bits 0–9) and fine (bits 32–63) bitfield definitions
- PLR HAS §"PLR_MAILBOX" — domain-specific (core/mesh) PLR, supporting both coarse and fine grain
- PLR HAS §"Slow Loop Resolution" — PLR updated every ~1 ms; 1-hot priority for RAPL-related limiters

### NWP Applicability

PLR is **fully supported on NWP**. NWP uses 2 CBBs; per-core MSR reads iterate both CBBs. MSR 0x19C path is unchanged from DMR. TPMI PERF_STATUS fine/coarse reason bits available via NIO path. Platform RAPL PLR bits (PPL1/PPL2) are ZBB on NWP — those fine-grain bits always 0.

### TC Coverage Map

| TC | Scope | Key Validation |
|----|-------|----------------|
| [22022422383 — Platform Limit Reason Check](https://hsdes.intel.com/appstore/article-one/#/22022422383) | PLR reason bit verification | Correct PLR coarse+fine bits set per active limiter; bits clear on limiter removal; TPMI PLR consistent with MSR 0x19C; mailbox returns valid data; multiple simultaneous limiters; RW0C clear semantics |

---

## Section 2: Interfaces and Protocols

| Interface | Register / Path | Description |
|-----------|----------------|-------------|
| PLR_DIE_LEVEL (TPMI) | `sv.socket0.cbb{0,1}.base.tpmi.perf_limit_reasons` | Die-level coarse (bits 0–9) + fine (bits 32–63) PLR — RW0C |
| PLR_MAILBOX_INTERFACE | PCode mailbox | Mailbox protocol for domain-specific (core/mesh) PLR |
| PLR_MAILBOX_DATA | PCode mailbox | [31:0] coarse, [63:32] fine per-domain |
| MSR 0x19C | IA32_THERM_STATUS (per-core) | POWER_LIMITATION_STATUS [11], CURRENT_LIMIT_STATUS [12], CROSS_DOMAIN_LIMIT_STATUS [14] |
| MSR 0x198 | IA32_PERF_STATUS | Current operating ratio — compare to max to confirm throttle |
| TPMI PERF_STATUS | `sv.socket0.nio.punit.tpmi.socket_rapl.perf_status` | Fine/coarse RAPL throttle reason |

---

## Section 3: Reset, Power, and Clocking

- PLR reason bits in PLR_DIE_LEVEL are log bits (RW0C) — persist until SW clears
- MSR 0x19C STATUS bits are transient (reflect current state); LOG bits are sticky
- After cold reset: all PLR bits cleared; PCode re-evaluates and sets as applicable
- After warm reset: PLR bits cleared; PCode re-evaluates within first slow loop
- PLR updated every slow loop (~1 ms) — bit transitions reflect real-time limiter state

---

## Section 4: Programming Model

### PLR Coarse-Grain Bitfield (PLR_DIE_LEVEL bits 0–9)

| Bit | Field | Description |
|---|---|---|
| 0 | FREQUENCY | Limited by Cdyn level or FCT |
| 1 | CURRENT | Limited by Pmax or Iccmax (RACL) |
| 2 | POWER | Limited by Socket/Platform RAPL or SST-CP |
| 3 | THERMAL | Limited by in-die thermal conditions |
| 4 | PLATFORM | Limited by XXPROCHOT or VRHOT |
| 5 | MCP | External die-based feedback |
| 6 | RAS | Limited by RAS |
| 7 | MISC | Out-of-band SW (e.g., BMC) |
| 8 | QOS | Quality of Service (reserved on NWP) |

### PLR Fine-Grain Bitfield (PLR_DIE_LEVEL bits 32–63)

| Bit | Field | Description |
|---|---|---|
| 32 | PL1 | Socket RAPL PL1 is active limiter |
| 33 | PL2 | Socket RAPL PL2 is active limiter |
| 34 | PPL1 | Platform RAPL PL1 (ZBB on NWP — always 0) |
| 35 | PPL2 | Platform RAPL PL2 (ZBB on NWP — always 0) |
| 36 | FAST_RAPL | FastRAPL 500 µs loop is active limiter |
| 37 | SST_CP | SST-CP limit |

### Mailbox Read Sequence

```python
# Read PLR via mailbox
sv.socket0.cbb0.base.tpmi.plr_mailbox_interface.write(
    (1 << 31) | (domain_id << 8) | (0x01)  # RUN_BUSY=1 + domain + READ_CMD
)
# Wait for RUN_BUSY clear
while sv.socket0.cbb0.base.tpmi.plr_mailbox_interface.read() & (1 << 31): pass
data = sv.socket0.cbb0.base.tpmi.plr_mailbox_data.read()
coarse = data & 0xFFFFFFFF
fine = (data >> 32) & 0xFFFFFFFF
```

---

## Section 5: Pass/Fail Bar

**Bar (PLR reason bit correctness and reporting):**

| Criterion | Threshold | Spec ref |
|-----------|-----------|----------|
| RAPL PL1 limiter → PLR POWER bit | PLR_DIE_LEVEL coarse bit 2 = 1 AND fine bit 32 = 1 within 2 slow loops (~2 ms) | PLR HAS §"PLR_DIE_LEVEL" |
| RAPL PL2 limiter → PLR POWER bit | PLR_DIE_LEVEL coarse bit 2 = 1 AND fine bit 33 = 1 | PLR HAS §"PLR_DIE_LEVEL" |
| Thermal limiter → PLR THERMAL bit | PLR_DIE_LEVEL coarse bit 3 = 1 | PLR HAS §"PLR_DIE_LEVEL" |
| PROCHOT → PLR PLATFORM bit | PLR_DIE_LEVEL coarse bit 4 = 1 | PLR HAS §"PLR_DIE_LEVEL" |
| Multiple simultaneous limiters | All applicable coarse + fine bits set simultaneously | PLR HAS §"Slow Loop Resolution" |
| PLR priority ordering | 1-hot: PlatPL2 > PlatPL1 > FastRAPL > SktPL2 > SktPL1 | PLR HAS §"Priority" |
| PLR bit clears on limiter removal | Corresponding bit = 0 within 2 slow loops after limiter removed | PLR HAS §"PLR_DIE_LEVEL" — RW0C |
| RW0C semantics | Write-0 clears bit; write-1 ignored; PCode re-sets if condition persists | PLR HAS §"RW0C Semantics" |
| Cross-interface consistency | MSR 0x19C POWER_LIMITATION_STATUS [11] aligns with TPMI PLR POWER coarse bit | PLR HAS + Intel SDM |
| Mailbox returns valid data | PLR_MAILBOX_DATA coarse+fine match PLR_DIE_LEVEL for same domain | PLR HAS §"PLR_MAILBOX" |
| Per-CBB independence | Each CBB (cbb0, cbb1) reports PLR independently | NWP topology |

**FAIL:** Limiter active but corresponding PLR bit not set; PLR bit set with no active limiter (and not a stale LOG bit); multiple limiters but only one PLR bit set; PLR bit not cleared within 2 slow loops after limiter removed; MSR 0x19C disagrees with TPMI PLR; mailbox returns error or mismatched data; write-1 clears a bit (RW0C violation).

---

## Section 6: TC Coverage Map & Corner Cases

| TC | Scope | Key Validation |
|----|-------|----------------|
| [22022422383](https://hsdes.intel.com/appstore/article-one/#/22022422383) | Platform Limit Reason Check | Full PLR verification: coarse+fine, RW0C, mailbox, cross-interface |

### Corner Cases

| Corner Case | Expected Behavior | Env |
|---|---|---|
| RAPL PL1 + PL2 both active | POWER coarse (2) + PL1 fine (32) + PL2 fine (33) all set | Simics=Full, Si=Full |
| Thermal + RAPL simultaneous | Both THERMAL (3) and POWER (2) coarse bits set | Si=Full |
| FastRAPL active alone | POWER coarse (2) + FAST_RAPL fine (36) set | Simics=Full, Si=Full |
| All limiters removed | All PLR bits clear within next slow loop (~1 ms) | Simics=Full, Si=Full |
| PLR read during PCode slow loop update | No torn reads — 64-bit atomicity on TPMI path | Si=Full |
| PLR per-module: different limiters per module | PLR_MAILBOX_DATA shows different bits per module; DIE_LEVEL is OR | Simics=Full, Si=Full |
| RAPL throttle active but reason bit not set | PCode PLR reporting bug — investigate PERF_STATUS | Si=Full |
| Reason bit set but no active limiter | Stale sticky LOG bit — clear with W0C | Si=Full |
| PLR_MAILBOX RUN_BUSY timeout | Mailbox handshake failure — PCode not responding | Si=Full |
| Platform RAPL PLR bits (PPL1/PPL2) on NWP | Always 0 — Platform RAPL is ZBB | Simics=Full, Si=Full |

---

## Section 7: Security / Safety / Policy

- PLR reason bits via PLR_DIE_LEVEL (TPMI) require Ring 0 or OOB privilege
- MSR 0x19C per-core reads require Ring 0
- PLR log bits are RW0C — debug reads do NOT clear bits (only explicit 0-write clears)
- PLR provides transparent visibility into performance limiting — supports debug and CSP SLA monitoring

---

## Section 8: References

| Reference | Link |
|-----------|------|
| PLR HAS | [PLR_HAS.html](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_PLR.html) |
| Intel RAPL HAS | [RAPL.html](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/RAPL/RAPL.html) — PERF_STATUS reason bit definitions |
| NWP PM MAS | [nwp_imh_soc_pm_mas.html](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) |
| Intel SDM | IA32_THERM_STATUS (MSR 0x19C) — power/current/cross-domain limit bits |
| Parent TPF KB | [TPF_16030767513](../pm_tpf_kb/16030767511_nwp_pm_telemetry_pem_plr/TPF_16030767513_nwp_pm_plr_performance_limit_reasons.md) |
| Socket RAPL KB | [socket_rapl.md](../../pm_features/power_rapl/socket_rapl.md) — RAPL throttle reason context |
| TCD 22022420821 | [Socket RAPL Registers](https://hsdes.intel.com/appstore/article-one/#/22022420821) — PERF_STATUS fine/coarse coverage |
| TCD 16031169448 | [Socket RAPL Reporting / Observability](https://hsdes.intel.com/appstore/article-one/#/16031169448) — PLR priority ordering |
| TCD 22022420798 | [Socket RAPL Algorithm & Functionality](https://hsdes.intel.com/appstore/article-one/#/22022420798) — RAPL enforcement that drives PLR |
