# Power/RAPL > RACL (Running Average Current Limit)

> **Status**: Restructured — NWP delta enriched from MCP HAS/MAS query
> **Parent**: [Power / RAPL](power_rapl_main.md)

## Baseline (DMR)

RACL is a per-VR **Thermal Design Current (TDC)** limiter for dual-VCCIN platforms (DMR+). It regulates each VCCIN VR to its TDC spec by computing a running average current limit and adjusting CPU frequency ceiling accordingly — analogous to RAPL but for current instead of power.

## HW Touchpoints

<!-- TODO: Extract from Legacy content or enrich via MCP HAS query -->
| IP Block | Die | Role | Key Signals / Wires | HAS Reference |
|----------|-----|------|---------------------|---------------|
| | | | | |

## FW Touchpoints

<!-- TODO: Extract from Legacy content or enrich via MCP HAS query -->
| Agent | Location | Role | Key Functions / Handlers | Source |
|-------|----------|------|--------------------------|--------|
| | | | | |

## OS Interfaces

<!-- TODO: Extract from Legacy content or enrich via MCP HAS query -->
| Interface | ID / Address | Access | Description | Spec Reference |
|-----------|-------------|--------|-------------|----------------|
| | | | | |

## NWP Delta

**RACL (Robust Access Control Limiter / per-VR TDC Limiter) is supported on NWP** — reused from DMR.

- Per-VR TDC limiting for dual VCCIN mechanism is reused
- TPMI RAPL reporting interface maintained
- RACL PID output via HPM RACL_PID_FREQ_OUTPUT field

### Validation Impact
- Same RACL test cases apply
- Verify RACL PID frequency output in NWP single-NIO topology

## Legacy (Human-Curated Reference)

### Architecture Summary

RACL is a per-VR **Thermal Design Current (TDC)** limiter for dual-VCCIN platforms (DMR+). It regulates each VCCIN VR to its TDC spec by computing a running average current limit and adjusting CPU frequency ceiling accordingly — analogous to RAPL but for current instead of power.

#### Why RACL Exists (DMR Dual VCCIN)
- **GNR**: Single VCCIN → bulk TDP on one VR → RAPL TDP enforcement implicitly manages TDC
- **DMR**: Dual VCCIN (VCCIN_0 for North iMH + CBB0/1, VCCIN_1 for South iMH + CBB2/3) → per-VR TDC ≠ total TDP → need parallel TDC limiter
- VR FETs are designed to TDC — exceeding it causes VR shutdown. RACL prevents this proactively
- TDC split is not always 50:50; slight overage (~60:60) allowed for imbalance

#### Key Design Points
- **RMS-based**: TDC limit uses RMS average ($TDC^2 - (VCCIN\_VR\_IMON)^2$ fed into EWMA) — VR heating losses are proportional to $I^2$
- **Per-iMH**: Each iMH PrimeCode runs its own RACL PID loop — North iMH for VCCIN_0, South iMH for VCCIN_1
- **Local limit**: Unlike RAPL (global), RACL is local to each iMH — not communicated root→leaf. Each iMH takes min(global RAPL limit, local RACL limit) before sending to its CBBs
- **No customer controllability**: TDC limit is fuse-only (set by binsplit), not SW-configurable. Only observability is exposed
- **Shared IMON**: Reuses existing SVID IMON sampling done for RAPL — no additional IMON reads
- **Slow loop feature**: Runs in Pcode slow loop, post-CPL3

#### Topology
```
North iMH (Root)         South iMH (Leaf)
  ├── VCCIN_0 VR           ├── VCCIN_1 VR
  ├── RACL PID (local)     ├── RACL PID (local)
  ├── CBB0, CBB1           ├── CBB2, CBB3
  └── SVID IMON            └── SVID IMON
```

---

### Execution Flow

#### Control Loop Block Diagram
```
VCCIN_VR_IMON (from SVID) → (IMON)² → [TDC² - IMON²] → EWMA filter → PID Controller → Frequency Ratio Output
                                                              ↑
                                                    FUSE_TDC_LIMIT² (target)
```

#### Initialization
1. PrimeCode reads `FUSE_TDC_LIMIT` per die (10-bit, 1A units). If 0 → RACL disabled (e.g., DMR-SP with single VCCIN)
2. PrimeCode reads `FUSE_TIME_WINDOW` per die (16-bit, 1ms units, range 1–5 sec). Enforced ≤ 5s to align with RAPL
3. EWMA time constant initialized from FUSE_TIME_WINDOW
4. RACL PID controller initialized per iMH die
5. Charge status accumulator initialized to 0

#### Runtime (per iMH, every slow loop iteration)
1. Read VCCIN VR IMON from SVID (shared with RAPL — no extra read)
2. Compute error: $TDC^2 - IMON^2$
3. Feed error into EWMA filter (time window from fuse)
4. PID controller outputs frequency ratio (range 1 to 0xFF for full fabric freq dynamic range)
5. Root iMH PrimeCode packs min(RAPL PIDs, RACL PID, PSYS PID) into RAPL_PERF_LIMIT HPM
6. Leaf iMH PrimeCode takes min(global RAPL limit, local RACL limit) → sends to its CBBs
7. CBB Pcode resolves CLOS_LIMITS (RAPL) vs. RACL_PID_FREQ_OUTPUT → drives CBB frequency
8. If cores limited by RACL, CBB Pcode increments LEAF_PERF_STATUS.RACL_PERF_STATUS counter
9. Update CHARGE_STATUS accumulator (monotonic, 18.14 Coulomb format)
10. Update RACL_PERF_STATUS.PWR_LIMIT_THROTTLE_CTR

#### Mesh Frequency Reduction
When RACL limits frequency, iMH fabric (IO and Mem) frequencies are also reduced per [DMR Fabric DVFS HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_Fabric_DVFS.html#raplracl-limits-for-imh-memory-io-fabric-frequencies) — same mechanism as RAPL fabric freq reduction.

---

### HPM Messages

#### RAPL_PERF_LIMIT (Root iMH → CBBs, opcode in HPM spec)
Root PrimeCode populates:
- **CLOS_LIMITS**: RAPL frequency ceiling (global, per-CLOS)
- **RACL_PID_FREQ_OUTPUT**: min(RACL, RAPL, PSYS) PID freq output. If RACL dominates, this field carries RACL limit
- **Limiter indicator bit**: Identifies which of RAPL/RACL/PSYS is the current limiter

CBB Pcode resolves: final freq = min(CLOS_LIMITS for RAPL, RACL_PID_FREQ_OUTPUT)

**Note**: RACL does not get disabled when PBM is disabled. PrimeCode continues sending RACL limit even if PBM off — CLOS_LIMITS set to 0xFF in that case, PID_FREQ_OUTPUT carries RACL limit.

#### LEAF_PERF_STATUS (CBB → Root iMH, opcode 0x16)
| Bits | Field | Description |
|------|-------|-------------|
| 31:16 | RACL_PERF_STATUS | Running counter of modules limited by RACL |
| 47:32 | SOCKET_RAPL_PERF_STATUS | Running counter of modules limited by Socket RAPL |
| 63:48 | PLATFORM_RAPL_PERF_STATUS | Running counter of modules limited by Platform RAPL |

---

### Key Registers & Interfaces

#### Fuses (per iMH die — can differ between iMH-P and iMH-S)

| Fuse | Bits | Width | Access | Description |
|------|------|-------|--------|-------------|
| FUSE_TDC_LIMIT | 9:0 | 10 | RO | TDC current limit in 1A units. 0 = RACL disabled (e.g., DMR-SP single VCCIN). Per-die, not SW configurable |
| FUSE_TIME_WINDOW | 15:0 | 16 | RO | EWMA time window in 1 ms units. Range 1–5000 ms (5 sec max enforced by PrimeCode). Per-die, not SW configurable |

Both fuses exposed through PMT for customer observability. PrimeCode implements a RACL limit variable that can be sampled dynamically for post-silicon debug.

#### CHARGE_STATUS (per iMH die — 2 instances)

| Bits | Field | Width | Access | Description |
|------|-------|-------|--------|-------------|
| 31:0 | CHARGE | 32 | RO_V | Total charge consumed since last reset. 18.14 format (Coulomb). Monotonic increment, auto-wraps at overflow (~262,144 C). Min resolution ~61 µC |
| 63:32 | TIME | 32 | RO_V | Total time elapsed at last charge update. Unit = 10 ns. Monotonic increment, auto-wraps |

**Overflow**: ≥ 1 minute guaranteed before overflow under any load. Typically no overflow within 4 minutes; most domains take weeks. SW must account for potential overflow in read cadence.

##### Security (RACL Fuzzing)
- Same SCA vulnerability as RAPL ENERGY_STATUS → same mitigation
- RAPL_FILTERING bit enables/disables fuzzing for both RAPL and RACL
- SGX/TDX enabling via OC_SECURE mailbox (same as RAPL)
- ERROR_BAND_PERCENTAGE = **5%** for RACL
- Adaptive error implementation identical to RAPL (DRNG-based randomization)

#### RACL_PERF_STATUS (per iMH die — 2 instances)

| Bits | Field | Width | Access | Description |
|------|-------|-------|--------|-------------|
| 31:0 | PWR_LIMIT_THROTTLE_CTR | 32 | RO_V | Accumulated time the RACL algorithm clipped frequency (increments of $2^{-10}$ sec ≈ 0.977 ms). Range ~50 days |
| 63:32 | RSVD | 32 | RO_V | Reserved |

#### RACL Debug Disable
- **Bit 9** of `IO_PCODE_SYSTEM_MODES_CONTROL2` (a reserved bit repurposed on DMR) disables RACL for PrimeCode controllability/debug

#### Interface Matrix

| Register/Parameter | MSR | IN_TPMI | OOB_TPMI | CSR | Fuses | MB |
|--------------------|-----|---------|----------|-----|-------|----|
| FUSE_TDC_LIMIT | — | — | — | — | RO (per-die) | — |
| FUSE_TIME_WINDOW | — | — | — | — | RO (per-die) | — |
| CHARGE_STATUS | — | — | PMT (RO_V) | — | — | — |
| RACL_PERF_STATUS | — | — | PMT (RO_V) | — | — | — |
| PLR.RACL (coarse) | — | RW0C | RW0C | — | — | PLR_MAILBOX |
| PLR_MAILBOX_DATA.RACL (fine, bit 54) | — | — | — | — | — | PLR_MAILBOX |
| PEM.RACL | — | — | PMT | — | — | — |
| RACL_PID_FREQ_OUTPUT | — | — | — | — | — | HPM |
| RAPL_PERF_LIMIT HPM | — | — | — | — | — | HPM |
| LEAF_PERF_STATUS HPM | — | — | — | — | — | HPM |
| IO_PCODE_SYSTEM_MODES_CONTROL2[9] | — | — | — | RW | — | — |

**Key**: No MSR, no IN_TPMI control, no customer controllability. Only observability (PMT via OOB-MSM). 4 observability counters: CHARGE_STATUS, RACL_PERF_STATUS, PLR (1 bit), PEM (1 bit).

---

### Cross Products

| Feature | RACL Impact |
|---------|-------------|
| **Socket RAPL** | CBB freq = min(RAPL global ceiling, RACL local limit). RACL is local per-iMH; RAPL is global across socket |
| **PSYS (Platform RAPL)** | Root iMH takes min(Platform RAPL, Socket RAPL, RACL) for PID_FREQ_OUTPUT |
| **Fast RAPL** | Independent — Fast RAPL fires in HW, RACL in FW slow loop |
| **SIMPL/DFC** | Independent frequency constraint paths. Both can clip simultaneously |
| **SST-CP / SST-BF / SST-TF** | No RACL cross product — RACL does not input to prioritization flow (minimal perf impact for most scenarios) |
| **SST-PP** | No impact — TDC is a global Pcode fuse, fused to worst-case SST-PP SKU |
| **VR HOT** | No cross product — independent flows |
| **Fabric DVFS** | RACL provides ceiling input to fabric freq. Per [Fabric DVFS HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_Fabric_DVFS.html#raplracl-limits-for-imh-memory-io-fabric-frequencies), RACL limits iMH Mem/IO fabric freq same as RAPL |
| **PBM disable** | RACL continues running even when PBM is disabled. CLOS_LIMITS set to 0xFF; PID_FREQ_OUTPUT carries RACL limit |

---

### TDC Fuse Setting Scenarios

| Scenario | RACL Dominant? | Description |
|----------|---------------|-------------|
| Symmetrical compute | No | Balanced load across both iMHs. RACL headroom sufficient. TDC fuse must not penalize this |
| Asymmetric IO (process variation) | No | Slight die-to-die variation in 2 iMH hubs |
| Asymmetric IO (cloud connectivity) | **Yes** | Unbalanced PCIe/CXL port attachment (e.g., 6L1+2L0 on one iMH). RACL dominates and throttles the overloaded side |
| Balanced cloud WL (core + IO) | No | Customers running balanced workloads get balanced freq |
| Single VCCIN (DMR-SP, **NWP**) | Disabled | FUSE_TDC_LIMIT = 0 → RACL disabled entirely. Socket RAPL manages TDC via TDP enforcement |

Binsplit target: TDC fuse per iMH slightly above 50:50 split (~60:60 allocation per iMH) to handle normal imbalance without triggering RACL.

---

### Source References

#### Primecode (iMH-level firmware)
| # | File | Description |
|---|------|-------------|
| 1 | `src/flow/racl/v1_0/racl.hpp` | RACL class — getRaclFreqLimit(), TDC limit, PID controller state |
| 2 | `src/flow/racl/v1_0/racl.cpp` | RACL implementation — EWMA filter, charge status, TDC limit, PID freq output |
| 3 | `src/flow/racl/v1_0/fuses_racl.xml` | RACL fuse definitions (FUSE_TDC_LIMIT, FUSE_TIME_WINDOW) |
| 4 | `src/flow/rapl/rapl_messaging/rapl_hpm_root/v2_0/rapl_hpm_root.cpp` | HPM root — calls getRaclFreqLimit(), packs RACL_PID_FREQ_OUTPUT into RAPL_PERF_LIMIT |
| 5 | `src/flow/rapl/rapl_bridge/v2_0/rapl_bridge_common.cpp` | Bridge — aggregates per-die RACL perf status |
| 6 | `src/ip/cfc/v2_0/cfc.cpp` | CFC IP — classifies RaplMeshLimitingReason::RACL, increments mesh_racl_perf_status |
| 7 | `src/flow/hpm/hpm_common/v2_0/hpm_mailbox.xml` | HPM mailbox — RAPL_PERF_LIMIT fields: RACL_PID_FREQ_OUTPUT, RACL_PERF_STATUS |

#### Pcode (CBB die-level firmware)
| # | File | Description |
|---|------|-------------|
| 1 | `source/pcode/flows/slow_limits/rapl/rapl.h` | RAPL class — stores racl_limit, dfx_racl_disabled, resolve_ccp_rapl_and_racl_tx() |
| 2 | `source/pcode/flows/slow_limits/rapl/rapl.cpp` | Receives RACL_PID_FREQ_OUTPUT from HPM, applies per-CCP RACL limit via slow_limits |
| 3 | `source/pcode/flows/slow_limits/slow_limits_interface.h` | Defines RACL_ID and CCP_SLR_RACL_ID enum values |
| 4 | `source/pcode/flows/slow_limits/plr/plr.h` | PLR_RACL_ID, num_ccps_limited_by_racl counter |
| 5 | `source/pcode/flows/slow_limits/pem_telemetry.h` | Maps RACL_ID → PEM_RACL (telemetry index 22) |

---

### Collateral Links

| Type | Link | Notes |
|------|------|-------|
| RACL HAS | [RACL VR TDC HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/Dual_VCCIN_RACL_VRTDC/RACL_VR_TDC.html) | Primary spec — dual VCCIN, control loop, fuses, observability, cross products |
| RACL Data | [RACL_sheets.xlsx](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/Dual_VCCIN_RACL_VRTDC/embeddings/RACL_sheets.xlsx) | Fuse definitions, register tables, charge status format |
| HPM Spec | [RAPL_PERF_LIMIT HPM](https://docs.intel.com/documents/primecode/has/DMR/Hierarchical%20PM/HPM_Message_Specification.html#RAPL_PERF_LIMIT) | RACL_PID_FREQ_OUTPUT field, LEAF_PERF_STATUS |
| Fabric DVFS | [RACL/RAPL Limits for Fabric](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_Fabric_DVFS.html#raplracl-limits-for-imh-memory-io-fabric-frequencies) | How RACL limits iMH Mem/IO fabric frequencies |
| Socket RAPL | [DMR RAPL Simplification](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_RAPL_Simplification.html) | RAPL E2E flow — root→leaf RACL integration pseudocode |
| HSD | [PM FW for Dual VCCIN](https://hsdes.intel.com/appstore/article/#/22014810103) | Feature tracking HSD |
| SOC PM HAS | [DMR SoC PM HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/SOC_PM_HAS/DMR_SOC_PM_HAS.html) | Single-VCCIN impact table — RACL suppression |
| Platform PM | [EEPAS](https://docs.intel.com/documents/server-platform-arch/Power%20Management/EEPAS.html) | Platform PM — single VCCIN → RACL not required |
| FHAS | [Primecode RACL FHAS](https://docs.intel.com/documents/primecode/fhas/DMR/RACL/SERVERPMFW-154.html) | Primecode RACL fuse/flow spec |
| PLR HAS | [DMR PLR HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_PLR.html) | PLR bit 54 = RACL (fine grain), coarse CURRENT bit |
| Socket RAPL KB | [socket_rapl.md](socket_rapl.md) | RAPL is global; RACL is local per-iMH — CBB takes min |
| PEM KB | [pem.md](pem.md) | PEM event ID 22 = RACL |
| SIMPL KB | [simpl.md](simpl.md) | SIMPL and RACL are independent frequency constraints |

---

---

### Related Sightings
<!-- No NWP RACL sightings cataloged yet -->

---

### NWP Delta

> **NWP has single VCCIN** — RACL is architecturally unnecessary and is disabled/suppressed. Socket RAPL remains the active package-level limiter.

#### Why RACL Is Not Required on NWP

- **Single VCCIN topology**: NWP uses a single VCCIN rail (like GNR and DMR-SP), not dual VCCIN. With one VR supplying the entire socket, TDP enforcement via Socket RAPL implicitly manages TDC — there is no per-VR current imbalance to protect against.
- **Fuse-level suppression**: `FUSE_TDC_LIMIT = 0` disables RACL entirely. This is the expected fuse setting for single-VCCIN configurations (confirmed in DMR RACL HAS and DMR SoC PM HAS single-VCCIN impact table).
- **Flow suppression**: When FUSE_TDC_LIMIT is 0, Primecode skips RACL PID initialization and does not generate RACL frequency limits. The RACL_PID_FREQ_OUTPUT field in RAPL_PERF_LIMIT HPM is effectively transparent (0xFF = no limit).
- **RAPL remains active**: Socket RAPL and Platform RAPL continue to operate normally. The CBB Pcode RAPL path is unaffected by RACL suppression.

#### Source Confirmation

| Source | Statement |
|--------|-----------|
| [RACL VR TDC HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/Dual_VCCIN_RACL_VRTDC/RACL_VR_TDC.html) | FUSE_TDC_LIMIT = 0 means RACL disabled; applies to single-VCCIN (e.g. DMR-SP) |
| [DMR SoC PM HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/SOC_PM_HAS/DMR_SOC_PM_HAS.html) | Single-VCCIN impact table: "RACL fuse for single rail will be disabled and it will suppress RACL flows" |
| [EEPAS](https://docs.intel.com/documents/server-platform-arch/Power%20Management/EEPAS.html) | Single VCCIN → RACL is not required |
| [Primecode RACL FHAS](https://docs.intel.com/documents/primecode/fhas/DMR/RACL/SERVERPMFW-154.html) | RACL fuse and flow behavior for single-VCCIN |
| GNR precedent | "GNR has one VCCIN ... TDP enforcement manages TDC enforcement as well" |

#### Test Case Applicability

All 16 RACL test cases are marked `Runnable_On_N-1` but will have **limited or no functional coverage on NWP single-VCCIN** since RACL is disabled by fuse. Key validation points shift to:

1. **Fuse verification**: Confirm `FUSE_TDC_LIMIT = 0` per iMH on NWP silicon — this is the primary validation gate
2. **Flow suppression**: Verify RACL PID does not initialize and RACL_PID_FREQ_OUTPUT = 0xFF (no limit) in HPM
3. **CHARGE_STATUS**: Should remain at 0 or not increment (no RACL accounting)
4. **RACL_PERF_STATUS**: PWR_LIMIT_THROTTLE_CTR should remain 0 (no RACL throttling)
5. **PLR bit 54**: Should never assert (no RACL limiting)
6. **PEM event 22**: Should not fire (no RACL throttling)
7. **Socket RAPL**: Verify RAPL continues to enforce TDP correctly as the sole package-level limiter

---

### Validation Starting Points

#### NWP (Single VCCIN — RACL Disabled)
1. **Fuse check**: Read FUSE_TDC_LIMIT per iMH via PythonSV — verify **= 0** (RACL disabled)
2. **Flow suppression**: Verify RACL PID does not initialize. RACL_PID_FREQ_OUTPUT in HPM = 0xFF
3. **Observability zero**: CHARGE_STATUS = 0, RACL_PERF_STATUS.PWR_LIMIT_THROTTLE_CTR = 0, PLR bit 54 = 0, PEM event 22 does not fire
4. **RAPL sole limiter**: Under package-level power limit, verify Socket RAPL throttles correctly without RACL

#### DMR Dual VCCIN (RACL Active — reference)
1. **Fuse check**: Read FUSE_TDC_LIMIT per iMH via PythonSV — verify non-zero (RACL enabled) and matches binsplit expectations
2. **Charge status**: Read RACL_CHARGE_STATUS via PMT — verify monotonic increment under load. Compare CHARGE/TIME ratio to expected VCCIN current
3. **Disable test**: Set IO_PCODE_SYSTEM_MODES_CONTROL2[9] = 1 → verify RACL stops limiting frequency
4. **Symmetric load**: Run identical workload on both iMHs → verify RACL_PERF_STATUS.PWR_LIMIT_THROTTLE_CTR ≈ 0 (RACL should not dominate)
5. **Asymmetric load**: Generate heavy IO traffic on one iMH only → verify RACL throttles the overloaded side while other side is unaffected
6. **PLR**: Under RACL throttling, read PLR_MAILBOX_DATA (domain=core) — verify bit 54 (RACL) set
7. **PEM**: Verify PEM event 22 (RACL) fires during throttling
8. **HPM**: Monitor RAPL_PERF_LIMIT HPM → verify RACL_PID_FREQ_OUTPUT < 0xFF when RACL dominates
