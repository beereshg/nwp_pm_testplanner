# TCD: Socket RAPL SVID Reporting Verification

| Field | Value |
|-------|-------|
| **TCD ID** | [22022420826](https://hsdes.intel.com/appstore/article-one/#/22022420826) |
| **Title** | Socket RAPL SVID Reporting Verification |
| **Status** | open |
| **Owner** | mps |
| **Parent TP** | [15019477653 -- NWP PM Socket RAPL](https://hsdes.intel.com/appstore/article-one/#/15019477653) |
| **Siblings** | [22022420798 -- Algorithm & Functionality](https://hsdes.intel.com/appstore/article-one/#/22022420798) . [22022420821 -- Registers Verification](https://hsdes.intel.com/appstore/article-one/#/22022420821) |
| **KB last updated** | 2026-06-24 |
| **Feature** | Power / RAPL -- Socket RAPL SVID IMON telemetry |

## Section 1: Architecture / Micro-architecture and Functionality

This TCD verifies **SVID IMON (Serial Voltage ID / Input Monitor Current) reporting** used by Socket RAPL. The IMON telemetry path carries real-time power/current data from the voltage regulator to PrimeCode. PrimeCode uses this telemetry as the primary feedback signal for all Socket RAPL NN-PID control loops. Without accurate IMON data, Socket RAPL cannot enforce power limits correctly.

**SVID** = Serial Voltage ID -- the serial interface between the processor and external VR (Voltage Regulator). In addition to VID (voltage set) commands, SVID carries IMON telemetry back to PrimeCode.

**Key distinction**: This TCD validates the **IMON telemetry reporting path** (addressing correctness, telemetry values, and SVID interface integrity). The Socket RAPL control algorithm itself is covered by **[TCD 22022420798](https://hsdes.intel.com/appstore/article-one/#/22022420798)**.

### SVID IMON Architecture

```
+-------------------------------------------------------------------------+
| Voltage Regulator (VR)                                                  |
|  Generates IMON signal proportional to output current / power           |
+-----------------------------+-------------------------------------------+
                              |
                              | SVID serial interface (IMON telemetry)
                              v
+-------------------------------------------------------------------------+
| NIO PrimeCode -- SVID IMON Receiver                                     |
|  Reads IMON via SVID polling (FIVR_INPUT_VOLTAGE + IMON)                |
|  Converts IMON reading to estimated power (P = V x I)                  |
|  Feeds power estimate into Socket RAPL NN-PID controllers               |
+-----------------------------+-------------------------------------------+
                              |
                              | IMON-derived power estimate
                              v
+-------------------------------------------------------------------------+
| Socket RAPL NN-PID Controllers (9 loops)                                |
|  Use IMON-derived power to compute RAPL_PERF_LIMIT                      |
|  Distribute freq ceiling to CBBs via HPM 0x14                          |
+-------------------------------------------------------------------------+
```

### Functional Scope

- **IMON addressing**: correct SVID address used for each power domain
- **IMON telemetry accuracy**: IMON values fall within expected range for given workload
- **Telemetry path integrity**: IMON data is received and consumed by PrimeCode correctly
- **ENERGY_STATUS correlation**: TPMI ENERGY_STATUS reflects power consistent with IMON-derived measurement

### NWP Applicability

SVID IMON reporting is **fully supported on NWP**. PrimeCode on the NIO die reads IMON via SVID to feed Socket RAPL PID loops. NWP uses the same SVID-based IMON telemetry path as DMR.

### TC Coverage Map

| TC | Scope | Key Validation |
|----|-------|----------------|
| [22022422042 -- RAPL IMON Addressing and Telemetry](https://hsdes.intel.com/appstore/article-one/#/22022422042) | SVID IMON addressing and telemetry | Correct SVID IMON address for each domain; IMON values in expected range; TPMI ENERGY_STATUS consistent with IMON-derived power estimate |

---

## Section 2: Interfaces and Protocols

| Interface | Path / Register | Description |
|-----------|----------------|-------------|
| SVID | VR <-> NIO PrimeCode | Serial interface carrying VID commands (outbound) and IMON telemetry (inbound) |
| IMON telemetry | SVID IMON register | Current monitor value from VR; units: platform-specific (typically mA or % of max) |
| TPMI ENERGY_STATUS | sv.socket0.nio.punit.tpmi.socket_rapl.energy_status | Software-visible energy accumulation; driven by IMON-based power estimate |
| FIVR_INPUT_VOLTAGE | Internal PrimeCode | VR input voltage; used with IMON to compute power estimate (P = V x I) |

---

## Section 3: Reset, Power, and Clocking

- SVID interface initializes during early boot (before PH6 RAPL PID startup)
- IMON telemetry begins after VR brings up the rail and SVID link is established
- After warm reset: SVID link re-establishes; PrimeCode resumes IMON polling at PH6
- ENERGY_STATUS accumulation driven by IMON-based power; resets on cold reset

---

## Section 4: Programming Model

### IMON Addressing Verification

1. Identify expected SVID address for each power domain (from platform spec / BIOS)
2. Verify PrimeCode is polling the correct SVID address for Socket RAPL IMON
3. Read IMON value at known load condition; verify value is in expected range
4. Verify IMON address is not aliased to wrong domain

### Telemetry Accuracy Verification

1. Apply a known stable workload to produce predictable power level
2. Read TPMI ENERGY_STATUS over a known time window
3. Compute average power = delta(ENERGY) / delta(TIME)
4. Compare computed power to expected level for the workload
5. Verify consistency -- power should track workload changes

---

## Section 5: Operational Behavior

- PrimeCode polls SVID IMON periodically (1 ms nominal) to read current power
- IMON value + VR input voltage -> power estimate -> NN-PID input
- If IMON indicates power > PL1 target: PID increases RAPL_PERF_LIMIT restriction
- If IMON indicates power < PL1 target: PID relaxes RAPL_PERF_LIMIT
- ENERGY_STATUS counter accumulates energy derived from IMON-based power estimate

---

## Section 6: Corner Cases & Error Handling

| Scenario | Expected Behavior |
|----------|------------------|
| IMON address incorrect (wrong domain) | RAPL PID receives incorrect power signal; may over- or under-throttle |
| IMON returns zero under full load | PID sees zero power; RAPL_PERF_LIMIT fully relaxed; ENERGY_STATUS stays flat |
| IMON stuck at max value | PID aggressively throttles regardless of actual power |
| SVID link disruption after boot | PrimeCode receives stale IMON; RAPL behavior may be undefined until link recovery |
| ENERGY_STATUS not tracking workload | Indicates IMON telemetry path or unit conversion issue |

---

## Section 7: Security / Safety / Policy

- IMON telemetry is read-only from the processor side
- SVID link integrity is a platform-level concern; processor trusts reported IMON values
- TPMI ENERGY_STATUS is observable by OS; energy fuzzing (MSR 0xBC) may affect visibility

---

## Section 8: References

- [Socket RAPL KB -- socket_rapl.md](../../pm_features/power_rapl/socket_rapl.md) -- IMON telemetry role, SVID architecture, ENERGY_STATUS units
- [TCD 22022420798 -- Socket RAPL Algorithm & Functionality](https://hsdes.intel.com/appstore/article-one/#/22022420798) -- PID algorithm that consumes IMON
- [TCD 22022420821 -- Socket RAPL Registers Verification](https://hsdes.intel.com/appstore/article-one/#/22022420821) -- ENERGY_STATUS register coverage
- [Intel RAPL HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/RAPL/RAPL.html) -- IMON / SVID telemetry architecture
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) -- NWP SVID and power measurement path
- [NWP HAS PM Features](https://docs.intel.com/documents/custom-xeon/newport-docs/has/Overview/NWP_HAS.html)
