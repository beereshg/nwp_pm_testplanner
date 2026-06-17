# Deep Analysis: [Solar] CStates - CStates_AnyCore_Random -- Exercise

| Field | Value |
|-------|-------|
| **HSD ID** | 14020458312 |
| **Title** | [Solar] CStates - CStates_AnyCore_Random -- Exercise |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Core C-States |
| **Sub-Feature** | Solar AnyCore Random Exercise — random C-state ordering, stress only |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test uses Solar in **Random Exercise mode** (`-r -mode e`): C-states are exercised in random order across cores. Random ordering stresses corner cases in entry/exit sequencing. Functional on NWP.

Command: `/usr/bin/solar/solar.sh /cstate -scope 0:0:100 -states C1,C6 -r -mode e /logpath . /log_ip_disables`

Tags: `NGA_MAIN`, `plc.feature.p1`.

---

## Section B: NWP-Specific Test Procedure

### NWP Solar AnyCore Random Exercise Command

```bash
# NWP: random exercise - all 96 cores, C1 and C6, random order
/usr/bin/solar/solar.sh \
  /cstate -scope 0:0:100 -states C1,C6 -r -mode e \
  /logpath . \
  /log_ip_disables
```

Or via NGA XML:
```bash
/usr/bin/solar/solar.sh \
  /cfg /usr/local/python/newport/pm/Solar/Solar_orderedleave_crossproduct.xml \
  /cfg /usr/lib/python3/dist-packages/newport/pm/Solar/SOLAR_NWP_XMLS/Exercise/CSTATES/Cstates_anycore_random_exercise.xml \
  /cstate -d hour:@{TestLine.TestStageEstimatedTime} /logpath
```

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Run Solar AnyCore Random in Exercise mode | `-r -mode e` |
| 2 | Solar randomizes core C-state request order | Exercises inter-core C-state interactions |
| 3 | Run for NGA duration | Per `TestStageEstimatedTime` |
| 4 | Monitor for hangs, MCAs | Random ordering can expose race conditions |
| 5 | Check Solar log | Pass = no errors |

### Random vs Ordered
| Mode | `-r` Flag | Pattern |
|------|-----------|---------|
| Ordered | No `-r` | Fixed sequence |
| Random | `-r` | Random C-state × core ordering |

Random mode is more effective at exposing race conditions in C-state arbitration.

### Pass Criteria
- No hang during random exercise
- No MCA
- Solar job completes successfully
- System stable after run

---

## Section F: Recommendation

**Recommendation: ADOPT — Same as ordered exercise but add `-r` flag; adapt Solar XML path `diamondrapids` → `newport`**

**Priority**: High — `NGA_MAIN`, `plc.feature.p1`; random ordering maximizes C-state race condition coverage across 96 NWP cores
