# Deep Analysis: [Solar] CStates - CStates_Unsupported -- Exercise

| Field | Value |
|-------|-------|
| **HSD ID** | 14020672784 |
| **Title** | [Solar] CStates - CStates_unsupported -- Exercise |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Core C-States |
| **Sub-Feature** | Solar: Exercise unsupported MWAIT encodings — verify no hang or bad behavior |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test uses the **Solar** tool to exercise unsupported MWAIT C-state encodings and verify:
- No hang
- No MCA
- Graceful handling of unsupported encodings (treat as C1 or no-op)

Command (from test steps):
```
/usr/bin/solar/solar.sh /cfg .../Cstates_unsupported_Mwait_exercise.xml /logpath . /log_ip_disables
```

NWP: The Solar XML path references `diamondrapids` — NWP equivalent XML must exist. Tags: `NGA_MAIN`, `plc.feature.p1`.

---

## Section B: NWP-Specific Test Procedure

### Command Adaptation

| Component | DMR | NWP |
|-----------|-----|-----|
| Solar XML path | `.../diamondrapids/pm/Solar/SOLAR_DMR_XMLS/Exercise/CSTATES/Cstates_unsupported_Mwait_exercise.xml` | `.../newport/pm/Solar/SOLAR_NWP_XMLS/Exercise/CSTATES/Cstates_unsupported_Mwait_exercise.xml` |
| Solar binary | `/usr/bin/solar/solar.sh` | Same |

### NWP Solar Command
```bash
/usr/bin/solar/solar.sh \
  /cfg /usr/lib/python3/dist-packages/newport/pm/Solar/SOLAR_NWP_XMLS/Exercise/CSTATES/Cstates_unsupported_Mwait_exercise.xml \
  /logpath . \
  /log_ip_disables
```

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Boot SVOS with C-states enabled/disabled by BIOS | Both configs tested |
| 2 | Verify NWP Solar XML exists | `Cstates_unsupported_Mwait_exercise.xml` in NWP Solar XMLs |
| 3 | Run Solar with unsupported MWAIT exercise XML | Command above |
| 4 | Monitor for hangs | No core hangs during unsupported MWAIT |
| 5 | Monitor for MCAs | No MCA triggered by unsupported encoding |
| 6 | Verify system still functional after run | SVOS responsive; no crashes |

### Unsupported MWAIT Encodings
- MWAIT hint values that don't map to defined C-states (e.g., 0x30-0x5F reserved)
- On NWP: unsupported encodings should fall through to C1 (or be ignored)

### Pass Criteria
- No system hang during unsupported MWAIT exercise
- No MCA triggered
- System functional after run
- Solar job completes successfully

---

## Section F: Recommendation

**Recommendation: ADOPT — Adapt Solar XML path from `diamondrapids` to `newport`; verify NWP Solar XML exists or port DMR XML**

**Priority**: Medium — `NGA_MAIN`, `plc.feature.p1`; unsupported MWAIT handling is a robustness requirement — bad OS drivers or buggy applications may send unexpected encodings
