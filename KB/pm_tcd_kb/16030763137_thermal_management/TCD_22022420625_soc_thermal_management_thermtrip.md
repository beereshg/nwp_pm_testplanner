# TCD: [SoC Thermal Management] Thermtrip

| Field | Value |
|-------|-------|
| **TCD ID** | [22022420625](https://hsdes.intel.com/appstore/article-one/#/22022420625) |
| **Title** | [SoC Thermal Management] Thermtrip |
| **Status** | open |
| **Parent TP** | [16030763137 -- NWP PM Thermal Management](https://hsdes.intel.com/appstore/article-one/#/16030763137) |
| **Feature** | SoC Thermal |
| **Sub-Feature** | ThermTrip — disable mechanisms (fuse/TAP register) |
| **NWP Disposition** | Runnable_On_N-1 |
| **KB last updated** | 2026-06-25 |

## Section 1: Architecture / Micro-architecture and Functionality

**Thermtrip** is the **catastrophic thermal shutdown path** — not a normal throttling flow. It is triggered when temperature exceeds safe operating limits requiring immediate power removal to prevent permanent damage. Every die hosts a bidirectional `THERMTRIP_N` pin wire-ORed across dice and connected to the package bump. HWRS is responsible for the catastrophic action: **asserting `THERMTRIP_N`**, **shutting down all FIVRs/PLLs**, and signaling the platform to shut down **MBVRs**.

**Key architectural facts (from Newport PM MAS + DMR Thermal HAS + Wave3 Socket Thermal HAS + HWRS MAS):**
- DTS thermtrip daisy-chained across instances; an **always-on DTS** preserves thermtrip availability independent of ordinary power gating
- Thermtrip generation path is **asynchronous** — no flops in the critical combinational outbound path
- Once asserted, thermtrip is **sticky** until reset clears it
- HWRS combines: local DTS-chain thermtrip, remote `xxTHERMTRIP_N`, and Punit `o_punit_cattrip` / `o_punit_thermtrip` contributions
- `THERMTRIP_N` on one die → all dielets see it (bidirectional bump) and shut down local FIVRs/PLLs
- Before valid fuse download and first DTS measurement, `THERMTRIP_N` must not be interpreted as a valid runtime thermal event

### Block Diagram

```
  Local DTS / Early DTS / Chained DTS
  (each can contribute catastrophic thermal indication)
         |
         v
  Thermtrip Aggregation (DTS daisy chain / die OR)
  + remote xxTHERMTRIP_N from other dice
         |
         v
  HWRS — Catastrophic Logic
  (async, no flops in outbound path)
  Enable/disable: HWRS_EB_FUSE_DWORD0.THERMTRIP_ENABLE
                  HWRS_SEQ_CONTROL.THERMTRIP_ENABLE
         |                        |
         v                        v
  THERMTRIP_N                Internal Shutdown
  GPIO / package pin         FIVRs + PLLs (all dielets)
  (wire-ORed, bidirectional)  Platform MBVR shutdown
  Sticky until reset
         |
         v
  Platform / BMC / PSU — shuts down socket power / MBVRs

  [IMH root-die + CBB0 + CBB1 each participate in
   multi-die thermtrip propagation and FIVR/PLL shutdown]
  TPMI / MSR / PMSB: limited observability / debug context
```

### TC Coverage Map

| TC ID | Title | NWP Disposition |
|-------|-------|----------------|
| [22022421666](https://hsdes.intel.com/appstore/article-one/#/22022421666) | [Thermtrip] Verify Thermtrip Disable | Runnable_On_N-1 |
| [22022421671](https://hsdes.intel.com/appstore/article-one/#/22022421671) | [Thermtrip] Verify Thermtrip shuts down all FIVRs and MBVRs | Runnable_On_N-1 |
| [22022421672](https://hsdes.intel.com/appstore/article-one/#/22022421672) | [Thermtrip] Verify functionality of thermtrip pin from various sources | Runnable_On_N-1 |

### TC Coverage Map

| TC ID | Title | NWP Disposition |
|-------|-------|----------------|
| [22022421666](https://hsdes.intel.com/appstore/article-one/#/22022421666) | [Thermtrip] Verify Thermtrip Disable | Runnable_On_N-1 |
| [22022421671](https://hsdes.intel.com/appstore/article-one/#/22022421671) | [Thermtrip] Verify Thermtrip shuts down all FIVRs and MBVRs | Runnable_On_N-1 |
| [22022421672](https://hsdes.intel.com/appstore/article-one/#/22022421672) | [Thermtrip] Verify functionality of thermtrip pin from vario | Runnable_On_N-1 |

---

## Section 2: Interfaces and Protocols

| Interface | Path | Purpose |
|-----------|------|---------|
| **`THERMTRIP_N`** | Package GPIO pin (bidirectional die bump) | Catastrophic thermal output to platform; wire-ORed across dice |
| **HWRS** | Per-die hardware reset sequencer | Aggregates thermtrip sources; drives async shutdown; applies enable/disable |
| **DTS / Early DTS chain** | Per-die thermal sensors (daisy-chained) | Detect catastrophic over-temp; always-on DTS ensures coverage during power-gated states |
| **`HWRS_EB_FUSE_DWORD0.THERMTRIP_ENABLE`** | HWRS fuse / EB register | Enable/disable control for thermtrip path (supports TC: Verify Thermtrip Disable) |
| **`HWRS_SEQ_CONTROL.THERMTRIP_ENABLE`** | HWRS sequencer control | Runtime enable/disable for thermtrip reporting |
| **FIVRs / PLLs** | Per-die power/clock resources | Shut down immediately on catastrophic trip internal feedback |
| **Platform / BMC / PSU** | External to SoC | Observe `THERMTRIP_N`; shut down MBVRs / socket power |
| TPMI / PMSB | `sv.socket0.imh0.punit.ptpcfsms.*` | Limited observability for status/debug (not in critical thermtrip path) |

---

## Section 3: Reset, Power, and Clocking

- Thermtrip is an **always-available catastrophic protection path** — not a slow-loop policy feature
- The outbound `THERMTRIP_N` path is **asynchronous** with no flops in the critical combinational path
- Once asserted, thermtrip is **sticky**; only reset clears it
- Before valid fuse download and first DTS measurement, `THERMTRIP_N` must not be interpreted as a valid runtime thermal event
- An **always-on DTS** provides thermtrip coverage independent of ordinary FIVR-powered sensor availability (needed because regular sensors may be unreliable at catastrophic temperatures)
- In a multi-die NWP package, thermtrip on one die propagates to all dielets; each local HWRS shuts down its FIVRs/PLLs
- Thermtrip remains available across SoC operating states (except Sx / powered off)

---

## Section 4: Programming Model

Thermtrip is primarily a **hardware-protection path** with limited enable/disable controls:

- **`HWRS_EB_FUSE_DWORD0.THERMTRIP_ENABLE`** — fuse/EB-based enable; controls whether thermtrip path is active
- **`HWRS_SEQ_CONTROL.THERMTRIP_ENABLE`** — runtime sequencer enable for thermtrip reporting
- **`SCU_TRIP_ENABLE`** — HWRS glue logic enable for SCU/Punit-provided trip contribution (`o_punit_cattrip`, `o_punit_thermtrip`)
- Fuse- and TAP-based disable capability exists for bring-up / debug purposes; must not be used in production
- No BIOS/OS MSR programming required for the catastrophic path itself; enable/disable is pre-boot configuration
- Test methodology: controlled forced thermtrip injection in lab environment with appropriate power controls

---

## Section 5: Operational Behavior

**Thermtrip entry flow:**
1. Local DTS / early DTS / chained DTS detects catastrophic over-temperature, **OR** remote die asserts `xxTHERMTRIP_N`
2. Aggregated thermtrip indication reaches HWRS (asynchronous path — no flops in critical combinational outbound)
3. HWRS evaluates enable controls (`HWRS_EB_FUSE_DWORD0.THERMTRIP_ENABLE`, `HWRS_SEQ_CONTROL.THERMTRIP_ENABLE`)
4. If enabled: HWRS asserts `THERMTRIP_N` (sticky) and propagates catastrophic internal shutdown signal
5. **All FIVRs and PLLs within the die shut down** immediately via internal catastrophic feedback
6. In multi-die NWP package: `THERMTRIP_N` is wire-ORed; all dielets observe assertion and shut down local power/clock resources
7. **Platform observes `THERMTRIP_N`** and shuts down MBVRs / socket power

**Post-thermtrip:**
- Assertion remains sticky until reset clears it
- System must be fully powered off and thermally recovered before re-energization

---

## Section 6: Corner Cases & Error Handling

| Scenario | Expected Behavior |
|----------|-----------------|
| Thermtrip asserted before fuse download / first valid DTS measurement | Must not be interpreted as valid runtime thermal event |
| Local DTS thermtrip vs remote die `xxTHERMTRIP_N` | Both should result in local FIVR/PLL shutdown and `THERMTRIP_N` assertion |
| Thermtrip disable control active (`HWRS_EB_FUSE_DWORD0` or `HWRS_SEQ_CONTROL`) | Catastrophic path blocked per control setting; `THERMTRIP_N` should not assert |
| Thermtrip asserted while clocks are unstable | Path still functions — asynchronous, not dependent on regular clocked control |
| One die trips in multi-die NWP package | All dielets observe wire-OR assertion and shut down local FIVRs/PLLs |
| Thermtrip asserted and thermal cause subsequently clears | Assertion remains sticky until reset — no automatic deassertion |
| Punit `o_punit_cattrip` contribution enabled | HWRS combined input generates thermtrip-class shutdown via SCU_TRIP_ENABLE path |

---

## Section 7: Security / Safety / Policy

- Thermtrip is a **safety-critical hardware protection path** — validation must only be performed in controlled lab environments
- Forcing thermtrip intentionally will shut down FIVRs, PLLs, and platform MBVRs; requires appropriate power control and system recovery plan
- Fuse/TAP-based disable controls (`HWRS_EB_FUSE_DWORD0.THERMTRIP_ENABLE`) are bring-up / debug controls; must not be used in production
- Test injection of thermtrip requires privileged access (JTAG/BIOS level); not accessible from OS ring-3

---

## Section 8: References

- [Newport PM MAS -- Thermtrip / HWRS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) -- HWRS local/remote thermtrip aggregation; FIVR/PLL shutdown; always-on DTS
- [Newport GPIO HAS](https://docs.intel.com/documents/custom-xeon/newport-docs/has/gpio/newport_nio_gpio_has.html) -- THERMTRIP_N pin behavior; bidirectional die bump; fuse-download timing
- [DMR Thermal HAS](https://docs.intel.com/documents/pm_doc/src/server/dmr/pm_features/thermals/dmr_thermal.html) -- DMR thermtrip architecture; asynchronous path; HWRS responsibility
- [Wave3 Socket Thermal Management HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Socket_Thermal_Mgmt/Socket_Thermal_Mgmt_HAS.html) -- multi-die wire-OR thermtrip; always-on DTS; catastrophic behavior
- [HWRS MAS](https://docs.intel.com/documents/arch_datacenter/dmr_mas/rcf/hwrs/hwrs_mas.html) -- HWRS_EB_FUSE_DWORD0.THERMTRIP_ENABLE; HWRS_SEQ_CONTROL; SCU_TRIP_ENABLE; cattrip/thermtrip enable controls
- [GNR/SRF/DMR Clock SOC HAS](https://docs.intel.com/documents/arch_datacenter/RCF/Clock/GNR_SRF_DMR/GNR_SRF_DMR_Clock_SOC_HAS.html) -- PLL/clock shutdown behavior on thermtrip
