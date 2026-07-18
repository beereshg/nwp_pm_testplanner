# TCD 16031169309 -- PCT - State Transition / Restore

| Field | Value |
|-------|-------|
| **TCD ID** | [16031169309](https://hsdes.intel.com/appstore/article-one/#/16031169309) |
| **Title** | PCT - State Transition / Restore |
| **Status** | open |
| **Owner** | bg3 |
| **Parent TPF** | [16030762939 -- NWP PM PCT](https://hsdes.intel.com/appstore/article-one/#/16030762939) |
| **Child TCs** | *(none yet -- TC TBD)* |
| **Source** | Co-Design T1 coverage gap audit, 2026-07-18 |
| **KB last updated** | 2026-07-18 |

---

## Section 1: Architecture / Micro-architecture and Functionality

This TCD validates **PCT state transitions**: enable-to-disable, disable-to-re-enable, and the register restoration semantics across those transitions. SST-CP can be enabled/disabled dynamically; this TCD verifies that stale CLOS state does not leak, that re-enable produces fresh differentiation, and that the full cycle is idempotent.

> **Architecture overview:** See [TPF 16030762939](https://hsdes.intel.com/appstore/article-one/#/16030762939) for PCT architecture.

### Co-Design Spec Refs (Gap findings #5--#6)

| Finding | Spec Ref |
|---------|----------|
| Runtime enable -> disable -> re-enable cycle uncovered | Dynamic SST-CP control — Intel SST HAS |
| Register-state restoration after disable/re-enable | Persistent CLOS programming model — Intel SST HAS |

---

## Section 2: Interfaces and Protocols

| Interface | Register | State Transition Role |
|-----------|----------|----------------------|
| TPMI | SST_CP_CONTROL.sst_cp_enable | Master enable/disable toggle |
| TPMI | SST_PP_CONTROL.feature_state[1] | SST-TF active flag |
| TPMI | SST_CLOS_ASSOC_* | Persists across disable; must not cause stale differentiation |
| TPMI | SST_CP_CONTROL.HANDSHAKE | Write completion confirmation |
| MSR | IA32_HWP_CAPABILITIES | Must reflect transition (HP->uniform->HP) |

---

## Section 3: Reset / Power / Clocking

- Enable/disable transitions happen at OS runtime via SST tool or direct TPMI write.
- PCode detects eature_state change within 1 slow-loop cycle.
- No reset required for transition — but warm reset must also restore from NVRAM cleanly.

---

## Section 4: Programming Model

| Step | Action | Observable State |
|------|--------|-----------------|
| 1 | Boot with PCT enabled (Partition Count > 0) | HP at P0max, LP at LP_clip |
| 2 | Disable via SST_CP_CONTROL.sst_cp_enable = 0 | All cores at conventional TRL; HWP_CAP uniform |
| 3 | Verify stale CLOS_ASSOC entries do not cause frequency bias | cpuinfo_max_freq uniform across all cores |
| 4 | Re-enable via sst_cp_enable = 1 | HP/LP differentiation restored; HP at P0max |
| 5 | Verify HANDSHAKE/LAST_HANDSHAKE match after each transition | SST_CP_STATUS.LAST_HANDSHAKE == written HANDSHAKE value |

---

## Section 5: Operational Behavior

| Scenario | Expected | TC |
|----------|----------|----|
| Enable -> disable -> re-enable full cycle | Clean transitions; no stale state leaks; frequency restored correctly | *(TC TBD)* |
| Register restoration after re-enable | CLOS assignments produce fresh HP/LP differentiation, not stale | *(TC TBD)* |
| HANDSHAKE verification across transitions | LAST_HANDSHAKE matches on each enable/disable write | *(TC TBD)* |

---

## Section 6: Corner Cases & Error Handling

| Corner Case | Description | Current Coverage | Action Required |
|-------------|-------------|-----------------|----------------|
| **Rapid toggle** | Multiple enable/disable cycles in quick succession | Not covered | TC TBD |
| **Disable during PL1 throttle** | PCT disabled while ordered throttle active; must cleanly exit | Not covered | TC TBD |

---

## Section 7: Security / Safety / Policy

- Runtime state transitions are OS ring-0 operations.
- Stale CLOS state after disable must not create a covert channel for frequency differentiation.

---

## Section 8: References

- [Intel SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) — SST_CP_CONTROL, dynamic enable/disable
- [NWP PM MAS -- PCT](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html)
- Co-Design T1 findings #5--#6 (2026-07-18)
