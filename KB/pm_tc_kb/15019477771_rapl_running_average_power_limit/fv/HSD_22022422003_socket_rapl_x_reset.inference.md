# Deep Analysis: Socket RAPL x Reset

| Field | Value |
|-------|-------|
| **HSD ID** | 22022422003 |
| **Title** | Socket Rapl x Reset |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Socket RAPL |
| **Sub-Feature** | RAPL cross-product with Cold and Warm Reset flows |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test is a **RAPL × Reset cross-product**, already covered by Reset team test cases:
- Cold Reset + RAPL: TC 14020745287
- Warm Reset + RAPL: TC 14020745288

Flow: Execute Reset flows, then run PM Flexcon + RAPL scripts to verify RAPL functionality post-reset. Tags: `DMR_PO`, `PMSS_NWP_READINESS_CHECK`.

---

## Section B: NWP-Specific Test Procedure

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Run Cold Reset flow | System cold boot; NWP cold reset path |
| 2 | After cold reset: run RAPL PMx | `python runPmx.py -x nwp.xml -p cpu_rapl -tM 6 -M 3` |
| 3 | Verify RAPL energy status, PL1/PL2 limits after cold reset | Defaults restored correctly |
| 4 | Run Warm Reset flow | Warm reset (ACPI S3 or warm reset command) |
| 5 | After warm reset: run RAPL PMx | Verify RAPL state persists or correctly re-initializes |
| 6 | Run Flexcon PM scripts | `flexconPM.py -c NWPSV.ini` for register verification |

### NWP Flexcon Command
```
flexconPM.py -c NWPSV.ini  (not DMRSV.ini)
```

### Pass Criteria
- After cold reset: RAPL MSRs/CSRs at default values; PL1/PL2 correct
- After warm reset: RAPL state correct (per NWP reset behavior spec)
- RAPL energy accounting resumes normally post-reset
- No RAPL lock/hang after reset cycle

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; `DMRSV.ini` → `NWPSV.ini`; cross-reference Reset TCs 14020745287, 14020745288**

1. `python runPmx.py -x nwp.xml -p cpu_rapl -tM 6 -M 3`
2. Test after cold reset (TC 14020745287 analog) and warm reset (14020745288 analog)
3. `flexconPM.py -c NWPSV.ini` for register state verification post-reset

**Priority**: Medium — RAPL × Reset validates power management state machine recovery after system reset
