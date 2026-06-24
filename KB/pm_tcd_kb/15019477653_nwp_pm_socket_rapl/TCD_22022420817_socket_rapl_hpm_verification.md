# TCD: Socket RAPL HPM Verification

| Field | Value |
|-------|-------|
| **TCD ID** | [22022420817](https://hsdes.intel.com/appstore/article-one/#/22022420817) |
| **Title** | Socket RAPL HPM Verification |
| **Status** | open |
| **Owner** | mps |
| **Parent TP** | [15019477653 -- NWP PM Socket RAPL](https://hsdes.intel.com/appstore/article-one/#/15019477653) |
| **Siblings** | [22022420798 -- Algorithm & Functionality](https://hsdes.intel.com/appstore/article-one/#/22022420798) . [22022420806 -- Cross-products](https://hsdes.intel.com/appstore/article-one/#/22022420806) . [22022420813 -- Fuse and BIOS Knobs](https://hsdes.intel.com/appstore/article-one/#/22022420813) |
| **KB last updated** | 2026-06-24 |
| **Feature** | Power / RAPL -- Socket RAPL HPM messaging |

## Section 1: Architecture / Micro-architecture and Functionality

This TCD verifies the **Hierarchical Power Management (HPM)** messaging path used by **Socket RAPL** on NWP. Socket RAPL enforcement depends on successful delivery of the resolved performance ceiling from PrimeCode on the **NIO** root die to each **CBB PCode**. The same path returns CBB-side status back to the root controller. Correct HPM operation is therefore required for correct end-to-end Socket RAPL behavior.

This TCD covers the **transport and application path** for Socket RAPL HPM messages. Base algorithm coverage belongs to **[TCD 22022420798](https://hsdes.intel.com/appstore/article-one/#/22022420798)**.

### Functional Scope

- Transmission of **RAPL_PERF_LIMIT** from NIO PrimeCode to each active CBB
- Receipt and enforcement of the delivered performance ceiling on each CBB
- Return of **LEAF_PERF_STATUS** from each CBB to the NIO root
- Observable throttle behavior consistent with HPM-delivered RAPL limits
- HPM behavior across throttle assertion, removal, and reset recovery

### Block Diagram

```
+--------------------------------------------------------------------------+
| Boot / Configuration                                                     |
|                                                                          |
|  +---------------+  programs   +----------------------------------+      |
|  |  BIOS / FW    |------------>| TPMI Socket RAPL Regs            |      |
|  |  Setup        |             | PL1_CONTROL, PL2_CONTROL, PL_INFO|      |
|  +---------------+             +------------------+---------------+      |
|                                                   | runtime inputs       |
+---------------------------------------------------+----------------------+
                                                    |
                                                    v
+--------------------------------------------------------------------------+
| NIO Root Control                                                         |
|  +--------------------------------------+                                |
|  | NIO PrimeCode - Socket RAPL Root     |                                |
|  |  reads telemetry                     |                                |
|  |  computes RAPL_PERF_LIMIT (NN-PID)   |                                |
|  +---------------------+----------------+                                |
+------------------------+------------------------------------------------+
                         |
                         | HPM 0x14 : RAPL_PERF_LIMIT (freq ceiling)
                         v
+--------------------------------------------------------------------------+
| HPM Messaging Fabric                                                     |
|  Downstream: NIO -> CBBs  =  HPM 0x14 : RAPL_PERF_LIMIT                 |
|  Upstream:   CBBs -> NIO  =  HPM 0x16 : LEAF_PERF_STATUS                |
+------------------+-------------------------------------+-----------------+
                   |                                     |
                   v                                     v
+---------------------------+            +---------------------------+
| CBB0 PCode / Enforcement  |            | CBB1 PCode / Enforcement  |
|  applies freq ceiling     |            |  applies freq ceiling     |
|  updates throttle state   |            |  updates throttle state   |
+-----------+---------------+            +---------------+-----------+
            | HPM 0x16                                   | HPM 0x16
            +----------------------+---------------------+
                                   |
                                   v
                    +------------------------------+
                    | NIO PrimeCode / Root Status  |
                    |  receives LEAF_PERF_STATUS   |
                    |  adjusts PID feedback        |
                    +------------------------------+
                                   |
                                   | software-visible observability
                                   v
+--------------------------------------------------------------------------+
| TPMI Status / Telemetry                                                  |
|  PERF_STATUS   -- per-CBB throttle counter                               |
|  ENERGY_STATUS -- socket power / energy observation                     |
+--------------------------------------------------------------------------+
```

### HPM Message Roles

| Message | Direction | Function |
|---------|-----------|----------|
| HPM 0x14 | NIO -> CBB | Carries RAPL_PERF_LIMIT -- effective frequency ceiling resolved by PrimeCode |
| HPM 0x16 | CBB -> NIO | Returns LEAF_PERF_STATUS -- CBB-side throttle feedback to root |

### NWP Applicability

NWP uses single NIO root + 2 CBBs + Socket RAPL HPM distribution. This TCD shall verify that RAPL_PERF_LIMIT reaches **both CBB0 and CBB1** and that feedback is correctly returned to the NIO root.

### TC Coverage Map

| TC | Scope | Key Validation |
|----|-------|----------------|
| [22022422019 -- RAPL HPM verification](https://hsdes.intel.com/appstore/article-one/#/22022422019) | HPM path checkout | RAPL_PERF_LIMIT delivered from NIO to both CBBs; enforcement observable on both; LEAF_PERF_STATUS feedback returned; no stale or inconsistent limit behavior |

---

## Section 2: Interfaces and Protocols

| Interface | Message / Register | Direction | Description |
|-----------|-------------------|-----------|-------------|
| HPM 0x14 | RAPL_PERF_LIMIT | NIO -> CBB0, CBB1 | Frequency ceiling (100 MHz units) from PrimeCode NN-PID output |
| HPM 0x16 | LEAF_PERF_STATUS | CBB -> NIO | CBB throttle status feedback; used by PrimeCode for PID adjustment |
| TPMI | PERF_STATUS | Software read | Throttle counter; increments when RAPL_PERF_LIMIT is enforced |
| TPMI | ENERGY_STATUS | Software read | Power accumulation; validates RAPL enforcement is real |
| NWP namednodes | sv.socket0.cbb{0,1}.base.tpmi.perf_status | Read | Per-CBB throttle counter verification |

---

## Section 3: Reset, Power, and Clocking

- HPM messaging is initiated by PrimeCode after PH6 initialization
- After warm reset, HPM messaging resumes with re-initialized PID state
- No stale RAPL_PERF_LIMIT shall remain active after reset -- CBBs receive a fresh message at PH6 exit
- HPM path between NIO and CBB is over D2D / UCIe link -- link integrity is a prerequisite

---

## Section 4: Programming Model

The HPM verification flow shall confirm that Socket RAPL command and feedback messaging are functioning end-to-end.

### Verification Flow

1. Program Socket RAPL PL1 to a value below current workload demand
2. Apply sufficient workload to trigger Socket RAPL throttling
3. Observe throttle indication on **CBB0** and **CBB1**
4. Verify TPMI PERF_STATUS increments on throttled CBBs
5. Verify effective operating frequency reflects the applied RAPL ceiling
6. Verify TPMI ENERGY_STATUS is consistent with enforced throttling
7. Remove the throttle condition
8. Verify the effective ceiling relaxes and performance recovers

Both **CBB0** and **CBB1** shall be checked. Runtime observation shall use **TPMI** (NIO path). Verification infers correct HPM delivery through consistent throttle accounting, effective frequency reduction, and recovery behavior.

---

## Section 5: Operational Behavior

Under normal Socket RAPL operation, PrimeCode periodically distributes RAPL_PERF_LIMIT to each CBB via HPM 0x14; each CBB enforces the ceiling locally; LEAF_PERF_STATUS feedback is returned via HPM 0x16.

**No throttle condition**: PERF_STATUS does not increment; effective frequency unconstrained by Socket RAPL.

**Throttle condition present**: PERF_STATUS increments on affected CBBs; effective frequency limited to active Socket RAPL ceiling.

**Throttle condition removed**: effective frequency recovers; PERF_STATUS ceases incrementing; new status reflects relaxed limit.

---

## Section 6: Corner Cases & Error Handling

| Scenario | Expected Behavior |
|----------|------------------|
| RAPL_PERF_LIMIT = 0 (unconstrained) | CBBs run at max available frequency; PERF_STATUS unchanged |
| RAPL_PERF_LIMIT < Pm | PrimeCode asserts fast_throttle; clock division applied; PERF_STATUS increments |
| Only one CBB throttled | PERF_STATUS increments only on throttled CBB |
| HPM 0x14 message loss | CBB holds last received limit; potential drift detected via PERF_STATUS stale count |
| Warm reset during active throttle | RAPL_PERF_LIMIT reset; new ceiling sent after PH6; no residual throttle |

---

## Section 7: Security / Safety / Policy

- RAPL HPM messaging is internal to the SoC and not directly accessible from OS
- TPMI PERF_STATUS is the OS-visible proxy for observing HPM-driven throttle events
- No security-sensitive data in HPM messages

---

## Section 8: References

- [Socket RAPL KB -- socket_rapl.md](../../pm_features/power_rapl/socket_rapl.md) -- NN-PID architecture, HPM 0x14/0x16 topology
- [TCD 22022420798 -- Socket RAPL Algorithm & Functionality](https://hsdes.intel.com/appstore/article-one/#/22022420798) -- runtime PID algorithm coverage
- [Intel RAPL HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/RAPL/RAPL.html) -- HPM message format
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) -- NIO to CBB HPM path
- [NWP HAS PM Features](https://docs.intel.com/documents/custom-xeon/newport-docs/has/Overview/NWP_HAS.html)
