# Deep Analysis: CState Entry Actions: Verify Flow C6S-P

| Field | Value |
|-------|-------|
| **HSD ID** | 14020647451 |
| **Title** | CState Entry Actions: Verify flow C6S-P |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Core C-States |
| **Sub-Feature** | C6S-P (Predictive C6S) entry flow — FIVR shutdown |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies the **C6S-P entry flow**. C6S-P = C6S with predictive voltage collapse (FIVR shutdown). Deepest core C-state — FIVR powered down. Functional on NWP.

Tags: `logs`, `cmdline`, `DMR_PO`, `plc.feature.p1`.

---

## Section B: NWP-Specific Test Procedure

### C6S-P Entry Pass/Fail Criteria

| Signal | Expected After C6S-P Entry |
|--------|-----------------------------|
| `core_cstate` | C6 |
| PICLET FSM | `PICLET_ENABLED` |
| SRL | `SRL_ACTIVE` |
| `BGF_RUN` | 0 |
| `CORE_PWR_GOOD` | 0 → **FIVR off** (distinguishes C6S-P) |
| `PLL_LOCK` | 0 |
| Target Volt | 0 |
| Target Freq | 0 |
| Target PS | 7 |
| FIVR | OFF (power collapsed — key differentiator from C6S) |

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Boot SVOS with C6 enabled | C6S-P functional on NWP |
| 2 | Run cstates PMx | `python runPmx.py -x nwp.xml -p cstates -H 1 -M 5` |
| 3 | OR standalone residency test | `python /usr/lib/python3/dist-packages/newport/pm/Idle_PM/cstates/ccx_residency_test.py` |
| 4 | Idle core with C6S-P MWAIT hint | OS requests predictive C6S |
| 5 | Verify FIVR powered down | `CORE_PWR_GOOD=0`; FIVR in 0 state |
| 6 | Verify cache flushed (S = flush) | MLC/L2 + LLC flushed same as C6S |
| 7 | Trigger interrupt to exit | Core FIVR powers up; core returns to C0 |

### C6S-P Key Differentiator (NWP)
- C6S-P = C6S + FIVR shutdown (predictive voltage collapse)
- FIVR turn-off = additional power savings vs C6S
- Requires predictive algorithm to determine FIVR won't be needed soon

### Pass Criteria
- FIVR powered OFF (`CORE_PWR_GOOD = 0`, FIVR state = 0) in C6S-P
- Cache flush occurred (MLC/L2 + LLC)
- Core exits C6S-P with FIVR restoration before first instruction

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; C6S-P functional on NWP; verify FIVR shutdown in addition to cache flush**

**Priority**: High — `plc.feature.p1`; C6S-P is the deepest single-core C-state — maximum idle power savings; FIVR shutdown verification critical
