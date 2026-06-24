# TCD: Performance Limit Reason (Platform Limit Reason)

| Field | Value |
|-------|-------|
| **TCD ID** | [22022421017](https://hsdes.intel.com/appstore/article-one/#/22022421017) |
| **Title** | Performance Limit Reason |
| **Status** | open |
| **Owner** | mps |
| **Parent TP** | [16030767513 -- NWP PM Telemetry (PEM/PLR)](https://hsdes.intel.com/appstore/article-one/#/16030767513) |
| **KB last updated** | 2026-06-24 |
| **Feature** | Telemetry -- PLR (Performance Limit Reason) / Platform Limit Reason |

## Section 1: Architecture / Micro-architecture and Functionality

**Performance Limit Reason (PLR)** / **Platform Limit Reason** exposes the active reason(s) why processor frequency is currently limited. When a core is running below its maximum turbo frequency, one or more limit reasons are flagged to indicate the responsible throttling source (RAPL, thermal, electrical/ICCMAX, etc.). This information is critical for power management debug and platform power optimization.

PLR is exposed via **IA32_THERM_STATUS (MSR 0x19C)** and related telemetry registers. PCode/PrimeCode sets the reason bits when the corresponding limiter is the active constraint. The **TPMI PERF_STATUS** (fine/coarse throttle reason fields) covered in Socket RAPL Register TCD also relates to PLR.

### PLR Architecture

```
+-------------------------------------------------------------------------+
| Active Limiters (PCode / PrimeCode)                                     |
|                                                                          |
|  RAPL PL1 / PL2 ──> RAPL reason bit set when RAPL is active limiter     |
|  Thermal (Tj)    ──> Thermal reason bit set when temperature throttling  |
|  ICCMAX / Power  ──> Electrical reason bit set when current limited      |
|  Platform RAPL   ──> Platform power reason bit set                       |
|  External (PROCHOT) ──> PROCHOT reason bit when external throttle        |
+-----------------------------+-------------------------------------------+
                              |
                              | sets reason bits in
                              v
+-------------------------------------------------------------------------+
| IA32_THERM_STATUS (MSR 0x19C)                                           |
|  Bit 11: POWER_LIMITATION_STATUS -- RAPL or power budget limiting        |
|  Bit 12: CURRENT_LIMIT_STATUS    -- ICCMAX electrical limiting           |
|  Bit 14: CROSS_DOMAIN_LIMIT_STATUS -- cross-die or platform limiting     |
|  (+ thermal bits 0-9)                                                    |
+-----------------------------+-------------------------------------------+
                              |
                              | observable by OS / validation
                              v
+-------------------------------------------------------------------------+
| SW / Validation Observation                                             |
|  MSR 0x19C per-core reads                                               |
|  TPMI PERF_STATUS fine/coarse throttle reason fields (per CBB)          |
|  PLR telemetry via PMx / python-sv                                      |
+-------------------------------------------------------------------------+
```

### Functional Scope

- **PLR reason bit correctness**: the correct reason bit is set when a specific limiter is active
- **Reason bit clears**: reason bit clears when the limiter is removed
- **Priority/masking**: when multiple limiters are active, all applicable reason bits are set
- **Platform limit reason**: platform-level limit reasons (cross-die, OOB, platform RAPL) are visible
- **Register consistency**: TPMI PERF_STATUS fine/coarse reason fields align with MSR 0x19C reason bits

### NWP Applicability

PLR is **fully supported on NWP**. NWP uses 2 CBBs; per-core MSR reads iterate both CBBs. MSR 0x19C path is unchanged from DMR. TPMI PERF_STATUS fine/coarse reason bits available via NIO path.

### TC Coverage Map

| TC | Scope | Key Validation |
|----|-------|----------------|
| [22022422383 -- Platform Limit Reason Check](https://hsdes.intel.com/appstore/article-one/#/22022422383) | PLR reason bit verification | Correct PLR reason bits set when RAPL / thermal / electrical / platform limits are active; bits clear when limiter removed; TPMI PERF_STATUS fine/coarse fields consistent with MSR reason |

---

## Section 2: Interfaces and Protocols

| Interface | Register / Path | Description |
|-----------|----------------|-------------|
| MSR 0x19C | IA32_THERM_STATUS | Per-core limit reason bits: POWER_LIMITATION_STATUS [11], CURRENT_LIMIT_STATUS [12], CROSS_DOMAIN_LIMIT_STATUS [14] |
| MSR 0x198 | IA32_PERF_STATUS | Current operating ratio -- compare to max to confirm throttle |
| TPMI PERF_STATUS | sv.socket0.nio.punit.tpmi.socket_rapl.perf_status | Fine / coarse RAPL throttle reason (from Socket RAPL TCD 22022420821) |
| MSR 0x1AD | IA32_TURBO_RATIO_LIMIT | Active TRL -- compare to current ratio to infer TRL-driven limit |
| NWP namednodes | pd.debug.access_to_msr(0x19C, core=N) | Per-core PLR read |

---

## Section 3: Reset, Power, and Clocking

- PLR reason bits in MSR 0x19C are transient -- set when limiter is active, cleared when resolved
- POWER_LIMITATION_STATUS and CURRENT_LIMIT_STATUS have sticky LOG bits (bits 11, 13) -- set until SW clears
- After warm reset: all PLR bits cleared; PCode re-evaluates and sets as applicable
- CROSS_DOMAIN_LIMIT_STATUS cleared on reset; set again if platform-level throttle is re-applied

---

## Section 4: Programming Model

### PLR Verification Flow

1. Establish a baseline: read MSR 0x19C on all active cores -- verify no unexpected reason bits set
2. Force RAPL PL1 throttle (set PL1 below active power level):
   - Read MSR 0x19C: verify POWER_LIMITATION_STATUS [11] = 1
   - Read TPMI PERF_STATUS: verify RAPL reason bit set
3. Remove RAPL throttle: verify bit 11 clears (within PID loop settling time)
4. Force thermal throttle (if platform supports thermal injection):
   - Read MSR 0x19C: verify THERMAL bits set
5. Verify multiple simultaneous reasons: apply RAPL + platform throttle together -- all applicable bits set
6. Read per-core MSR 0x19C on all cores in both CBBs (NWP: 2 CBBs x 48 cores)

### NWP Execution Notes

- Iterate both CBBs: use pd.debug.access_to_msr(0x19C, core=N) for N across all active cores
- TPMI PERF_STATUS fine/coarse: verify via sv.socket0.nio.punit.tpmi.socket_rapl.perf_status

---

## Section 5: Operational Behavior

- When RAPL PL1 is the active limiter: POWER_LIMITATION_STATUS [11] = 1 on affected cores
- When ICCMAX is the active limiter: CURRENT_LIMIT_STATUS [12] = 1
- When platform or cross-die limit applies: CROSS_DOMAIN_LIMIT_STATUS [14] = 1
- All active reason bits may be set simultaneously when multiple limiters apply
- Sticky LOG bits (bits 11 log, 13, etc.) persist until SW clears via 0-write

---

## Section 6: Corner Cases & Error Handling

| Scenario | Expected Behavior |
|----------|------------------|
| RAPL throttle active but reason bit not set | PCode/PrimeCode PLR reporting bug; investigate PERF_STATUS |
| Reason bit set but no active limiter | Stale sticky LOG bit; clear with 0-write to MSR 0x19C |
| Multiple limiters simultaneously | All applicable reason bits set |
| CROSS_DOMAIN_LIMIT_STATUS behavior on NWP | Platform/OOB limits visible via bit 14 when applicable |
| Reason bit per-core inconsistency | Different cores may have different active limiters |

---

## Section 7: Security / Safety / Policy

- PLR reason bits are read-only for OS (sticky LOG bits can be cleared by SW)
- PLR telemetry provides transparent visibility into performance limiting -- supports debug without exposing sensitive data
- LOCK_THERM_INT (deprecated on NWP) -- PLR interrupts handled via PCode broadcast

---

## Section 8: References

- [Socket RAPL KB -- socket_rapl.md](../../pm_features/power_rapl/socket_rapl.md) -- RAPL throttle reason and PERF_STATUS context
- [TCD 22022420821 -- Socket RAPL Registers Verification](https://hsdes.intel.com/appstore/article-one/#/22022420821) -- PERF_STATUS fine/coarse reason coverage
- [TCD 22022420798 -- Socket RAPL Algorithm & Functionality](https://hsdes.intel.com/appstore/article-one/#/22022420798) -- RAPL enforcement that drives POWER_LIMITATION reason
- [Intel RAPL HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/RAPL/RAPL.html) -- PERF_STATUS reason bit definitions
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) -- NWP throttle reason reporting
- [NWP HAS PM Features](https://docs.intel.com/documents/custom-xeon/newport-docs/has/Overview/NWP_HAS.html)
