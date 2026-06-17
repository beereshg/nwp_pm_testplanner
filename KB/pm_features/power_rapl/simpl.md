# Power/RAPL > SIMPL (SoC IccMax Proactive Limits)

> **Status**: Restructured — NWP delta enriched from MCP HAS/MAS query
> **Parent**: [Power / RAPL](power_rapl_main.md)

## Baseline (DMR)

SIMPL is a **proactive IccMax protection** feature that dynamically trades off max allowed frequencies across multiple power domains (cores, CBB fabric, iMH IO fabric, iMH Mem fabric) to keep the SoC within predetermined platform power delivery (PD) Iccmax.max limits. It extends the GNR-era DFC (Dynamic Frequency Constraint) from 2 domains on one die to 4 domains across multiple dies.

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

**SIMPL (SoC IccMax Proactive Limits) is supported on NWP** — reused from DMR.

- Proactive power throttling control flows are reused
- Register interface unchanged
- SIMPL operates at socket level via Punit/Pcode

### Validation Impact
- Same SIMPL test cases apply

## Legacy (Human-Curated Reference)

### Architecture Summary

SIMPL is a **proactive IccMax protection** feature that dynamically trades off max allowed frequencies across multiple power domains (cores, CBB fabric, iMH IO fabric, iMH Mem fabric) to keep the SoC within predetermined platform power delivery (PD) Iccmax.max limits. It extends the GNR-era DFC (Dynamic Frequency Constraint) from 2 domains on one die to 4 domains across multiple dies.

#### Design Rationale
- **Pmax.max** is the peak power sustainable for <100 ns — too fast for package/platform caps to mitigate
- **Proactive** (correct-by-construction) vs. reactive (detect→communicate→respond in <10 ns): proactive is simpler, deterministic, and avoids late PD spec thrash
- Real-world workloads do not require max frequency across all domains simultaneously
- Key assumption: **all latency requirements and benchmarks are satisfied at base frequencies** for all domains

#### Domain Priority (highest → lowest)
1. **iMH IO Fabric** — wins vs. all if IO BW demands above base
2. **iMH Mem Fabric** — wins vs. cores if Mem BW demands above base
3. **CBB Core & Fabric** — manages core vs. ring within allocated budget (via DFC)

#### Topology
- **Hub-and-spoke**: Primary iMH is root, secondary iMH and CBBs are leaves
- Root iMH observes global IO/Mem BW telemetry and resolves SIMPL policy
- Leaf iMH can request higher policy via REQUEST_POLICY when local P2P IO traffic is high
- CBBs only act and acknowledge — they never request policy changes
- Two HPM messages: **SIMPL** (opcode 0x20, root→leaf) and **SIMPL_RESPONSE** (opcode 0x21, leaf→root)

#### Customer-Facing Name
SIMPL/DFC is exposed to customers as **PFM** (Priority Frequency Management):
- **PFM-SoC** = SIMPL (cross-die policy)
- **PFM-CBB** = DFC (per-CBB core vs. ring)

---

### DFC — Dynamic Frequency Constraint (SIMPL Subset)

DFC is the per-CBB subset of SIMPL, first implemented on GNR. It trades off max core vs. max CBB CFC (ring) frequency within a single CBB die.

- **Core-bound** scenario: core gets P0nmax, ring clipped by DFC offset bins
- **Cache/mem-bound** scenario: ring gets P0nmax, core clipped by DFC offset bins
- Priority is given to CCF (ring) demand — if heuristics indicate cache/memory bound, ring gets higher limit
- Controlled by fuse `SIMPL_CBB_DFC_EN` and per-policy offset fuses
- Dynamic disable: if active cores < `SIMPL_POLICY_[i]_CBB_DFC_EN_MIN_CORES_ACTIVE`, DFC is disabled to avoid limiting performance when TDP/IccMax headroom exists
- **GVFSM decoupling**: when DFC is enabled, core and ring DVFS must follow Go_Increase_GB → Go_Decrease_GB sequencing for electrical safety. Decoupled once at boot if DFC is enabled.

---

### SIMPL Policies

Policies are a pre-defined set of per-domain frequency limits encoded as a POLICY_NUMBER (3 bits, up to 8 policies). Each die has a fused LUT mapping policy# to constraints.

#### DMR Policy Table (reference, as of 2025ww09)

| Policy# | WL Type | iMH IO Freq Limit | iMH Mem Freq Limit | CBB Core Limit | CBB Fabric Limit |
|---------|---------|-------------------|--------------------|--------------------|---------------------|
| 0 (default) | Core Heavy / IO Light | 1.4 GHz | 1.8 GHz | P0nmax (core-heavy) | P0nmax - Y0 (solve) |
| 1 | IO Med + Mem Light | 2.0 GHz | 1.8 GHz | P0nmax (core-heavy) | P0nmax - Y2 (solve) |
| 2 | IO Med + Mem Heavy | 2.0 GHz | 2.3 GHz | P0nmax (core-heavy) | P0nmax - Y1 (solve) |
| 3 | IO Heavy + Mem Heavy | 2.1 GHz | 2.1 GHz | P0nmax (core-heavy) | P0nmax - Y3 (solve) |

**Notes**:
- CBB core/fabric freq limits are per-TRL (Cdyn level) and per-SST-PP level — solved by binsplit team
- DMR-AP/-SP PoR: **single SIMPL policy** only (fused NUM_SIMPL_POLICIES=1), but feature must still be fully implemented
- Policy numbers are monotonic: core freq decreases and iMH fabric freq increases with higher policy#

#### Policy Resolution (Root iMH)
```
resolved_io_bw_req  = max(leaf_request_policy_io_BW, root_local_io_BW)
resolved_mem_bw_req = max(leaf_request_policy_mem_BW, root_local_mem_BW)
resolved_simpl_policy = f(resolved_io_bw_req, resolved_mem_bw_req)
```

#### IO BW → IO Fabric Frequency Mapping
| IO BW (GB/s) | IO Fabric Freq (GHz) |
|-------------|---------------------|
| < 30 | 0.8 |
| 30–300 | 1.4 |
| 300–650 | 1.8–2.0 |
| > 650 | 2.0–2.5 |

#### Mem BW → Mem Fabric Frequency Mapping (varies by IO Fabric Freq)
| B2IO/B2CA Util | Mem BW (GB/s) | IO Fabric (GHz) | Mem Fabric (GHz) |
|---------------|-------------|-----------------|-----------------|
| 0% | 0–26 | 0.8 | 0.8 |
| 0% | 26–51 | 0.8 | 1.4 |
| 0% | 51–600 | 0.8 | 1.8 |
| 0% | > 819 | 0.8 | 2.5 |
| 50% | 51–600 | 1.8–2.0 | 1.8 |
| 50% | > 819 | 1.8–2.0 | 2.5 |
| 80% | 51–600 | 2.0–2.5 | 1.8 |
| 80% | > 819 | 2.0–2.5 | 2.5 |

---

### Execution Flow

#### SIMPL Policy Transition — Multi-Phase Handshake

All policy changes follow a 3-phase protocol ensuring electrical correctness (frequency that increases IccMax is never raised before the compensating domain is clipped):

##### Phase 1: Policy Change Request
- **Root-initiated**: Root iMH observes BW telemetry change → resolves new target policy
- **Leaf-initiated**: Leaf iMH sends SIMPL_RESPONSE with REQUEST_POLICY (no ACK required for request)
- Root combines REQUEST_POLICY with its own computation to resolve final policy

##### Phase 2: GO_INCREASE_GUARDBAND (limit the domain that must yield budget)
- Root sends SIMPL(TARGET_POLICY, GO_INCREASE_GB=1) to all leaves
- **Higher policy** (more IO/Mem): CBBs reduce core/fabric freq ceiling per fused limits → ACK
- **Lower policy** (more core): iMHs reduce IO/Mem fabric freq ceiling per fused limits → ACK
- Each leaf must ACK with SIMPL_RESPONSE(CURRENT_POLICY matching TARGET_POLICY)

##### Phase 3: GO_DECREASE_GUARDBAND (release budget to the requesting domain)
- Root sends SIMPL(TARGET_POLICY, GO_DECREASE_GB=1) to all leaves
- **Higher policy**: iMHs raise IO/Mem fabric freq ceiling → ACK
- **Lower policy**: CBBs raise core/fabric freq ceiling → ACK
- Policy transition complete when all ACKs received

#### Initialization
1. FW reads `fuse:NUM_SIMPL_POLICIES` — determines supported policy count
2. FW reads per-policy fused LUTs: `SIMPL_POLICY_[i]_IMH_CFCIO_MAX_FREQ`, `SIMPL_POLICY_[i]_IMH_CFCMEM_MAX_FREQ`, `SIMPL_POLICY_[i]_CBB_CCP_MAX_FREQ_CDYN_[j]`, `SIMPL_POLICY_[i]_CBB_CFC_MAX_FREQ`
3. CBB Pcode reads `fuse:SIMPL_CBB_DFC_EN` and per-policy DFC offset fuses
4. If DFC enabled: decouple GVFSM at boot (core and ring DVFS independent)
5. TPMI PFM_HEADER initialized per OSXML
6. Default to Policy 0 (core-heavy, IO-light)

#### Runtime
1. iMH root PrimeCode evaluates BW telemetry every ~1–5 ms
2. Resolves new SIMPL policy via BW→freq mapping + leaf REQUEST_POLICY
3. If policy change needed: execute 3-phase handshake
4. CBB Pcode applies new CCP/CFC freq limits from fused LUT
5. CBB Pcode evaluates DFC heuristics within policy limits (core-bound vs. ring-bound)
6. TPMI status registers updated: SIMPL_CURRENT_POLICY, PFM_CBB_STATUS
7. Telemetry counters accumulate: SIMPL_POLICY_[i]_Residency (iMH), CBB_SIMPL_DFC_{CFC,CORE}_LIMIT_RESIDENCY (CBB)

---

### HPM Messages

#### SIMPL (Opcode 0x20 — Root → Leaf)
| Bits | Field | Width | Description |
|------|-------|-------|-------------|
| 7:0 | OPCODE | 8 | 0x20 — SIMPL message |
| 14:8 | AGENT_ID | 7 | Source Agent ID |
| 15 | RESPONSE_REQUIRED | 1 | Always 1 — leaf must ACK |
| 16 | GO_INCREASE_GUARDBAND | 1 | Phase 2: limit frequency to make IccMax headroom |
| 17 | GO_DECREASE_GUARDBAND | 1 | Phase 3: grant frequency to requesting domain |
| 35:32 | TARGET_POLICY | 4 | Target SIMPL policy# (leaf must transition immediately) |

#### SIMPL_RESPONSE (Opcode 0x21 — Leaf → Root)
| Bits | Field | Width | Description |
|------|-------|-------|-------------|
| 7:0 | OPCODE | 8 | 0x21 — SIMPL_RESPONSE message |
| 14:8 | AGENT_ID | 7 | Source Agent ID |
| 15 | RESPONSE_REQUIRED | 1 | Always 0 (ACK or request, not both) |
| 16 | GO_INCREASE_GUARDBAND | 1 | Echoes root's GO_INC_GB in ACK |
| 17 | GO_DECREASE_GUARDBAND | 1 | Echoes root's GO_DEC_GB in ACK |
| 35:32 | CURRENT_POLICY | 4 | Leaf's current active policy# |
| 43:40 | REQUEST_POLICY | 4 | Leaf iMH requests new policy (CBBs always set 0) |

**Protocol rules**:
- At most one of GO_INC_GB or GO_DEC_GB can be set. If both set (invalid), leaf must execute GO_INC_GB (electrically safe)
- Policy# must be within fused range. If violated, leaf snaps to highest policy# (lowest IccMax)
- REQUEST_POLICY from iMH-S can pass a new TARGET_POLICY change (root compares CURRENT_POLICY to detect ACK vs. new request)
- At reset exit: GO_INCREASE_GUARDBAND=0, GO_DECREASE_GUARDBAND=1

---

### Key Registers & Interfaces

#### SIMPL & DFC Fuses

##### iMH Fuses
| Fuse | Bits | Description |
|------|------|-------------|
| `fw_fuses_NUM_SIMPL_POLICIES` | 4 | Number of supported SIMPL policies (PoR=1 for DMR-AP/-SP, up to 4) |
| `PCODE_SIMPL_POLICY_[i]_IMH_CFCIO_MAX_FREQ` | 8 | Max iMH CFC_IO freq limit for policy [i] |
| `PCODE_SIMPL_POLICY_[i]_IMH_CFCMEM_MAX_FREQ` | 8 | Max iMH CFC_Mem freq limit for policy [i] |

##### CBB Fuses (per BASE_CBB0)
| Fuse | Bits | Description |
|------|------|-------------|
| `fw_fuses_NUM_SIMPL_POLICIES` | 4 | Same as iMH — replicated on each die |
| `SIMPL_POLICY_[i]_CBB_CFC_MAX_FREQ` | 8 | Max CBB CFC (ring) freq for policy [i] |
| `SIMPL_POLICY_[i]_CBB_CCP_MAX_FREQ_CDYN_[j]` | 8 | Max CBB core freq for policy [i] × Cdyn level [j] (j ∈ {0..5}) |
| `SIMPL_CBB_DFC_EN` | 1 | Enable DFC; must be 1 if any DFC offset fuse is non-zero |
| `SIMPL_POLICY_[i]_CBB_DFC_EN_MIN_CORES_ACTIVE` | 6 | Active core threshold below which DFC is dynamically disabled |
| `SIMPL_POLICY_[i]_CBB_DFC_OFFSET_BINS_CFC` | 3 | Ring frequency clip (bins) when core-bound |
| `SIMPL_POLICY_[i]_CBB_DFC_OFFSET_BINS_CORE_CDYN_[j]` | 3 | Core frequency clip (bins) when cache/mem-bound, per Cdyn level |

#### TPMI Registers (in UFS Feature Space)

SIMPL/DFC adds 2 registers to the TPMI UFS feature space, plus 1 PFM_HEADER for customer enumeration.

##### Internal Names (Design/Validation)

**SIMPL_DFC_CONTROL** (64-bit, RW)
| Bits | Field | Default | Owner | Description |
|------|-------|---------|-------|-------------|
| 3:0 | SIMPL_MAX_POLICY_OVRD | fuse | Root iMH | Max policy override. Disable SIMPL by setting MAX=MIN |
| 11:8 | SIMPL_MIN_POLICY_OVRD | 0h | Root iMH | Min policy override |
| 17:16 | SIMPL_CBB_DFC_Mode | 2'b00 | CBB Pcode | 00=disabled, 01=CFC clipped, 10=Core clipped, 11=dynamic |

**SIMPL_DFC_STATUS** (64-bit, RO)
| Bits | Field | Default | Owner | Description |
|------|-------|---------|-------|-------------|
| 3:0 | SIMPL_NUM_POLICIES | fuse | All dies | Reflects fused policy count |
| 11:8 | SIMPL_CURRENT_POLICY | 0h | All dies | Current active policy (may differ during transitions) |
| 16 | SIMPL_CBB_DFC_STATUS | fuse | CBB only | Resolved DFC enable (fuse AND mode). iMH reports 0 |

##### Customer Names (PFM — TPMI OSXML/EDS)

**PFM_HEADER** (64-bit, RO)
| Bits | Field | Default | Description |
|------|-------|---------|-------------|
| 7:0 | INTERFACE_VERSION | 0x1 | TPMI version for SW enumeration |

**PFM_CONTROL** (64-bit, RW) — identical to SIMPL_DFC_CONTROL with sanitized field names:
- `PFM_SOC_MAX_POLICY_OVRD`, `PFM_SOC_MIN_POLICY_OVRD`, `PFM_CBB_Mode`

**PFM_STATUS** (64-bit, RO) — identical to SIMPL_DFC_STATUS:
- `PFM_SOC_NUM_POLICIES`, `PFM_SOC_CURRENT_POLICY`, `PFM_CBB_STATUS`

#### Interface Touch Points

| Register/Parameter | MSR | IN_TPMI | OOB_TPMI | CSR | Fuses | MB |
|--------------------|-----|---------|----------|-----|-------|----|
| PFM_CONTROL (SIMPL_DFC_CONTROL) | — | RW | RW | — | defaults | — |
| PFM_STATUS (SIMPL_DFC_STATUS) | — | RO | RO | — | reflects | — |
| PFM_HEADER | — | RO | RO | — | — | — |
| SIMPL Policy LUT | — | — | — | — | per-policy fuses | — |
| DFC Offset LUT | — | — | — | — | per-policy×Cdyn | — |
| SIMPL HPM msg | — | — | — | — | — | HPM |
| SIMPL_RESPONSE HPM msg | — | — | — | — | — | HPM |

#### Performance Observability (Telemetry Counters)
| Counter | Die | Clock | Description |
|---------|-----|-------|-------------|
| `SIMPL_POLICY_[i]_Residency` | iMH | x1clk (100 MHz) | Cycles in each SIMPL policy (one per supported policy) |
| `CBB_SIMPL_DFC_CFC_LIMIT_RESIDENCY` | CBB | x1clk (100 MHz) | Cycles with DFC enabled AND ring clipped by DFC offset |
| `CBB_SIMPL_DFC_CORE_LIMIT_RESIDENCY` | CBB | x1clk (100 MHz) | Cycles with DFC enabled AND core clipped by DFC offset |

#### PLR — Perf Limit Reasons Observability

PLR is the debug interface through which SIMPL/DFC frequency clipping is observable to SW. PLR is **CBB-only** — iMH does not support PLR (PrimeCode writes "1" to PLR_HEADER to disable it on iMH dies). DMR drops all MSR and PECI-PCS PLR interfaces.

##### PLR Interface Matrix

| Register/Parameter | MSR | IN_TPMI | OOB_TPMI | CSR | Fuses | MB |
|--------------------|-----|---------|----------|-----|-------|----|
| PLR_HEADER | Drop | RO | RO | — | — | — |
| PLR_DIE_LEVEL (coarse) | Drop | RW0C | RW0C | — | — | — |
| PLR_MAILBOX_INTERFACE | Drop | RW | RW | — | — | — |
| PLR_MAILBOX_DATA (coarse+fine) | Drop | RW0C | RW0C | — | — | — |
| RAPL_PERF_LIMIT HPM (iMH→CBB) | — | — | — | — | — | HPM |
| LEAF_PERF_STATUS HPM (CBB→iMH) | — | — | — | — | — | HPM |

**Dropped MSRs** (not supported since GNR): MSR_IA_PERF_LIMIT_REASONS, MSR_IA_PERF_LIMIT_REASONS2, MSR_CLM_PERF_LIMIT_REASONS

##### PLR_DIE_LEVEL — Coarse Grain (64-bit, RW0C, die-scoped)
| Bit | Field | Description |
|-----|-------|-------------|
| 0 | FREQUENCY | Limited by Cdyn level or FCT |
| 1 | CURRENT | Limited by Pmax or IccMax (RACL) |
| 2 | POWER | Limited by Socket/Platform RAPL or SST-CP |
| 3 | THERMAL | Limited by in-die thermal conditions |
| 4 | PLATFORM | Limited by XXProchot and/or VRHOT |
| 5 | MCP | External die-based feedback (D-line arch) |
| 6 | RAS | Limited by RAS limit |
| 7 | MISC | Freq limit from OOB SW (e.g., BMC) — aggregates all OOB clipping |
| 8 | QOS | Limited by QoS constraints (Reserved) |
| 9 | **ICCMAX** | **Limited by DFC/SIMPL** |

**Semantics**: Log bits (not status). Pcode sets, SW clears by writing 0 (RW0C). Pcode re-sets as long as clipping persists. TPMI response latency ~1 ms.

##### PLR_MAILBOX_DATA — Fine Grain (64-bit, RW0C, per module/domain)

Accessed via PLR_MAILBOX_INTERFACE (Domain: 0=core, 1=ring; ID=module#; Command: 0=read, 1=write).

**Bits [31:0] — Coarse Grain** (same as PLR_DIE_LEVEL bits [9:0])

**Bits [63:32] — Fine Grain**
| Bit | Field | Description |
|-----|-------|-------------|
| 32 | CDYN0 | TRL level 0 freq limiting |
| 33 | CDYN1 | TRL level 1 freq limiting |
| 34 | CDYN2 | TRL level 2 freq limiting |
| 35 | CDYN3 | TRL level 3 freq limiting |
| 36 | CDYN4 | TRL level 4 freq limiting |
| 37 | CDYN5 | TRL level 5 freq limiting |
| 38 | FCT | Limited by FCT |
| 39 | PCS_TRL | OOB TRL override (ODC_TURBO_MAX_RATIO) limiting core freq |
| 40 | MTPMAX | Power exceeds Pmax.app limit |
| 41 | FAST_RAPL | Limited by Fast RAPL firing |
| 42 | PKG_PL1_INBAND | Package RAPL PL1 from OS/SW |
| 43 | PKG_PL1_CSR | Package RAPL PL1 from BIOS |
| 44 | PKG_PL1_OOB | Package RAPL PL1 from OOB SW |
| 45 | PKG_PL2_INBAND | Package RAPL PL2 from OS/SW |
| 46 | PKG_PL2_CSR | Package RAPL PL2 from BIOS |
| 47 | PKG_PL2_OOB | Package RAPL PL2 from OOB SW |
| 48 | PLATFORM_PL1_INBAND | Platform RAPL PL1 from OS/SW |
| 49 | PLATFORM_PL1_CSR | Platform RAPL PL1 from BIOS |
| 50 | PLATFORM_PL1_OOB | Platform RAPL PL1 from OOB SW |
| 51 | PLATFORM_PL2_INBAND | Platform RAPL PL2 from OS/SW |
| 52 | PLATFORM_PL2_CSR | Platform RAPL PL2 from BIOS |
| 53 | PLATFORM_PL2_OOB | Platform RAPL PL2 from OOB SW |
| 54 | RACL | Limited by RACL condition |
| 55 | PER_CORE_THERMAL | Core temp exceeds threshold |
| 56 | ICCMAX_MODULE_LEVEL | **DFC/SIMPL clipping at module level** |
| 57 | XXPROCHOT | Platform prochot pin triggered |
| 58 | HOT_VR | Platform VR_HOT pin triggered |
| 61 | PCS_PSTATE_NOT_SUPPORTED | Not supported (DMR drops PCS_PSTATE per GNR errata) |
| 62 | RAS_MODULE_LEVEL | RAS limit at module level |

##### HPM Handshake for PLR

**RAPL_PERF_LIMIT** (iMH → CBB, opcode 0x16): iMH PrimeCode distinguishes in-band vs. OOB vs. CSR source of RAPL limits and sends per-source PLR bits to CBBs via this HPM message. CBB Pcode copies these bits into PLR_MAILBOX_DATA when responding to SW reads.

**LEAF_PERF_STATUS** (CBB → iMH, opcode 0x16): CBB Pcode periodically reports running counters of modules clipped by each limit category:

| Bits | Field | Description |
|------|-------|-------------|
| 31:16 | RACL_PERF_STATUS | Count of modules limited by RACL |
| 47:32 | SOCKET_RAPL_PERF_STATUS | Count of modules limited by Socket RAPL (PL1/PL2 in-band/CSR/OOB + Fast RAPL) |
| 63:48 | PLATFORM_RAPL_PERF_STATUS | Count of modules limited by Platform RAPL (PL1/PL2 in-band/CSR/OOB) |

---

### Cross Products

| Event | SIMPL Behavior |
|-------|---------------|
| **Pmax (hard throttle)** | Pmax takes precedence. No SIMPL policy change executed. Resume SIMPL after recovery |
| **Prochot** | Prochot takes precedence. No SIMPL policy change. Resume after recovery |
| **VRHot** | VRHot takes precedence. No SIMPL policy change. Resume after recovery |
| **RAPL** | RAPL takes precedence. No SIMPL policy change. Resume after recovery |
| **RACL** | RACL takes precedence. No SIMPL policy change. Resume after recovery |
| **ADR** | Must obey current SIMPL policy's max freq (Iccmax safety). iMH selects min(SIMPL_policy_max, BIOS_programmed_value). No full SIMPL handshake during ADR (latency < 1 ms). For fADR: same constraint |
| **Seamless Patch Load** | µCode quiesces cores → likely triggers Policy 0. SIMPL change latency (~1 ms) should be outside critical WrMSR 0x79 path |
| **iMH UFS** | SIMPL provides ceiling input into UFS flow. Final fabric freq = min(activity-based, SIMPL limit, RAPL/RACL limit) |

---

### Source References

#### Primecode (iMH-level firmware)
| # | File | Description |
|---|------|-------------|
| 1 | `src/flow/simpl/simpl_algo/v1_0/simpl.hpp` | Core SIMPL algorithm — policy selection and limit computation |
| 2 | `src/flow/simpl/simpl_algo/v1_0/simpl.cpp` | SIMPL algorithm implementation |
| 3 | `src/flow/simpl/simpl_algo/v1_0/fuses_simpl.xml` | SIMPL fuse definitions |
| 4 | `src/flow/simpl/simpl_hpm/v1_0/simpl_hpm.hpp` | SIMPL HPM message handler (opcodes 0x20/0x21) |
| 5 | `src/flow/simpl/simpl_hpm/v1_0/simpl_hpm.cpp` | HPM implementation with persistent patch support |
| 6 | `src/flow/simpl/simpl_root_state/v1_0/simpl_root_state.hpp` | Root state machine (iMH as root orchestrator) |
| 7 | `src/flow/simpl/simpl_root_state/v1_0/simpl_root_state.cpp` | Root state controller — drives policy transitions |
| 8 | `src/flow/simpl/simpl_leaf_state/v1_0/simpl_leaf_state.hpp` | Leaf state machine (iMH as leaf) |
| 9 | `src/flow/simpl/simpl_leaf_state/v1_0/simpl_leaf_state.cpp` | Leaf state — processes incoming SIMPL policy, sends SIMPL_RESPONSE |
| 10 | `src/flow/simpl/simpl_tpmi/v1_0/simpl_tpmi.hpp` | SIMPL TPMI register interface for OS observability |
| 11 | `src/flow/simpl/simpl_tpmi/v1_0/simpl_tpmi.cpp` | SIMPL TPMI implementation |
| 12 | `src/flow/ufs/ufs_algos/v2_0/ufs_flow.hpp` | UFS flow — resolves fabric freq from RAPL/SIMPL/heuristics |
| 13 | `src/flow/ufs/ufs_algos/v2_0/ufs_heuristics.cpp` | UFS demand-based heuristic frequency estimation |
| 14 | `src/ip/mdfc/v1_0/mdfc.hpp` | MDFC (Mesh Dynamic Frequency Control) IP driver |

#### Pcode (CBB die-level firmware)
| # | File | Description |
|---|------|-------------|
| 1 | `source/pcode/flows/slow_limits/simpl/simpl.h` | CBB SIMPL class — receives policy from iMH, computes CCP/ring freq limits |
| 2 | `source/pcode/flows/slow_limits/simpl/simpl.cpp` | CBB SIMPL implementation — reads fused SIMPL_POLICY LUT |
| 3 | `source/pcode/flows/slow_limits/dfc/dfc.h` | CBB DFC header — `set_dfc_limit(simpl_policy)` with offset bins |
| 4 | `source/pcode/flows/slow_limits/dfc/dfc.cpp` | CBB DFC implementation — reads DFC_EN, per-policy offset fuses |
| 5 | `source/pcode/flows/slow_limits/dfc/dfc_telemetry.h` | DFC telemetry — CFC/Core limit residency counters |
| 6 | `source/pcode/flows/slow_limits/slow_limits/slow_limits.h` | Slow limits resolver — merges RAPL, VR, EMTTM, SIMPL, DFC |
| 7 | `source/pcode/hpm/hpm_api.h` | HPM API — HPM_MSG_SIMPL_t message type |

---

### Collateral Links

| Type | Link | Notes |
|------|------|-------|
| SIMPL HAS | [DMR SIMPL HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_SIMPL.html) | Primary spec — policies, HPM messages, fuses, TPMI, cross products |
| DFC HAS (GNR) | [HPM UFS — DFC](https://docs.intel.com/documents/pm_doc/src/server/GNR/Features/Hierarchical%20UFS/HPM_UFS.html#proactive-iccmax-management-dynamic-frequency-constraint) | Original DFC specification in GNR UFS HAS |
| TPMI HAS | [TPMI HAS](https://docs.intel.com/documents/pm_doc/src/server/arch_common/TPMI/TPMI.html) | PFM feature enumeration, SW flow, interface_version |
| Fabric DVFS Data | [DMR_Fabric_DVFS.xlsx](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/assets/DMR_Fabric_DVFS.xlsx) | Policy definitions, BW→freq tables, fuse values (source of truth) |
| PLR HAS | [DMR PLR HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_PLR.html) | Perf Limit Reasons — PLR_DIE_LEVEL, PLR_MAILBOX, ICCMAX bit for DFC/SIMPL, HPM handshake |
| PLR Data | [DMR_Perf_Limit_Reasons.xlsx](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/assets/DMR_Perf_Limit_Reasons.xlsx) | PLR bit definitions, coarse/fine grain tables (source of truth) |
| GNR PLR HAS | [GNR PLR HAS](https://docs.intel.com/documents/pm_doc/src/server/GNR/Features/perf_limit_reasons/perf_limit_reasons_has.html) | Baseline PLR spec (DMR inherits from GNR) |
| Socket RAPL KB | [socket_rapl.md](socket_rapl.md) | RAPL takes precedence over SIMPL; SIMPL limits iMH fabric via UFS |
| PEM KB | [pem.md](pem.md) | PEM observes SIMPL-induced frequency clipping as a Perf Limit Reason |

---

---

### Related Sightings
<!-- No NWP SIMPL sightings cataloged yet -->

---

### NWP Delta

NWP inherits DMR SIMPL architecture. Key NWP-specific areas to validate:
- **Policy count**: Verify `fuse:NUM_SIMPL_POLICIES` — DMR-AP/-SP PoR is 1 policy, NWP may differ
- **Fuse values**: NWP binsplit team must provide NWP-specific per-policy freq limits and DFC offsets
- **Die topology**: NWP hub-and-spoke topology (iMH root, CBB leaves) — verify SIMPL HPM message routing
- **BW telemetry thresholds**: NWP IO/Mem BW→freq mapping may differ from DMR (different fabric and memory configs)
- **TPMI PFM registers**: Verify PFM_HEADER INTERFACE_VERSION, PFM_CONTROL/STATUS accessible per OSXML
- **Primecode version**: NWP uses `src/flow/simpl/*/v1_0/` — verify SIMPL algo, root/leaf state, HPM, TPMI
- **DFC dynamic disable**: Verify `DFC_EN_MIN_CORES_ACTIVE` threshold correct for NWP core count per CBB
- **Cross products**: Validate SIMPL pause during Pmax/Prochot/VRHot/RAPL/RACL and ADR SIMPL-constrained freq

---

### Validation Starting Points

1. **Read TPMI status**: Read PFM_STATUS via TPMI — verify SIMPL_NUM_POLICIES and SIMPL_CURRENT_POLICY (expect Policy 0 at idle)
2. **Fuse check**: Dump all SIMPL/DFC fuses via PythonSV — verify LUT entries match binsplit expectations
3. **PFM_CONTROL override**: Set PFM_SOC_MAX_POLICY_OVRD = PFM_SOC_MIN_POLICY_OVRD to lock SIMPL to a specific policy, verify freq limits enforced
4. **DFC test**: Run core-heavy workload → verify ring clipped (CBB_SIMPL_DFC_CFC_LIMIT_RESIDENCY > 0). Run cache-heavy → verify core clipped (CBB_SIMPL_DFC_CORE_LIMIT_RESIDENCY > 0)
5. **Policy transition**: Generate IO-heavy traffic → verify SIMPL transitions to higher policy# (lower core freq, higher IO fabric freq)
6. **Asymmetric workload**: IO traffic on secondary iMH only → verify iMH-S sends REQUEST_POLICY, root resolves correctly
7. **Cross-reset**: Verify SIMPL policy persists or re-initializes correctly across warm and cold resets
8. **Telemetry counters**: Read SIMPL_POLICY_[i]_Residency — verify non-zero for active policy, zero for inactive
