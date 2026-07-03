# Deep Analysis: Fast RAPL - HPM Message Verification

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421955 |
| **Title** | Fast rapl - hpm message verification |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Socket RAPL |
| **Sub-Feature** | Fast RAPL HPM message — verify FAST_RAPL_BIT in HPM message to CBBs |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies the **FAST RAPL bit in the RAPL HPM Message** from iMH Punit to CBBs:
- Run workload to exercise Fast RAPL
- Verify `FAST_RAPL_BIT` is set in the HPM message to CBBs when fast RAPL is active

On NWP: imh0 sends HPM messages to cbb0 and cbb1 during RAPL. The `FAST_RAPL_BIT` field must be correct in the HPM message for both CBBs. Tags: `DMR_PO`, `plc.feature.p2`, `PMSS_NWP_READINESS_CHECK`.

---

## Section B: NWP-Specific Test Procedure

### NWP HPM Message Path

| Message | Path |
|---------|------|
| HPM RAPL message | `imh0 Punit → cbb0 Punit`, `imh0 Punit → cbb1 Punit` |
| FAST_RAPL_BIT | In HPM message payload; verify when Fast RAPL triggered |

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Run Fast RAPL PMx | `python runPmx.py -x nwp.xml -p cpu_rapl -tM 6 -M 3` |
| 2 | Run workload to drive power above PL1 (triggers Fast RAPL) | PTU or CPU stress |
| 3 | Capture HPM message to cbb0 | Check `FAST_RAPL_BIT` field in message |
| 4 | Capture HPM message to cbb1 | Verify same bit set for both CBBs |
| 5 | Verify FAST_RAPL_BIT = 1 when Fast RAPL active | HPM debug log or register |
| 6 | Verify FAST_RAPL_BIT = 0 when RAPL not in fast mode | Bit correctly deasserted |

### NWP Fast RAPL Trigger Condition
- Fast RAPL engages when power exceeds PL1 threshold rapidly
- iMH (imh0) Punit decides Fast RAPL and communicates via HPM to both CBBs
- NWP: single iMH → HPM message verification simpler (only imh0 source)

### Pass Criteria
- `FAST_RAPL_BIT=1` in HPM message to cbb0 AND cbb1 when Fast RAPL active
- `FAST_RAPL_BIT=0` when Fast RAPL not active
- HPM message sent to both CBBs (not just cbb0)

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; verify FAST_RAPL_BIT in HPM messages to both cbb0 and cbb1**

1. `python runPmx.py -x nwp.xml -p cpu_rapl -tM 6 -M 3`
2. NWP: single `imh0` source; verify HPM to `cbb0` and `cbb1` both carry FAST_RAPL_BIT correctly
3. Trigger Fast RAPL by exceeding PL1 with workload

**Priority**: Medium — `plc.feature.p2`; FAST_RAPL_BIT in HPM validates the communication path from iMH to CBBs for fast power management decisions
