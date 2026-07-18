# TCD: Socket RAPL - Boot / Reset Boundary Conditions

| Field | Value |
|-------|-------|
| **TCD ID** | [16031169466](https://hsdes.intel.com/appstore/article-one/#/16031169466) |
| **Title** | Socket RAPL - Boot / Reset Boundary Conditions |
| **Status** | open |
| **Owner** | bg3 |
| **Parent TPF** | [15019477653 -- NWP PM Socket RAPL](https://hsdes.intel.com/appstore/article-one/#/15019477653) |
| **KB last updated** | 2026-07-18 |
| **KB revision** | 2 |
| **Feature** | Power / RAPL -- Socket RAPL boot-state invariants and reset boundary behavior |
| **Created from** | Co-Design T2 audit -- boot/reset boundary split from TCD 22022420821 |
| **REV 2 changes** | Spec-confirmed cold/warm reset behavior for all registers; fixed §4 content routing (removed test steps); §6 upgraded to 4-column coverage verdict; NWP NIO register paths confirmed |

## Section 1: Architecture / Micro-architecture and Functionality

This TCD verifies **Socket RAPL boot-state invariants and reset boundary conditions** on NWP. These are specific initialization and reset behaviors that define the expected state of RAPL registers and counters at well-defined system boundaries (cold boot, warm reset, lock clear). They are distinct from steady-state register interface correctness (TCD 22022420821) and from runtime algorithm behavior (TCD 22022420798).

> **Architecture overview:** See [TPF 15019477653](https://hsdes.intel.com/appstore/article-one/#/15019477653) Section 2 Design Details for boot flow.

### Functional Scope

- **Counter initialization at cold boot**: ENERGY_STATUS = 0, PERF_STATUS = 0 at OS handoff
- **ENERGY_STATUS warm reset persistence**: counter NOT reset on warm reset (monotonic across warm resets)
- **PERF_STATUS warm reset behavior**: counter reset/retention semantics
- **LOCK bit reset behavior**: LOCK cleared on cold reset; re-set by BIOS during next boot
- **Stale limit recovery after reset**: no residual RAPL_PERF_LIMIT persists after reset

### TC Coverage Map

| TC | Scope | Key Validation |
|----|-------|----------------|
| [22022421931 -- [BEAT][FV PM][AR] Validate RAPL PL1=0 during OS Boot](https://hsdes.intel.com/appstore/article-one/#/22022421931) | Cold boot counter init | ENERGY_STATUS = 0, PERF_STATUS = 0 at OS boot |
| [16031169546 -- [FV PM] Socket RAPL PL1 Toggle 0W to TDP Under Load](https://hsdes.intel.com/appstore/article-one/#/16031169546) | PL1 boundary toggle under load | PL1=0W clips to MIN_PL; PL1=TDP restores correct limit; multi-cycle stability |

### Coverage Gaps (from Co-Design T1 audit + REV 2 spec confirmation)

| Gap | Recommended TC | Priority | Spec Status |
|-----|---------------|----------|-------------|
| ENERGY_STATUS warm reset persistence | *(TC TBD)* -- verify ENERGY_STATUS NOT reset on warm reset | M | ✅ Confirmed: sticky, persists |
| PERF_STATUS warm reset persistence | *(TC TBD)* -- verify PERF_STATUS NOT reset on warm reset | M | ✅ Confirmed: sticky, persists |
| LOCK bit clear on cold reset | *(TC TBD)* -- verify LOCK=0 after cold reset; BIOS re-sets during boot | M | ✅ Confirmed: cleared on powergood_rst_b |
| LOCK bit persistence on warm reset | *(TC TBD)* -- verify LOCK persists across warm reset | M | ✅ Confirmed: sticky |
| PL1/PL2 defaults after cold reset | *(TC TBD)* -- verify PL1=TDP, PL2=1.2xTDP after cold reset | L | ✅ Confirmed: defaults from SST_PP_INFO TDP |
| PL_INFO repopulation after cold reset | *(TC TBD)* -- verify PL_INFO matches fuse TDP | L | ✅ Confirmed: repopulated at PH6 |
| Stale RAPL_PERF_LIMIT after reset | *(TC TBD)* -- verify fresh HPM 0x14 sent after PH6; no stale limit | M | ✅ Confirmed: FW validity check before use |
| Warm reset during active RAPL throttle | *(TC TBD)* -- verify PID re-init + counter persistence under active throttle | M | Inferred from sticky semantics |

---

## Section 2: Interfaces and Protocols

| Interface | Register / Path | Cold Reset | Warm Reset | Description |
|-----------|----------------|------------|------------|-------------|
| TPMI ENERGY_STATUS | `sv.socket0.nio.punit.tpmi.socket_rapl.energy_status` | Reset to 0 | **Persists** (sticky) | Monotonic energy counter; must be 0 at OS handoff after cold boot |
| TPMI PERF_STATUS | `sv.socket0.nio.punit.tpmi.socket_rapl.perf_status` | Reset to 0 | **Persists** (sticky) | Throttle time counter; must be 0 at OS handoff after cold boot |
| TPMI PL1_CONTROL | `sv.socket0.nio.punit.tpmi.socket_rapl.pl1_control` | LOCK=0 (unlocked); PWR_LIM=TDP | **Persists** (sticky) | LOCK bit cleared on cold reset; BIOS re-programs and re-locks during next boot |
| TPMI PL2_CONTROL | `sv.socket0.nio.punit.tpmi.socket_rapl.pl2_control` | LOCK=0 (unlocked); PWR_LIM=1.2×TDP | **Persists** (sticky) | LOCK bit cleared on cold reset; BIOS re-programs and re-locks during next boot |
| TPMI PL_INFO | `sv.socket0.nio.punit.tpmi.socket_rapl.pl_info` | Repopulated from fuses | **Persists** (sticky, RO) | MAX_PL1=TDP, MAX_PL2=1.2×TDP; read-only, populated by FW at PH6 |
| TPMI POWER_UNIT | `sv.socket0.nio.punit.tpmi.socket_rapl.power_unit` | Repopulated | **Persists** (sticky, RO) | Power/energy/time unit encodings |
| HPM RAPL_PERF_LIMIT | HPM msg 0x14 (NIO→CBB) | Invalid/stale; FW checks validity before use | Persists if valid | Fresh HPM sent after PH6 init; stale data detected by FW validity check |

---

## Section 3: Reset, Power, and Clocking

All Socket RAPL TPMI registers are **sticky** (survive warm reset, cleared on cold reset via `powergood_rst_b`). The operational boot-state invariants are:

| Register | Cold Reset (powergood) | Warm Reset (prim_rst_b) | Boot Reprogramming |
|----------|----------------------|-------------------------|-------------------|
| ENERGY_STATUS | 0 | Persists | None — counter starts accumulating at PH6 |
| PERF_STATUS | 0 | Persists | None — counter increments when RAPL throttles |
| PL1_CONTROL (incl. LOCK) | PWR_LIM=TDP, LOCK=0 | Persists (incl. LOCK) | BIOS re-programs PL1 + re-sets LOCK at CPL3 |
| PL2_CONTROL (incl. LOCK) | PWR_LIM=1.2×TDP, LOCK=0 | Persists (incl. LOCK) | BIOS re-programs PL2 + re-sets LOCK at CPL3 |
| PL_INFO | Repopulated from fuses | Persists | FW populates at PH6 (MAX_PL1=TDP, MAX_PL2=1.2×TDP) |
| RAPL_PERF_LIMIT (HPM) | Stale/invalid | Persists if valid | PrimeCode sends fresh HPM 0x14 after PH6 RAPL PID init |

**Key distinction**: Cold reset asserts `powergood_rst_b`, clearing ALL registers to defaults. Warm reset asserts only `prim_rst_b`, which clears non-sticky registers — all Socket RAPL TPMI registers are sticky and therefore survive warm reset.

---

## Section 4: Programming Model

### Cold Boot Register State Contract

After cold reset, BIOS and PrimeCode re-establish the Socket RAPL programming model in a defined sequence:

- **PH6 (PrimeCode Runtime Init)**: PrimeCode reads fuse-derived TDP and populates `PL_INFO` (MAX_PL1=TDP, MAX_PL2=1.2×TDP). RAPL NN-PID controllers are initialized with default gains. The first `RAPL_PERF_LIMIT` HPM (msg 0x14) is sent to all CBBs with valid frequency limits.
- **CPL3 (BIOS Handoff)**: BIOS programs `PL1_CONTROL.PWR_LIM` = TDP and `PL2_CONTROL.PWR_LIM` = 1.2×TDP (or OEM overrides). BIOS sets `PL1_CONTROL.LOCK` = 1 and `PL2_CONTROL.LOCK` = 1 to prevent OS modification of power limits.
- **OS Handoff**: At this point, ENERGY_STATUS = 0 (no energy accumulated yet), PERF_STATUS = 0 (no throttling has occurred), PL1/PL2 are locked with correct limits, and PL_INFO reflects fuse-derived maximums.

### Warm Reset Register State Contract

On warm reset, all Socket RAPL TPMI registers retain their pre-reset values because they are sticky. BIOS does **not** re-program PL1/PL2 on warm reset (they persist with LOCK still set). PrimeCode re-initializes its PID controllers at PH6 and sends a fresh `RAPL_PERF_LIMIT` HPM, but the TPMI register state is inherited from before the reset. ENERGY_STATUS continues accumulating monotonically.

### NWP Topology Consideration

NWP uses a **single NIO die** (vs dual IMH on DMR). All RAPL PID controllers run on the NIO, and HPM RAPL_PERF_LIMIT messages are sent from NIO directly to all 4 CBBs. There is no IMH-S leaf RACL PID aggregation step. Register paths use `sv.socket0.nio.punit.tpmi.socket_rapl.*` instead of `sv.socket0.imh0.punit.tpmi.socket_rapl.*`.

---

## Section 5: Operational Behavior

> **WHAT:** Socket RAPL boot-state invariants and reset boundary conditions are correct across cold boot, warm reset, and lock clear scenarios.

### Scenario × Expected Outcome

| # | Scenario | Expected Outcome | Measurable Bar | TC Link |
|---|----------|-----------------|----------------|---------|
| 1 | Cold boot — counter init | ENERGY_STATUS = 0 and PERF_STATUS = 0 at OS handoff (post-CPL3) | `ENERGY_STATUS.ENERGY[31:0] == 0` AND `PERF_STATUS.PWR_LIMIT_THROTTLE_CTR[31:0] == 0` | [22022421931](https://hsdes.intel.com/appstore/article-one/#/22022421931) |
| 2 | Warm reset — ENERGY_STATUS persistence | ENERGY_STATUS > 0 after warm reset (counter NOT cleared) | `ENERGY_STATUS.ENERGY[31:0] > pre_reset_energy_value` | *(TC TBD)* |
| 3 | Warm reset — PERF_STATUS persistence | PERF_STATUS retains pre-reset value (sticky) | `PERF_STATUS.PWR_LIMIT_THROTTLE_CTR[31:0] >= pre_reset_throttle_ctr` | *(TC TBD)* |
| 4 | Cold reset — LOCK bit cleared | PL1_CONTROL.LOCK = 0 and PL2_CONTROL.LOCK = 0 after cold reset, before BIOS CPL3 | `PL1_CONTROL.LOCK == 0` AND `PL2_CONTROL.LOCK == 0` (sampled before BIOS lock) | *(TC TBD)* |
| 5 | Warm reset — LOCK bit persists | PL1_CONTROL.LOCK and PL2_CONTROL.LOCK retain pre-reset value | `PL1_CONTROL.LOCK == pre_reset_lock_value` | *(TC TBD)* |
| 6 | Cold reset — PL1/PL2 defaults | PL1=TDP and PL2=1.2×TDP after cold reset at OS handoff | `PL1_CONTROL.PWR_LIM == PL_INFO.MAX_PL1` AND `PL2_CONTROL.PWR_LIM == PL_INFO.MAX_PL2` | [16031169546](https://hsdes.intel.com/appstore/article-one/#/16031169546) (partial — validates PL1=TDP restore) |
| 7 | Cold reset — PL_INFO repopulation | PL_INFO matches fuse-derived TDP values after cold reset | `PL_INFO.MAX_PL1 == fuse_TDP` AND `PL_INFO.MAX_PL2 == 1.2 × fuse_TDP` | *(TC TBD)* |
| 8 | Reset — fresh RAPL_PERF_LIMIT HPM | PrimeCode sends valid HPM 0x14 after PH6; no stale limit from previous boot | No RAPL throttling observed before workload starts post-reset | *(TC TBD)* |

---

## Section 6: Corner Cases & Error Handling

| Corner Case | Description | Current Coverage | Action Required |
|-------------|-------------|-----------------|----------------|
| **Cold boot after power loss** | Full power cycle — all registers must be at cold-reset defaults: ENERGY=0, PERF=0, LOCK=0 | ✅ Covered by TC 22022421931 (cold boot counter init) | No action |
| **Warm reset during active RAPL throttle** | RAPL PID is actively throttling when warm reset occurs — throttle must be removed; PID re-initialized at PH6; PERF_STATUS retains accumulated count | ❌ Not covered — no TC exercises warm reset under active throttle | New TC needed: run workload above PL1, trigger warm reset, verify PID re-init + counter persistence |
| **Rapid warm reset succession** | Multiple warm resets within seconds — each must produce clean PH6 init without accumulated stale state in HPM or PID weights | ❌ Not covered — no TC tests sequential warm resets | New TC needed: 3× warm reset in <30s, verify PH6 init clean each time |
| **LOCK = 1 before warm reset** | BIOS has locked PL1/PL2; LOCK must persist across warm reset (sticky bit) | ❌ Not covered — no TC verifies LOCK persistence across warm reset | New TC needed: verify LOCK=1 before and after warm reset |
| **PL_INFO mismatch after cold reset** | PL_INFO should match fuse-derived TDP; mismatch indicates FW init failure | ⚠️ Verification criterion only — should be a precondition check in cold boot TCs | Add PL_INFO == fuse TDP assertion to TC 22022421931 precondition |
| **ENERGY_STATUS rollover** | 32-bit energy counter wraps to 0 after 0xFFFFFFFF — must not be confused with cold reset clearing | ⚠️ Verification criterion only — add rollover awareness to warm reset persistence TC | Note in warm reset TC: if ENERGY post-reset < pre-reset, verify rollover (not reset) |
| **OEM PL1/PL2 override vs defaults** | BIOS may program non-default PL1/PL2; cold reset must still restore to TDP/1.2×TDP before BIOS reprograms | ⚠️ Verification criterion only — sample PL1/PL2 after powergood_rst_b before BIOS CPL3 | Add pre-BIOS register read step to LOCK clear TC |

---

## Section 7: Security / Safety / Policy

- Boot-state invariants ensure clean RAPL state for OS; no stale power policy from previous boot
- LOCK clear on cold reset ensures BIOS can re-establish platform policy

---

## Section 8: References

- [Socket RAPL KB](../../pm_features/power_rapl/socket_rapl.md) -- reset semantics, counter behavior, NN-PID architecture
- [Wave3 Socket RAPL HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Socket_RAPL/Socket_RAPL.html) -- register definitions, reset behavior
- [NWP iMH SoC PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) -- NWP-specific RAPL scope
- [TCD 22022420821 -- Registers CSR/TPMI](https://hsdes.intel.com/appstore/article-one/#/22022420821) -- steady-state register interface (sibling)
- [TCD 22022420806 -- Cross-products](https://hsdes.intel.com/appstore/article-one/#/22022420806) -- RAPL x Reset TC (cross-product scope)
- Co-Design spec query (2026-07-18) -- NWP register cold/warm reset behavior confirmed via `codesign-ask-specs-and-wikis` (NWP project)
- Co-Design audits 2026-07-18 -- boot/reset boundary split
