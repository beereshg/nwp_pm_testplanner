# TCD: Socket RAPL - Reporting / Observability

| Field | Value |
|-------|-------|
| **TCD ID** | [16031169448](https://hsdes.intel.com/appstore/article-one/#/16031169448) |
| **Title** | Socket RAPL - Reporting / Observability |
| **Status** | open |
| **Owner** | bg3 |
| **Parent TPF** | [15019477653 -- NWP PM Socket RAPL](https://hsdes.intel.com/appstore/article-one/#/15019477653) |
| **Siblings** | [22022420798 -- Algorithm & Functionality](https://hsdes.intel.com/appstore/article-one/#/22022420798) . [22022420821 -- Registers CSR/TPMI](https://hsdes.intel.com/appstore/article-one/#/22022420821) . [22022420813 -- Fuse/BIOS](https://hsdes.intel.com/appstore/article-one/#/22022420813) . [22022420817 -- HPM](https://hsdes.intel.com/appstore/article-one/#/22022420817) . [22022420826 -- SVID](https://hsdes.intel.com/appstore/article-one/#/22022420826) . [22022420806 -- Cross-products](https://hsdes.intel.com/appstore/article-one/#/22022420806) . [16031169418 -- Below-Pm](https://hsdes.intel.com/appstore/article-one/#/16031169418) |
| **KB last updated** | 2026-07-18 |
| **Feature** | Power / RAPL -- Socket RAPL reporting, observability, and throttle accounting |
| **Created from** | Co-Design T2 audit 2026-07-18 -- reporting semantics split from TCD 22022420821 (register interface) |

## Section 1: Architecture / Micro-architecture and Functionality

This TCD verifies the **Socket RAPL reporting, observability, and throttle accounting** behavior on NWP. These are the software-visible outputs that allow OS, tools, and BMC to observe RAPL enforcement status -- distinct from both the control-loop algorithm (TCD 22022420798) and the raw register interface encoding (TCD 22022420821).

> **Architecture overview:** See [TPF 15019477653](https://hsdes.intel.com/appstore/article-one/#/15019477653) Section 2 Design Details for full-stack diagram and observability table.

### Functional Scope

- **PERF_STATUS throttle accounting**: counter increments during active RAPL limiting; ceases when unconstrained
- **PLR (Perf Limit Reasons)** fine-grain attribution: correct reason bit set per active limiter (PL1 vs PL2 vs FastRAPL)
- **PLR priority ordering**: 1-hot priority -- PlatPL2 > PlatPL1 > FastRAPL > SktPL2 > SktPL1
- **PEM (PnP Excursion Monitor)**: excursion events visible when RAPL limits are exceeded; PEM registers accessible

### WHAT Boundary

| Behavior | This TCD | Sibling TCD |
|----------|----------|-------------|
| Throttle counter increments correctly | YES | |
| Correct limiter attributed in PLR reason bits | YES | |
| PLR priority order correct | YES | |
| PEM excursion events visible | YES | |
| NN-PID convergence quality (response/settling) | | TCD 22022420798 |
| PERF_STATUS register encoding / readback | | TCD 22022420821 |
| ENERGY_STATUS counter monotonicity | | TCD 22022420821 |
| HPM LEAF_PERF_STATUS transport | | TCD 22022420817 |

### NWP Applicability

- PERF_STATUS, PLR, and PEM are supported on NWP
- PLR priority includes FastRAPL (500 us loop) which is NWP-supported
- PEM accessible via CBB TPMI: sv.socket0.cbb{0,1}.base.tpmi.pem_status
- PERF_STATUS accessible via NIO TPMI: sv.socket0.nio.punit.tpmi.socket_rapl.perf_status

### TC Coverage Map

| TC | Scope | Key Validation |
|----|-------|----------------|
| [22022422032 -- RAPL PEM (PnP Excursion Monitor)](https://hsdes.intel.com/appstore/article-one/#/22022422032) | PEM registers (FV) | PEM register accessible via TPMI; excursion events visible when RAPL limits exceeded |
| [22022422036 -- RAPL Perf limit reasons - Fine & Coarse](https://hsdes.intel.com/appstore/article-one/#/22022422036) | PLR fine/coarse (FV) | Correct reason bit set per active limiter; PLR 1-hot priority order |
| [22022422038 -- RAPL Perf status](https://hsdes.intel.com/appstore/article-one/#/22022422038) | PERF_STATUS counter (FV) | Throttle accounting -- counter increments during active RAPL limiting |
| [16030715724 -- [PSS] Perf Status -- Socket RAPL](https://hsdes.intel.com/appstore/article-one/#/16030715724) | PERF_STATUS counter (PSS) | Counter increment correctness in pre-silicon |
| [16030715720 -- [PSS] PEM -- Socket RAPL PL1](https://hsdes.intel.com/appstore/article-one/#/16030715720) | PEM PL1 (PSS) | PL1 excursion monitoring in pre-silicon *(moved from TCD 22022420798)* |
| [16030715722 -- [PSS] PEM -- Socket RAPL PL2](https://hsdes.intel.com/appstore/article-one/#/16030715722) | PEM PL2 (PSS) | PL2 excursion monitoring in pre-silicon *(moved from TCD 22022420798)* |
| [16030715726 -- [PSS] PLR -- Socket RAPL PL2](https://hsdes.intel.com/appstore/article-one/#/16030715726) | PLR PL2 (PSS) | PL2 limiter attribution / PLR reason correctness *(moved from TCD 22022420798)* |
| [16030715728 -- [PSS] PLR -- Socket RAPL PL1](https://hsdes.intel.com/appstore/article-one/#/16030715728) | PLR PL1 (PSS) | PL1 limiter attribution / PLR reason correctness *(moved from TCD 22022420798)* |

### Coverage Gaps

| Gap | Recommended TC | Priority |
|-----|---------------|----------|
| PLR priority when FastRAPL + SktPL1 both active | *(TC TBD)* -- verify FastRAPL > SktPL1 in PLR | H |
| PEM excursion event timing / latency | *(TC TBD)* -- measure PEM event latency relative to limit breach | M |
| PLR transition accuracy (PL1-limiting -> PL2-limiting -> unconstrained) | *(TC TBD)* -- PLR reason bits update correctly during limiter transitions | M |

---

## Section 2: Interfaces and Protocols

| Interface | Register / Path | Description |
|-----------|----------------|-------------|
| TPMI PERF_STATUS | sv.socket0.nio.punit.tpmi.socket_rapl.perf_status | Throttle counter + fine/coarse reason bits |
| TPMI PEM_STATUS | sv.socket0.cbb{0,1}.base.tpmi.pem_status | PEM excursion events per CBB |
| HPM 0x16 | LEAF_PERF_STATUS | CBB -> NIO feedback (transport verified by TCD 22022420817; reporting semantics verified here) |

> Spec ref: RAPL HAS -- LEAF_PERF_STATUS PLR flag bitfields, PEM collateral

---

## Section 3: Reset, Power, and Clocking

- PERF_STATUS throttle counter: reset on cold reset; warm-reset retention behavior validated
- PLR reason bits: cleared when no limiter active; updated each PID iteration
- PEM: excursion events accumulate from boot; reset behavior per PEM spec

---

## Section 4: Programming Model

### Verifying PLR Priority

1. Configure PL1 to cause PL1-only throttling under load
2. Read PERF_STATUS reason bits: SktPL1 bit set, others clear
3. Configure PL2 to cause PL2 throttling (shorter burst)
4. Read PERF_STATUS reason bits: SktPL2 bit set (higher priority than SktPL1)
5. Enable FastRAPL with IO load
6. Read PERF_STATUS reason bits: FastRAPL bit set (higher priority than SktPL1)

### Verifying PERF_STATUS Counter

1. Apply load with PL1 set below current power draw
2. Read PERF_STATUS throttle counter at t0
3. Wait known interval
4. Read PERF_STATUS throttle counter at t1
5. Verify: t1 > t0 (counter incremented during throttling)
6. Remove load or raise PL1 above power draw
7. Read PERF_STATUS again: counter stops incrementing

On NWP: sv.socket0.nio.punit.tpmi.socket_rapl.perf_status.show()

---

## Section 5: Operational Behavior

> **WHAT:** Socket RAPL reporting, observability, and throttle accounting correctness.

**Pass/fail bar:**

**A. Throttle Accounting (TCs 22022422038, 16030715724):**
- PERF_STATUS throttle counter increments during active RAPL limiting
- Counter does NOT increment when frequency is unconstrained by RAPL
- Counter increment rate is proportional to throttle duration

**B. PLR Attribution (TC 22022422036):**
- Correct PLR reason bit set per active limiter: PL1 vs PL2 vs FastRAPL
- PLR 1-hot priority ordering: PlatPL2 > PlatPL1 > FastRAPL > SktPL2 > SktPL1
- When no limiter active: all reason bits clear
- When multiple limiters active: highest-priority limiter's bit set

**C. PEM Observability (TC 22022422032):**
- PEM registers accessible via TPMI
- Excursion events visible when RAPL power limits are exceeded
- PEM events correlate with active RAPL throttling

---

## Section 6: Corner Cases & Error Handling

| Scenario | Expected Behavior |
|----------|------------------|
| No RAPL limiting active | PERF_STATUS counter stable; all PLR reason bits clear |
| PL1-only limiting | SktPL1 reason bit set; SktPL2 and FastRAPL bits clear |
| PL1 + PL2 simultaneous | SktPL2 bit set (higher priority); SktPL1 may also be set |
| FastRAPL + SktPL1 both active | FastRAPL bit set (higher priority than SktPL1) |
| Limiter transitions (PL1 -> PL2 -> unconstrained) | Reason bits update within one PID iteration |
| PERF_STATUS counter rollover | 32-bit wrap; software handles delta calculation |
| PEM register read during no excursion | Returns 0 / no-event state |

---

## Section 7: Security / Safety / Policy

- PERF_STATUS and PEM are read-only status registers; no security-sensitive write path
- PLR reason bits are software-visible for power management telemetry and debugging

---

## Section 8: References

- [Socket RAPL KB -- socket_rapl.md](../../pm_features/power_rapl/socket_rapl.md) -- PLR priority, PERF_STATUS fields
- [TCD 22022420821 -- Registers CSR/TPMI](https://hsdes.intel.com/appstore/article-one/#/22022420821) -- raw register interface (sibling)
- [TCD 22022420798 -- Algorithm & Functionality](https://hsdes.intel.com/appstore/article-one/#/22022420798) -- NN-PID convergence (sibling)
- [DMR RAPL Simplification HAS](https://docs.intel.com/documents/pm_doc/src/server/dmr/pm%20features/dmr_rapl_simplification.html) -- PLR flag bitfields
- Co-Design T2 audit 2026-07-18 -- reporting/observability split from TCD 22022420821
