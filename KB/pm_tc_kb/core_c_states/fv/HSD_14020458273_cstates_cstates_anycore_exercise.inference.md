# Deep Analysis: [Solar] CStates - CStates_AnyCore -- Exercise

| Field | Value |
|-------|-------|
| **HSD ID** | 14020458273 |
| **Title** | [Solar] CStates - CStates_AnyCore -- Exercise |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Core C-States |
| **Sub-Feature** | Solar AnyCore Exercise — stress testing all C-states on any core (no residency verification) |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test uses the **Solar** tool in **Exercise mode** to stress-test core C-states (C1 and C6) across all cores. Exercise mode = no residency verification; just stress for stability. Functional on NWP (C1, C6A/C6S/C6S-P all available).

Command variants:
1. Simplified: `/usr/bin/solar/solar.sh /cstate -scope 0:0:100 -states C1,C6 -mode e /logpath . /log_ip_disables`
2. Full NGA: `/usr/bin/solar/solar.sh /cfg <NWP Solar XML> /cstate -d hour:@{TestLine.TestStageEstimatedTime} /logpath`

Tags: `DMR_PO`, `NGA_MAIN`, `plc.feature.p1`.

---

## Section B: NWP-Specific Test Procedure

### NWP Solar AnyCore Exercise Command

```bash
# NWP: cstate exercise on all 96 cores
/usr/bin/solar/solar.sh \
  /cstate -scope 0:0:100 -states C1,C6 -mode e \
  /logpath . \
  /log_ip_disables
```

Or via NGA XML:
```bash
/usr/bin/solar/solar.sh \
  /cfg /usr/local/python/newport/pm/Solar/Solar_orderedleave_crossproduct.xml \
  /cfg /usr/lib/python3/dist-packages/newport/pm/Solar/SOLAR_NWP_XMLS/Exercise/CSTATES/Cstates_anycore_exercise.xml \
  /cstate -d hour:@{TestLine.TestStageEstimatedTime} \
  /logpath
```

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Verify NWP Solar XML paths exist | `Cstates_anycore_exercise.xml` for NWP |
| 2 | Run Solar AnyCore Exercise | Command above; `-scope 0:0:100` = all 100% of cores |
| 3 | Run for required duration | Per NGA `TestStageEstimatedTime` |
| 4 | Monitor for hangs, MCAs | Any failure = test failure |
| 5 | Check Solar log | `solar.log` in /logpath; look for errors |

### NWP Notes
- `-scope 0:0:100` = socket 0, tile 0, 100% of cores = all 96 NWP cores
- `-states C1,C6` covers all functional core C-states on NWP
- C6 on NWP includes C6A, C6S, C6S-P depending on hint
- No SMT on NWP — solar exercises per physical core

### Pass Criteria
- No hang during Solar exercise
- No MCA during exercise
- Solar job completes without fatal errors
- System stable after run

---

## Section F: Recommendation

**Recommendation: ADOPT — Adapt Solar XML path `diamondrapids` → `newport`; `-scope 0:0:100` covers all 96 NWP cores; `-states C1,C6` functional**

**Priority**: High — `NGA_MAIN`, `plc.feature.p1`; AnyCore exercise is the primary stress test for C-state infrastructure correctness
