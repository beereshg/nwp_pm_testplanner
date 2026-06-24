# TCD: Socket RAPL Registers Verification - CSR and TPMI

| Field | Value |
|-------|-------|
| **TCD ID** | [22022420821](https://hsdes.intel.com/appstore/article-one/#/22022420821) |
| **Title** | Socket RAPL Registers Verification - CSR and TPMI |
| **Status** | open |
| **Owner** | mps |
| **Parent TP** | [15019477653 -- NWP PM Socket RAPL](https://hsdes.intel.com/appstore/article-one/#/15019477653) |
| **Siblings** | [22022420798 -- Algorithm & Functionality](https://hsdes.intel.com/appstore/article-one/#/22022420798) . [22022420806 -- Cross-products](https://hsdes.intel.com/appstore/article-one/#/22022420806) . [22022420813 -- Fuse & BIOS Knobs](https://hsdes.intel.com/appstore/article-one/#/22022420813) . [22022420817 -- HPM Verification](https://hsdes.intel.com/appstore/article-one/#/22022420817) |
| **KB last updated** | 2026-06-24 |
| **Feature** | Power / RAPL -- Socket RAPL register interface verification |

## Section 1: Architecture / Micro-architecture and Functionality

This TCD verifies the **Socket RAPL register interface** on NWP -- CSR, TPMI, and OOB-visible programming and status paths. It validates that each register behaves correctly per NWP specification and that deprecated interfaces behave as specified.

Base functional behavior is covered by **[TCD 22022420798](https://hsdes.intel.com/appstore/article-one/#/22022420798)**. This TCD covers register-path correctness only.

### Functional Scope

- TPMI: ENERGY_STATUS, PERF_STATUS, PL1_CONTROL, PL2_CONTROL, PL_INFO
- CSR: PKG_RAPL_LIMIT (boot / BIOS path)
- MSR: deprecated legacy RAPL MSRs on NWP
- OOB: PECI-over-MCTP / OOBMSM access to Socket RAPL registers

### NWP-Specific Interface Behavior

- Runtime access via **NIO TPMI**: sv.socket0.nio.punit.tpmi.socket_rapl.*
- MSR 0x610, 0x611, 0x606: **deprecated** on NWP -- reads return 0, writes no-op
- MSR 0xBC (ENERGY_FILTERING_ENABLE): **not deprecated** -- valid on NWP
- OOB access via **OOBMSM / PECI-over-MCTP**

### Register Access Architecture


```
+-------------------------------------------------------------------------+
| Boot / BIOS Programming                                                 |
|                                                                         |
|  BIOS / FW  --programs/locks-->  CSR PKG_RAPL_LIMIT                    |
|      |                                    |                             |
|      | boot-time policy         mirrors / |  initializes               |
|      v                                    v                             |
|  TPMI Socket RAPL Registers  <----->  NIO PrimeCode / Socket RAPL Root |
|    - PL_INFO                                                            |
|    - PL1_CONTROL                                                        |
|    - PL2_CONTROL                                                        |
|    - ENERGY_STATUS                                                      |
|    - PERF_STATUS                                                        |
+-----------------------------+-------------------------------------------+
                              |
                              | in-band runtime access
                              v
+-------------------------------------------------------------------------+
| In-band SW / Validation Access                                          |
|  PythonSV / OS reads and writes TPMI Socket RAPL state via NIO path    |
|  sv.socket0.nio.punit.tpmi.socket_rapl.*                               |
+-----------------------------+-------------------------------------------+
                              |
                              | OOB path
                              v
+-------------------------------------------------------------------------+
| OOB Access Path                                                         |
|  BMC / NM -- PECI-over-MCTP / OOBMSM --> Socket RAPL TPMI registers    |
|  Validates consistency with in-band TPMI reads / writes                |
+-------------------------------------------------------------------------+

+-------------------------------------------------------------------------+
| Deprecated Legacy Interface                                             |
|  MSR 0x610  IA32_PKG_RAPL_LIMIT      -> deprecated on NWP              |
|  MSR 0x611  IA32_PKG_ENERGY_STATUS   -> deprecated on NWP              |
|  MSR 0x606  IA32_PKG_POWER_SKU_UNIT  -> deprecated on NWP              |
|  Expected behavior: reads return 0; writes have no effect              |
+-------------------------------------------------------------------------+
```


### Register Scope by TC

| TC | Register / Interface | Scope |
|----|---------------------|-------|
| [22022422023 -- RAPL Energy status reporting](https://hsdes.intel.com/appstore/article-one/#/22022422023) | TPMI ENERGY_STATUS | Energy counter correctness; monotonic; TIME field; fuzzing via MSR 0xBC |
| [22022422029 -- RAPL MSR checks - Negative test case](https://hsdes.intel.com/appstore/article-one/#/22022422029) | MSR 0x610, 0x611, 0x606 | Deprecated on NWP: reads return 0, writes no-op; negative validation |
| [22022422032 -- RAPL PEM (PnP Excursion Monitor)](https://hsdes.intel.com/appstore/article-one/#/22022422032) | TPMI / RAPL PEM registers | Excursion monitor visibility and behavior |
| [22022422034 -- RAPL PL1/PL2 limits and Tau Verification](https://hsdes.intel.com/appstore/article-one/#/22022422034) | TPMI PL1_CONTROL, PL2_CONTROL | Power-limit and time-window programming / readback; U11.3 encoding |
| [22022422036 -- RAPL Perf limit reasons - Fine and Coarse](https://hsdes.intel.com/appstore/article-one/#/22022422036) | TPMI PERF_STATUS reason fields | Fine / coarse throttle reason reporting; correct reason when PL1 vs PL2 limiting |
| [22022422038 -- RAPL Perf status](https://hsdes.intel.com/appstore/article-one/#/22022422038) | TPMI PERF_STATUS | Throttle accounting behavior; counter increment correctness |
| [22022422040 -- Socket RAPL verification - OOB](https://hsdes.intel.com/appstore/article-one/#/22022422040) | PECI-over-MCTP / OOBMSM | OOB access consistency with in-band TPMI reads / writes |

---

## Section 2: Interfaces and Protocols

| Interface | Register / Path | NWP Path | Description |
|-----------|----------------|----------|-------------|
| TPMI | ENERGY_STATUS | sv.socket0.nio.punit.tpmi.socket_rapl.energy_status | ENERGY [31:0] (0.0625 J/LSB); TIME [63:32] (10 ns); monotonic |
| TPMI | PERF_STATUS | sv.socket0.nio.punit.tpmi.socket_rapl.perf_status | Throttle counter; fine throttle reason bits |
| TPMI | PL1_CONTROL | sv.socket0.nio.punit.tpmi.socket_rapl.pl1_control | PL1 power limit + time window + LOCK |
| TPMI | PL2_CONTROL | sv.socket0.nio.punit.tpmi.socket_rapl.pl2_control | PL2 power limit + time window |
| TPMI | PL_INFO | sv.socket0.nio.punit.tpmi.socket_rapl.pl_info | RO capability: MAX_PL1, MIN_PL, MAX_PL2 |
| MSR 0xBC | IA32_MISC_PACKAGE_CTLS | pd.debug.access_to_msr(0xBC) | ENERGY_FILTERING_ENABLE [0] -- valid, not deprecated |
| MSR 0x610 | IA32_PKG_RAPL_LIMIT | Deprecated | Reads 0; writes no-op on NWP |
| MSR 0x611 | IA32_PKG_ENERGY_STATUS | Deprecated | Reads 0 on NWP |
| MSR 0x606 | IA32_PKG_POWER_SKU_UNIT | Deprecated | Reads 0 on NWP |
| OOB | PECI-over-MCTP / OOBMSM | OOB -> TPMI | BMC/NM Socket RAPL read/write access |
| CSR | PKG_RAPL_LIMIT | BIOS-only | Locked at boot; mirrors TPMI PL1/PL2 |

---

## Section 3: Reset, Power, and Clocking

- ENERGY_STATUS accumulates from boot; resets on cold reset; **not reset on warm reset** -- TC 22022422023 must handle rollover
- PERF_STATUS throttle counter reset behavior on warm reset shall be validated (TC 22022422038)
- PL1_CONTROL / PL2_CONTROL reflect effective post-boot programmed state after reset recovery, consistent with BIOS policy
- OOB access path reinitializes after reset; Socket RAPL TPMI state persists
- Deprecated MSR behavior remains unchanged across resets

---

## Section 4: Programming Model

### Energy / Status Validation

1. Read TPMI ENERGY_STATUS -- verify monotonic (delta > 0 between reads)
2. Verify TIME field increments in 10 ns units
3. Enable energy fuzzing (MSR 0xBC.bit0=1); verify ENERGY_STATUS behavior changes
4. Read TPMI PERF_STATUS under active RAPL throttle -- verify counter increments
5. Read PERF_STATUS reason bits -- verify correct fine/coarse reason when PL1 vs PL2 is limiting

### Control Register Validation

1. Read PL_INFO -- verify MAX_PL1 = TDP, MAX_PL2 = 1.2xTDP, MIN_PL != 0
2. Write PL1_CONTROL.PWR_LIM = target (U11.3, <= MAX_PL1); readback = same
3. Write PL1_CONTROL.TIME_WINDOW = encoded tau; readback = same (within clipping)
4. Verify LOCK bit persists after boot if BIOS configured lock

### Deprecated MSR Negative Tests

1. Write MSR 0x610 -- read back should return 0 (write ignored)
2. Read MSR 0x611 -- should return 0
3. Read MSR 0x606 -- should return 0

### OOB Validation

1. Send PECI-over-MCTP read for Socket RAPL TPMI register
2. Verify returned value matches PythonSV in-band TPMI read
3. Send OOB write; verify consistent with in-band register view

---

## Section 5: Operational Behavior

- **ENERGY_STATUS**: monotonic energy counter; 10 ns TIME field; energy fuzzing support via MSR 0xBC
- **PERF_STATUS**: throttle counter with fine (per-reason) and coarse fields; increments under active RAPL limiting
- **PL1/PL2_CONTROL**: BIOS-programmed limit readback; LOCK enforcement; clipping to fused MAX
- **Deprecated MSRs**: reads return 0; writes are no-ops -- silicon-level enforcement
- **OOB**: TPMI register visibility via BMC/NM path is consistent with in-band access

---

## Section 6: Corner Cases & Error Handling

| Scenario | Expected Behavior |
|----------|------------------|
| ENERGY_STATUS overflow (32-bit) | Counter wraps; test computes delta to handle rollover |
| MSR 0x610 write while RAPL active | Write silently dropped; TPMI PL1_CONTROL unchanged |
| MSR 0x606 read | Returns 0; shall not be used for unit discovery |
| PERF_STATUS fine reason bits | Correct reason bit set when PL1 vs PL2 is the active limiter |
| OOB and in-band read of same register | Values shall be consistent |
| Energy fuzzing enabled + OOB read | OOB may observe fuzzed or unfiltered value per path policy |
| PL1_CONTROL LOCK=1, OOB write attempt | Write rejected via OOB path as well |

---

## Section 7: Security / Safety / Policy

- ENERGY_STATUS fuzzing (MSR 0xBC) is a security feature -- prevents energy side-channel attacks
- Deprecated MSR reads returning 0 prevent legacy SW from using unsupported unit values
- OOB access is authenticated via BMC/platform security policy
- LOCK bit prevents OS from overriding BIOS-programmed limits

---

## Section 8: References

- [Socket RAPL KB -- socket_rapl.md](../../pm_features/power_rapl/socket_rapl.md) -- full register table, TPMI paths, energy/time units
- [TCD 22022420798 -- Socket RAPL Algorithm & Functionality](https://hsdes.intel.com/appstore/article-one/#/22022420798) -- algorithm and enforcement coverage
- [Intel RAPL HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/RAPL/RAPL.html) -- TPMI register definitions, PERF_STATUS bit fields, energy units
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) -- NWP TPMI path, deprecated MSR list
- [NWP HAS PM Features](https://docs.intel.com/documents/custom-xeon/newport-docs/has/Overview/NWP_HAS.html)
