# Deep Analysis: CStates C6A Demotion Policy Check

| Field | Value |
|-------|-------|
| **HSD ID** | 14023715625 |
| **Title** | CStates: C6A Demotion policy check |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Core C-States |
| **Sub-Feature** | C6A demotion policy — conditions under which C6A is demoted |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies **C6A demotion policy** — conditions that trigger demotion of C6A requests. Tags: `NGA_MAIN`, `plc.feature.p1`.

**Note**: Test step content appears to be the default HSD template (unreleased/incomplete). The section headers are present but specific steps have not been authored. The test should be considered a **placeholder** for C6A demotion policy validation.

---

## Section B: NWP-Specific Test Procedure

### C6A Demotion Policy (Inferred)

C6A demotion can occur when:
1. Uncore is not ready to support C6 (fabric busy)
2. Module-level conditions prevent C6 (other core in module active)
3. Explicit demotion via MSR 0xE2 bits 25/26

### Adapted Steps (Inferred from context)

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Run cstates PMx | `python runPmx.py -x nwp.xml -p cstates -H 1 -M 5` |
| 2 | Create conditions that trigger C6A demotion | Uncore busy; set demotion bits |
| 3 | Verify C6A request demoted to C1/C3 | core_cstate = C1 instead of C6 |
| 4 | Verify demotion policy follows MSR 0xE2 settings | Bits 25-28 control demotion |
| 5 | Verify no demotion when conditions not met | C6A proceeds when uncore ready |

### Pass Criteria (Inferred)
- C6A demoted to correct target (C3 or C1) under appropriate conditions
- No demotion when conditions are not met
- MSR 0xE2 demotion enable bits are respected

---

## Section F: Recommendation

**Recommendation: ADOPT — Test content incomplete in HSD; infer C6A demotion policy from MSR 0xE2 behavior; C6A functional on NWP**

Required: Engineer to complete test steps in HSD. Use MSR 0xE2 bits and `cstate_focus` to implement policy check.

**Priority**: Medium — `NGA_MAIN`, `plc.feature.p1`; C6A demotion policy determines idle power efficiency under varying uncore conditions
