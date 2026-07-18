# TCD: Socket RAPL - Boot / Reset Boundary Conditions

| Field | Value |
|-------|-------|
| **TCD ID** | [16031169466](https://hsdes.intel.com/appstore/article-one/#/16031169466) |
| **Title** | Socket RAPL - Boot / Reset Boundary Conditions |
| **Status** | open |
| **Owner** | bg3 |
| **Parent TPF** | [15019477653 -- NWP PM Socket RAPL](https://hsdes.intel.com/appstore/article-one/#/15019477653) |
| **KB last updated** | 2026-07-18 |
| **Feature** | Power / RAPL -- Socket RAPL boot-state invariants and reset boundary behavior |
| **Created from** | Co-Design T2 audit -- boot/reset boundary split from TCD 22022420821 |

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
| [22022421931 -- [BEAT][FV PM][AR] Validate RAPL=0 during OS Boot](https://hsdes.intel.com/appstore/article-one/#/22022421931) | Cold boot counter init | ENERGY_STATUS = 0, PERF_STATUS = 0 at OS boot |

### Coverage Gaps (from Co-Design T1 audit)

| Gap | Recommended TC | Priority |
|-----|---------------|----------|
| ENERGY_STATUS warm reset persistence | *(TC TBD)* -- verify ENERGY_STATUS NOT reset on warm reset | M |
| PERF_STATUS warm reset retention/clear | *(TC TBD)* -- verify PERF_STATUS behavior across warm reset | M |
| LOCK bit clear on cold reset | *(TC TBD)* -- verify LOCK=0 after cold reset; BIOS re-sets during boot | M |
| PL1/PL2 defaults after cold reset | *(TC TBD)* -- verify PL1=TDP, PL2=1.2xTDP after cold reset | L |
| Stale RAPL_PERF_LIMIT after warm reset | *(TC TBD)* -- verify fresh HPM 0x14 sent after PH6; no stale limit | M |

---

## Section 2: Interfaces and Protocols

| Interface | Register / Path | Description |
|-----------|----------------|-------------|
| TPMI ENERGY_STATUS | sv.socket0.nio.punit.tpmi.socket_rapl.energy_status | Must be 0 at cold boot; persists across warm reset |
| TPMI PERF_STATUS | sv.socket0.nio.punit.tpmi.socket_rapl.perf_status | Must be 0 at cold boot; warm reset behavior validated |
| TPMI PL1_CONTROL.LOCK | sv.socket0.nio.punit.tpmi.socket_rapl.pl1_control | LOCK cleared on cold reset |

---

## Section 3: Reset, Power, and Clocking

- ENERGY_STATUS: resets on cold reset; NOT reset on warm reset (monotonic)
- PERF_STATUS: resets on cold reset; warm reset retention TBD (validate)
- PL1/PL2_CONTROL: BIOS re-programs at CPL3 after any reset; LOCK cleared on cold reset
- PL_INFO: re-populated from fuses at PH6 after any reset
- HPM RAPL_PERF_LIMIT: fresh message sent after PH6; no stale limit from previous boot

---

## Section 4: Programming Model

### Cold Boot Validation
1. Cold boot platform
2. At OS handoff (post-CPL3), read TPMI ENERGY_STATUS
3. Verify ENERGY [31:0] = 0
4. Read TPMI PERF_STATUS
5. Verify PWR_LIMIT_THROTTLE_CTR = 0

### Warm Reset Persistence
1. Run workload to accumulate ENERGY_STATUS > 0
2. Trigger warm reset
3. After PH6 + CPL3, read ENERGY_STATUS
4. Verify ENERGY > 0 (counter persisted across warm reset)

---

## Section 5: Operational Behavior

> **WHAT:** Socket RAPL boot-state invariants and reset boundary conditions are correct.

**Pass/fail bar:**
- At cold boot OS handoff: ENERGY_STATUS = 0, PERF_STATUS = 0
- After warm reset: ENERGY_STATUS persists (NOT reset); PERF_STATUS behavior per spec
- LOCK bit cleared after cold reset; re-set by BIOS if configured
- No stale RAPL_PERF_LIMIT persists after any reset

---

## Section 6: Corner Cases & Error Handling

| Scenario | Expected Behavior |
|----------|------------------|
| Cold boot after power loss | ENERGY_STATUS = 0; PERF_STATUS = 0; LOCK = 0 |
| Warm reset during active RAPL throttle | Throttle removed; counters per spec; fresh PID init at PH6 |
| Rapid warm reset succession | Each reset produces clean PH6 init; no accumulated stale state |
| LOCK = 1 before warm reset | LOCK persists across warm reset (BIOS re-sets at CPL3) |

---

## Section 7: Security / Safety / Policy

- Boot-state invariants ensure clean RAPL state for OS; no stale power policy from previous boot
- LOCK clear on cold reset ensures BIOS can re-establish platform policy

---

## Section 8: References

- [Socket RAPL KB](../../pm_features/power_rapl/socket_rapl.md) -- reset semantics, counter behavior
- [TCD 22022420821 -- Registers CSR/TPMI](https://hsdes.intel.com/appstore/article-one/#/22022420821) -- steady-state register interface (sibling)
- [TCD 22022420806 -- Cross-products](https://hsdes.intel.com/appstore/article-one/#/22022420806) -- RAPL x Reset TC (cross-product scope)
- Co-Design audits 2026-07-18 -- boot/reset boundary split
