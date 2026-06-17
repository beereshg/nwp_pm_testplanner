# Deep Analysis: [Solar] CStates - CStates_AnyCore_Random -- Verify

| Field | Value |
|-------|-------|
| **HSD ID** | 14020458388 |
| **Title** | [Solar] CStates - CStates_AnyCore_Random -- Verify |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Core C-States |
| **Sub-Feature** | Solar AnyCore Random Verify — residency verification with random C-state ordering |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test uses Solar in **Random Verify mode** (`-r -mode v`): C-states are randomized AND residency is verified. Most comprehensive Solar C-state test. Functional on NWP.

Command: `/usr/bin/solar/solar.sh /cstate -scope 0:0:100 -states C1,C6 -r -mode v /logpath . /log_ip_disables`

Tags: `NGA_MAIN`, `plc.feature.p1`.

---

## Section B: NWP-Specific Test Procedure

### NWP Solar AnyCore Random Verify Command

```bash
# NWP: random verify - all 96 cores, C1 and C6, random order, verify residency
/usr/bin/solar/solar.sh \
  /cstate -scope 0:0:100 -states C1,C6 -r -mode v \
  /logpath . \
  /log_ip_disables
```

Or via NGA XML:
```bash
/usr/bin/solar/solar.sh \
  /cfg /usr/local/python/newport/pm/Solar/Solar_orderedleave_crossproduct.xml \
  /cfg /usr/lib/python3/dist-packages/newport/pm/Solar/SOLAR_NWP_XMLS/Exercise/CSTATES/Cstates_anycore_random_verify.xml \
  /cstate -d hour:@{TestLine.TestStageEstimatedTime} \
  /logpath
```

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Run Solar AnyCore Random Verify | `-r -mode v` |
| 2 | Solar randomizes C-state request order across 96 cores | Random inter-core ordering |
| 3 | Solar verifies residency for each requested C-state | Residency counter checked |
| 4 | Run for NGA duration | Per `TestStageEstimatedTime` |
| 5 | Check Solar verify log | Pass = all cores achieve expected residency |

### Solar Test Matrix (NWP)

| TC | Mode | Random | Purpose |
|----|------|--------|---------|
| 14020458273 | Exercise | No | Stability |
| 14020458300 | Verify | No | Ordered residency |
| 14020458312 | Exercise | Yes | Random stability |
| **14020458388** | **Verify** | **Yes** | **Random residency — most comprehensive** |

### Pass Criteria
- All 96 NWP cores achieve C6 residency in random ordering
- C1 residency verified where requested
- No failures, hangs, or MCAs
- Solar verify passes for all cores in scope

---

## Section F: Recommendation

**Recommendation: ADOPT — Combine `-r` and `-mode v`; adapt Solar XML `diamondrapids` → `newport`; this is the most comprehensive C-state verification TC**

**Priority**: High — `NGA_MAIN`, `plc.feature.p1`; random verify is the definitive C-state correctness test for NWP — must pass before NGA production
