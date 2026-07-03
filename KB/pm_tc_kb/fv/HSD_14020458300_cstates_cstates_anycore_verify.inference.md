# Deep Analysis: [Solar] CStates - CStates_AnyCore -- Verify

| Field | Value |
|-------|-------|
| **HSD ID** | 14020458300 |
| **Title** | [Solar]_CStates-CStates_AnyCore--Verify |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Core C-States |
| **Sub-Feature** | Solar AnyCore Verify — residency verification for C1 and C6 on all cores |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test uses the **Solar** tool in **Verify mode** to check C-state residency on all cores. Verify mode = checks residency counters to confirm cores actually entered the requested C-states. Functional on NWP.

Command: `/usr/bin/solar/solar.sh /cstate -scope 0:0:100 -states C1,C6 -mode v /logpath . /log_ip_disables`

Tags: `NGA_MAIN`, `plc.feature.p1`.

---

## Section B: NWP-Specific Test Procedure

### NWP Solar AnyCore Verify Command

```bash
# NWP: verify C-state residency on all 96 cores
/usr/bin/solar/solar.sh \
  /cstate -scope 0:0:100 -states C1,C6 -mode v \
  /logpath . \
  /log_ip_disables
```

Or via NGA XML:
```bash
/usr/bin/solar/solar.sh \
  /cfg /usr/local/python/newport/pm/Solar/Solar_orderedleave_crossproduct.xml \
  /cfg /usr/lib/python3/dist-packages/newport/pm/Solar/SOLAR_NWP_XMLS/Exercise/CSTATES/Cstates_anycore_verify.xml \
  /cstate -d hour:@{TestLine.TestStageEstimatedTime} \
  /logpath
```

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Run Solar AnyCore in Verify mode | `-mode v` vs `-mode e` |
| 2 | Solar idles cores and checks residency | Reads C-state residency counters |
| 3 | Verify C6 residency > threshold | All 96 cores should show C6 residency |
| 4 | Verify C1 residency where expected | C1 during light activity |
| 5 | Check Solar log for failures | Zero cores with zero residency = pass |

### Verify vs Exercise Mode
| Mode | Purpose | Failure Condition |
|------|---------|-------------------|
| Exercise (`-mode e`) | Stress stability | Hang, MCA |
| Verify (`-mode v`) | Check residency | Zero residency on expected cores |

### Pass Criteria
- All 96 NWP cores show C6 residency during idle phase
- C1 residency shown when light workload applied
- Solar verify passes for all cores in scope
- No hang or MCA during verify run

---

## Section F: Recommendation

**Recommendation: ADOPT — Same as exercise TC (14020458273) but `-mode v`; adapt Solar XML path `diamondrapids` → `newport`**

**Priority**: High — `NGA_MAIN`, `plc.feature.p1`; verify mode is the residency correctness check — confirms all 96 cores achieve C6 at idle
