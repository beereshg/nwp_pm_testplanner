# TCD: PMAX Cross Products

| Field | Value |
|-------|-------|
| **TCD ID** | [22022420701](https://hsdes.intel.com/appstore/article-one/#/22022420701) |
| **Title** | PMAX Cross Products |
| **Parent TPF** | [15019477947](https://hsdes.intel.com/appstore/article-one/#/15019477947) |
| **Feature** | PMAX |
| **NWP Disposition** | Runnable_On_N-1 |
| **KB last updated** | 2026-06-25 |

## Section 1: Architecture / Micro-architecture and Functionality

**PMAX Cross Products** validate system stability and correct arbitration when PMAX hard throttle co-occurs with other power/thermal limiting features. The key principle: `min(PMax Psafe ceiling, Fast RAPL ceiling, RAPL PL1/PL2 ceiling)` must be enforced without MCA, hang, or incorrect PLR reporting.

**Cross-product scenarios (ti_gate.b0 / NGA_MAIN):**
- **PMAX × Fast RAPL**: PMAX hard throttle concurrent with Fast RAPL power excursion; min-ceiling arbitration; both PLR bits set
- **PMAX × Thermals**: PMAX hard throttle concurrent with PROCHOT thermal throttle; PMAX dominates (lower ceiling); both PLR bits set

**NWP delta:** Single NIO; 2 CBBs; no IMH1. PROCHOT via `sv.socket0.imh0.punit.prochot_trigger`. Fast RAPL via `sv.socket0.cbb{0,1}.base.tpmi.pem_status`.

### TC Coverage Map

| TC ID | Title | NWP Disposition |
|-------|-------|----------------|
| [22022421790](https://hsdes.intel.com/appstore/article-one/#/22022421790) | PMAX Cross Fast RAPL | Runnable_On_N-1 |
| [22022421791](https://hsdes.intel.com/appstore/article-one/#/22022421791) | PMAX Cross Thermals | Runnable_On_N-1 |

---

## Section 2: Interfaces and Protocols

| Interface | Register / Path | Purpose |
|-----------|----------------|---------|
| global_pmax_inject | sv.socket0.imh0.pcodeio_map.io_pmax_config.global_pmax_inject | DFX PMAX hard throttle inject |
| pmax_log | sv.socket0.imh0.punit.throttle.package_therm_status.pmax_log | PMAX event log; set during throttle |
| perf_limit_reasons bit 8 | sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.perf_limit_reasons | MT-PMAX PLR bit |
| perf_limit_reasons bit 9 | sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.perf_limit_reasons | FAST_RAPL PLR bit |
| prochot_trigger | sv.socket0.imh0.punit.prochot_trigger | PROCHOT injection for thermal cross-product |
| pem_status | sv.socket0.cbb{0,1}.base.tpmi.pem_status | Fast RAPL PEM excursion bit per CBB |

---

## Section 3: Reset, Power, and Clocking

- Cross-product tests run on fully booted system with no pre-existing MCAs
- PMAX inject requires punit_supervises_pmax=1 and global_pmax_latch_bypass=1
- Both injections must be cleaned up after test (inject=0; prochot=0)

---

## Section 4: Programming Model

- PMAX inject: `global_pmax_inject=1` + `global_pmax_latch_bypass=1` + supervision configured
- Fast RAPL: sustained workload (PTU/PTAT) driving power above Fast RAPL threshold
- PROCHOT inject: `prochot_trigger.write(1)` for thermal throttle simulation
- Verify: both PLR bits set concurrently; system stable for 30s; clean recovery after clear

---

## Section 5: Operational Behavior

**PMAX × Fast RAPL:**
1. Start PTAT workload → Fast RAPL PLR bit (bit 9) active
2. Inject PMAX hard throttle → PMAX PLR bit (bit 8) active
3. min(PMAX Psafe, Fast RAPL ceiling) enforced — PMAX typically more restrictive
4. Clear both; verify clean recovery; no MCA

**PMAX × Thermals:**
1. Inject PROCHOT → PROCHOT PLR active; thermal throttle engaged
2. Inject PMAX hard throttle simultaneously
3. PMAX ceiling more restrictive than PROCHOT; PMAX hard throttle dominates
4. Clear both; verify recovery

---

## Section 6: Corner Cases & Error Handling

| Scenario | Expected Behavior |
|----------|-----------------|
| Only one PLR bit set during concurrent throttle | One path blocked; check inject sequence |
| MCA during dual throttle | Critical failure; collect NLOG and crash dump |
| Stuck PLR after clear | Stale semaphore; clear GLOBAL_PMAX_SEMAPHORE |
| Fast RAPL not active | SVID IMON invalid or workload insufficient |

---

## Section 7: Security / Safety / Policy

- Cross-product tests require privileged access for PMAX inject and PROCHOT trigger
- Dual throttle testing must be done in controlled lab; risk of system instability
- Clean up both inject states before declaring test complete

---

## Section 8: References

- [DMR PMax HAS](https://docs.intel.com/documents/pm_doc/src/server/dmr/pm_features/dmr_pmax.html) — PMAX vs RAPL priority; min-ceiling arbitration; hard throttle dominance
- [Primecode Fast RAPL Flow](https://docs.intel.com/documents/primecode/primecode_two/firmware_architecture/flows_pm_features/fast_rapl.html) — concurrent Fast RAPL + PMAX behavior
- [DMR Thermal HAS](https://docs.intel.com/documents/pm_doc/src/server/dmr/pm_features/thermals/dmr_thermal.html) — PROCHOT concurrent with PMAX behavior
