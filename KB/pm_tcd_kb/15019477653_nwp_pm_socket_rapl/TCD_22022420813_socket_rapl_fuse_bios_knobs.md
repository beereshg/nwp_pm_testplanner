# TCD: Socket RAPL Fuse and BIOS Knobs

| Field | Value |
|-------|-------|
| **TCD ID** | [22022420813](https://hsdes.intel.com/appstore/article-one/#/22022420813) |
| **Title** | Socket RAPL Fuse and BIOS Knobs |
| **Status** | open |
| **Owner** | mps |
| **Parent TP** | [15019477653 — NWP PM Socket RAPL](https://hsdes.intel.com/appstore/article-one/#/15019477653) |
| **Siblings** | [22022420798 — Algorithm & Functionality](https://hsdes.intel.com/appstore/article-one/#/22022420798) · [22022420806 — Cross-products](https://hsdes.intel.com/appstore/article-one/#/22022420806) |
| **KB last updated** | 2026-06-24 |
| **Feature** | Power / RAPL — Socket RAPL fuse checkout and BIOS knob verification |

## Section 1: Architecture / Micro-architecture and Functionality

This TCD verifies the **static configuration layer** of **Socket RAPL** on NWP — fuse-defined capability values and BIOS-programmed Socket RAPL knobs. Runtime algorithm validation is covered by **[TCD 22022420798](https://hsdes.intel.com/appstore/article-one/#/22022420798)**.

### Functional Scope

- Fused **Socket TDP** exposure through TPMI PL_INFO
- Fused **maximum PL2** (= 1.2 x TDP per socket_rapl.md KB)
- Fused **minimum supported power limit**
- BIOS programming of: PL1 power limit, PL2 power limit, PL1 time window, PL2 time window, lock policy

### Initialization Flow

1. PrimeCode reads RAPL capability fuses at **PH6**
2. PrimeCode populates TPMI PL_INFO (MAX_PL1, MAX_PL2, MIN_PL)
3. BIOS CPL3 reads PL_INFO to determine valid range
4. BIOS programs PL1_CONTROL and PL2_CONTROL within supported limits
5. BIOS may assert **LOCK** before OS handoff

### NWP Applicability

Socket RAPL fuse handling and BIOS knob programming are **fully supported on NWP**. Fuse structure unchanged from DMR. Runtime access via **NIO TPMI**. Legacy **MSR 0x606** deprecated -- shall not be used for unit discovery.

### Fuse and BIOS Knob Map

| Item | Type | Source | TPMI Register / Field | Expected Behavior |
|------|------|--------|----------------------|------------------|
| Socket TDP power | Fuse | Manufacturing | \PL_INFO.MAX_PL1 [17:0]\ | = fused TDP (U11.3 W) |
| Max PL2 power | Fuse | Manufacturing | \PL_INFO.MAX_PL2 [53:36]\ | = 1.2 x fused TDP |
| Min power limit | Fuse | Manufacturing | \PL_INFO.MIN_PL [35:18]\ | Non-zero minimum supported limit |
| PL1 programmed | BIOS knob | BIOS Setup | \PL1_CONTROL.PWR_LIM [17:0]\ | BIOS-configured PL1 (<=  MAX_PL1) |
| PL2 programmed | BIOS knob | BIOS Setup | \PL2_CONTROL.PWR_LIM [17:0]\ | BIOS-configured PL2 (<= MAX_PL2) |
| PL1 time window | BIOS knob | BIOS Setup | \PL1_CONTROL.TIME_WINDOW [24:18]\ | Encoded tau; clipped to [1 s, 5 s] |
| PL2 time window | BIOS knob | BIOS Setup | \PL2_CONTROL.TIME_WINDOW [24:18]\ | Encoded tau; clipped to [11.7 ms, 39 ms] |
| LOCK bit | BIOS policy | BIOS boot | \PL1_CONTROL.LOCK [63]\ | 1 = locked before OS handoff |
| RAPL units MSR | Deprecated | -- | MSR 0x606 | Not valid on NWP -- reads 0; shall not be used |

### TC Coverage Map

| TC | Scope | Key Validation |
|----|-------|----------------|
| [22022422017 -- RAPL - Checkout fuses related to RAPL](https://hsdes.intel.com/appstore/article-one/#/22022422017) | Fuse checkout | PL_INFO.MAX_PL1 = fused TDP; MAX_PL2 = 1.2 x TDP; MIN_PL non-zero; values match silicon fuse programming |
| [22022422018 -- RAPL BIOS Knobs Verification](https://hsdes.intel.com/appstore/article-one/#/22022422018) | BIOS knob verification | BIOS-programmed PL1_CONTROL / PL2_CONTROL values match expected policy; LOCK bit reflects BIOS lock setting; PL values within fused MAX bounds |
| [22022421962 -- RAPL Cold TDP checkout](https://hsdes.intel.com/appstore/article-one/#/22022421962) | Cold boot defaults | PL_INFO / default fuse initialization; PL1 default = TDP, PL2 default = 1.2×TDP *(moved from TCD 22022420798 per Co-Design T2 audit — fuse scope, not PID scope)* |

---

## Section 2: Interfaces and Protocols

| Interface | Register / Path | Purpose |
|-----------|----------------|---------|
| TPMI | PL_INFO (idx=9) | RO capability discovery — MAX_PL1, MIN_PL, MAX_PL2; populated from fuses by PrimeCode at PH6 |
| TPMI | PL1_CONTROL (idx=2) | RW — BIOS programs PL1 value, time window, lock bit |
| TPMI | PL2_CONTROL (idx=3) | RW — BIOS programs PL2 value, time window |
| CSR | PKG_RAPL_LIMIT | BIOS-only; locked at boot; mirrors TPMI values |
| MSR 0x606 | IA32_PKG_POWER_SKU_UNIT | **Deprecated on NWP** — reads 0; use TPMI unit encoding |
| NWP namednodes | sv.socket0.nio.punit.tpmi.socket_rapl.pl_info | Fuse capability read path |
| NWP namednodes | sv.socket0.nio.punit.tpmi.socket_rapl.pl1_control | PL1 BIOS knob verification path |
| NWP namednodes | sv.socket0.nio.punit.tpmi.socket_rapl.pl2_control | PL2 BIOS knob verification path |

---

## Section 3: Reset, Power, and Clocking

- Fuse values are static — PL_INFO is populated once at PH6 and does not change
- BIOS programs PL1/PL2 during CPL3 before OS handoff; LOCK bit prevents OS modification
- After warm reset: BIOS re-programs PL1/PL2 at CPL3; fuse values re-read at PH6
- LOCK bit cleared on cold reset; re-set by BIOS during next boot cycle

---

## Section 4: Programming Model

**Fuse Capability Checks:**

1. Read TPMI PL_INFO.MAX_PL1; compare to expected fused Socket TDP value
2. Read TPMI PL_INFO.MAX_PL2; verify = 1.2 x MAX_PL1 (U11.3 format)
3. Read TPMI PL_INFO.MIN_PL; verify non-zero and < MAX_PL1

**BIOS Knob Checks:**

1. Configure BIOS PL1 knob to a known value; boot platform
2. Read PL1_CONTROL.PWR_LIM; verify = BIOS-configured value (U11.3, <= MAX_PL1)
3. Read PL1_CONTROL.TIME_WINDOW; verify encoded tau = BIOS-configured time window (clipped to valid range)
4. Read PL1_CONTROL.LOCK; verify = 1 if BIOS configured lock
5. Repeat equivalent checks for PL2_CONTROL

On NWP: validation shall use **TPMI**. Deprecated MSR 0x606 shall not be used.

**Power unit encoding (U11.3)**: 1 LSB = 0.125 W.

---

## Section 5: Operational Behavior

- PrimeCode reads RAPL capability fuses at PH6 and exposes them through PL_INFO
- BIOS programs PL1_CONTROL and PL2_CONTROL within fuse-defined bounds during boot
- Values above supported limits are clipped by PrimeCode to MAX_PL1 / MAX_PL2
- Time windows outside valid range are clipped to supported bounds
- When LOCK bit is set, runtime software writes to PL1_CONTROL / PL2_CONTROL are rejected

---

## Section 6: Corner Cases & Error Handling

| Scenario | Expected Behavior |
|----------|------------------|
| PL1 programmed > MAX_PL1 | PrimeCode clips to MAX_PL1; TPMI reflects clipped value |
| PL2 programmed > MAX_PL2 | PrimeCode clips to MAX_PL2 |
| PL1 TIME_WINDOW out of valid range | PrimeCode clips to [1 s, 5 s] |
| LOCK bit = 1, OS attempts to write PL1 | Write rejected; TPMI value unchanged |
| MSR 0x606 read (deprecated) | Returns 0; test must not use this MSR for unit discovery |
| Fuse not programmed (TDP = 0) | Platform-specific; verify PL_INFO handles gracefully |

---

## Section 7: Security / Safety / Policy

- BIOS LOCK bit prevents OS override of RAPL limits on managed platforms
- Fuse values are read-only and cannot be modified by software
- PL_INFO is read-only — OS/SW can discover limits but not change them

---

## Section 8: References

- [Socket RAPL KB — socket_rapl.md](../../pm_features/power_rapl/socket_rapl.md) — fuse structure, PH6 init, TPMI register definitions
- [TCD 22022420798 — Socket RAPL Algorithm & Functionality](https://hsdes.intel.com/appstore/article-one/#/22022420798) — runtime algorithm coverage
- [Intel RAPL HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/RAPL/RAPL.html) — PL_INFO / PL1_CONTROL / PL2_CONTROL register definitions
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) — PH6 RAPL init, fuse read flow
- [NWP HAS PM Features](https://docs.intel.com/documents/custom-xeon/newport-docs/has/Overview/NWP_HAS.html)
