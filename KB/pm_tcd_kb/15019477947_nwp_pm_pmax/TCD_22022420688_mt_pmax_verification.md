# TCD: MT PMax Verification

| Field | Value |
|-------|-------|
| **TCD ID** | [22022420688](https://hsdes.intel.com/appstore/article-one/#/22022420688) |
| **Title** | MT PMax Verification |
| **Status** | open |
| **Parent TPF** | [15019477947 - NWP PM PMAX](https://hsdes.intel.com/appstore/article-one/#/15019477947) |
| **Feature** | PMAX |
| **NWP Disposition** | Runnable_On_N-1 |
| **KB last updated** | 2026-06-25 |

## Section 1: Architecture / Micro-architecture and Functionality

**Multi-Threshold PMax (MT-PMax)** protects against VccIN overcurrent by sensing FIVR input voltage and triggering frequency throttle before hardware damage occurs. NWP: single VCCIN on NIO (not dual like DMR-AP); one PMax detector on imh0.

**Four throttle levels (DMR MT-PMax + PMax HAS):**

| Level | Threshold | Response | Timing |
|-------|-----------|----------|--------|
| Hard (Vtrip 0) | Lowest V = highest overcurrent | D2D fast-throttle wire to Psafe freq | ~50 ns |
| Soft L1 (Vtrip 1) | Medium | PWM proportional via D2D YY_FAST_THROTTLE_IN_1 | ~500 µs |
| Soft L2 (Vtrip 2) | Softest | Lightest PWM duty cycle; walk-back algorithm | ~500 µs |
| FDD | Fast Droop Detection | Architectural throttle via separate aggregator | ~100 ns |

PrimeCode computes Psafe frequency ceilings at PH6 from fused P-F curves; distributes via HPM PMAX_FREQUENCY_LIMIT to CBBs. On hard trigger: HPM PMAX_INST_PWR_CONTROLLED_FREQ_LIMIT sent.

Soft throttle walk-back: ratio = IO_ACCUMULATED_THROTTLE_CYCLES / ELAPSED_TIME; ramp up if ratio < 5%; penalize if ratio > 8%.

**NWP delta:** single NIO root die; 2 CBBs (cbb0+cbb1); root = sv.socket0.nio.punit.*; no IMH1.

### Block Diagram

`
VccIN VR (single on NWP)
       |
       v
MT-PMax Detector (imh0/NIO)
  Vtrip 0 -> D2D fast-throttle ~50ns
  Vtrip 1 -> PWM FAST_THROTTLE_IN_1 ~500us
  Vtrip 2 -> Soft walk-back ~500us
  FDD     -> Architectural throttle ~100ns
       |
       v
PrimeCode / Punit (NIO)
Psafe ceilings from fused P-F curves
HPM PMAX_FREQUENCY_LIMIT / PMAX_INST_PWR_CONTROLLED_FREQ_LIMIT
       |
  +----+----+
  v         v
CBB0      CBB1
Psafe      Psafe
ceiling    ceiling
LEAF_PERF_STATUS via HPM 0x16
`

### TC Coverage Map

| TC ID | Title | NWP Disposition |
|-------|-------|----------------|
| [22022421764](https://hsdes.intel.com/appstore/article-one/#/22022421764) | PMAX CONTROL Register Verification | Runnable_On_N-1 |
| [22022421770](https://hsdes.intel.com/appstore/article-one/#/22022421770) | PMAX Soft Throttle Verification using FT PMAX INJECT | Runnable_On_N-1 |
| [22022421773](https://hsdes.intel.com/appstore/article-one/#/22022421773) | PMAX Disable Verification | Runnable_On_N-1 |
| [22022421775](https://hsdes.intel.com/appstore/article-one/#/22022421775) | PMAX Hard Throttle Verification using Global PMAX Inject | Runnable_On_N-1 |

---

## Section 2: Interfaces and Protocols

| Interface | Register / Path | Purpose |
|-----------|----------------|---------|
| pmax_control | sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.pmax_control | PMAX_VTRIP_0_OFFSET (signed 7-bit, 2mV/LSB); LOCK; disable_mask |
| package_therm_status.pmax_log | sv.socket0.imh0.punit.throttle.package_therm_status.pmax_log | Throttle event log; set on any PMAX event |
| perf_limit_reasons | sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.perf_limit_reasons | MT-PMAX PLR bit (bit 8) |
| global_pmax_inject | sv.socket0.imh0.pcodeio_map.io_pmax_config.global_pmax_inject | DFX inject for hard throttle testing |
| punit_supervises_pmax | sv.socket0.imh0.punit.throttle.pmax_service.punit_supervises_pmax | 1 = Punit manages PMAX response |
| punit_root_supervisor | sv.socket0.imh0.punit.throttle.pmax_service.punit_root_supervisor | 0 = hard path; 1 = soft path |
| IO_ACCUMULATED_THROTTLE_CYCLES | sv.socket0.imh0.punit.IO_ACCUMULATED_THROTTLE_CYCLES | Soft throttle PWM counter |

---

## Section 3: Reset, Power, and Clocking

- MT-PMax hardware detector always active when VCCIN powered
- pmax_control programmed by BIOS at CPL3; LOCK=1 before OS handoff
- Psafe ceilings computed at PH6 from fused P-F curves; sent to CBBs
- pmax_log SW-clearable; IO_ACCUMULATED_THROTTLE_CYCLES resets on warm reset

---

## Section 4: Programming Model

- pmax_control.pmax_disable_mask: 00=MT enabled, 01=no hard, 10=no soft, 11=both disabled
- pmax_control.lock: BIOS sets before OS; register read-only after
- DFX inject path: global_pmax_inject + global_pmax_latch_bypass (no real VccIN droop needed)
- pmax_vtrip_0_offset: signed 7-bit offset to Vtrip threshold (2 mV/LSB resolution)

---

## Section 5: Operational Behavior

**Hard throttle entry:**
1. VccIN droops below Vtrip 0; detector asserts D2D fast-throttle (~50 ns)
2. CBBs instantly clock-throttle cores to Psafe
3. PrimeCode sends HPM PMAX_INST_PWR_CONTROLLED_FREQ_LIMIT
4. After 500 µs: soft throttle walk-back engages (IO_ACCUMULATED_THROTTLE_CYCLES counter)

**Exit flow:** VccIN recovers; detector deasserts; GLOBAL_PMAX_SEMAPHORE=0 / GLOBAL_PMAX_RESET=1; freq walks back.

---

## Section 6: Corner Cases & Error Handling

| Scenario | Expected Behavior |
|----------|-----------------|
| Hard throttle + RAPL simultaneously | min(PMax Psafe, RAPL ceiling) enforced; both PLR bits set |
| PMAX disabled (disable_mask=0x3) | No throttle on inject; pmax_log = 0 |
| pmax_control.lock=1 | Register read-only; BIOS value preserved at runtime |
| pmax_log stuck | Stale semaphore; clear GLOBAL_PMAX_SEMAPHORE |
| CBB count (DMR 4 vs NWP 2) | Loop over cbb0/cbb1 only |

---

## Section 7: Security / Safety / Policy

- MT-PMax is safety-critical hardware protection; pmax_control.lock prevents OS tampering
- DFX inject requires privileged access (BIOS/JTAG level); not accessible from OS ring-3
- Testing must be done in controlled silicon lab with power control and recovery plan

---

## Section 8: References

- [DMR PMax HAS](https://docs.intel.com/documents/pm_doc/src/server/dmr/pm_features/dmr_pmax.html) — Hard/Soft throttle; Psafe ceiling; D2D wire; semaphore clear
- [DMR PMax Detector HAS](https://docs.intel.com/documents/arch_datacenter/pmax/dmr/dmr_pmax_detector_has/dmr_pmax_detector_has.html) — MT thresholds; PMAX_CONTROL fields; LOCK; disable_mask
- [MT PMax HAS](https://docs.intel.com/documents/pm_doc/src/server/gnr/features/multi-threshold_pmax_detector/mt_pmax.html) — Multi-threshold architecture; PLR bit definitions
- [Newport NIO GPIO HAS](https://docs.intel.com/documents/custom-xeon/newport-docs/has/gpio/newport_nio_gpio_has.html) — PMAX_TRIGGER_IO; single VCCIN NWP topology
