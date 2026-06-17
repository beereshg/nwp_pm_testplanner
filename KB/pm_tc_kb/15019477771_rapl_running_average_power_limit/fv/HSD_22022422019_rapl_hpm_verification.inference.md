# Deep Analysis: RAPL HPM Verification

| Field | Value |
|-------|-------|
| **HSD ID** | 22022422019 |
| **Title** | RAPL HPM verification |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Socket RAPL |
| **Sub-Feature** | RAPL HPM message — PL1/PL2/Fast RAPL bit verification in HPM to CBBs |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies **RAPL HPM message bits** from iMH Punit to CBB Punit for each RAPL use case:
- **PL1 active**: PL1 HPM bit set in message to CBBs
- **PL2 active**: PL2 HPM bit set in message
- **Fast RAPL active**: FAST_RAPL bit set in message

Reference: DMR HAS §HPM-messaging-for-RAPL-RACL. Tags: `DMR_PO`, `plc.feature.p2`, `PMSS_NWP_READINESS_CHECK`.

On NWP: single `imh0` sends HPM messages to `cbb0` and `cbb1`. Verify HPM bit correctness for both CBBs.

---

## Section B: NWP-Specific Test Procedure

### RAPL HPM Message Bits (NWP)

| RAPL State | HPM Bit | Verification |
|------------|---------|-------------|
| PL1 active | PL1_THROTTLE_BIT | Set when power > PL1 and RAPL throttling |
| PL2 active | PL2_THROTTLE_BIT | Set during PL2 burst window |
| Fast RAPL | FAST_RAPL_BIT | Set when Fast RAPL engaged |
| Not throttling | All bits = 0 | Normal operation |

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Run cpu_rapl PMx | `python runPmx.py -x nwp.xml -p cpu_rapl -tM 6 -M 3` |
| 2 | Set PL1 below current power → trigger PL1 throttle | Power > PL1 |
| 3 | Verify PL1_THROTTLE_BIT set in HPM to cbb0 AND cbb1 | Check HPM message register |
| 4 | Set PL2 limit and run burst workload → trigger PL2 | Power > PL2 burst |
| 5 | Verify PL2_THROTTLE_BIT set in HPM to cbb0 AND cbb1 | Check HPM message register |
| 6 | Force Fast RAPL (large power transient) → verify FAST_RAPL_BIT | Cross-ref with TC 22022421955 |
| 7 | Verify bit cleared when RAPL not active | Normal operation: bits = 0 |

### NWP HPM Message Debug Access
```python
# NWP HPM message verification (imh0 → cbb0, cbb1)
# Check RAPL HPM bit in cbb0 Punit HPM status register
sv.socket0.cbb0.punit.<hpm_status_reg>.show()
sv.socket0.cbb1.punit.<hpm_status_reg>.show()
```

### Pass Criteria
- PL1_THROTTLE_BIT = 1 in HPM message to both CBBs when PL1 active
- PL2_THROTTLE_BIT = 1 when PL2 burst active
- FAST_RAPL_BIT = 1 when Fast RAPL engaged
- All bits = 0 in normal (non-throttle) operation

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; verify RAPL HPM bits to both cbb0 and cbb1 from single imh0**

1. `python runPmx.py -x nwp.xml -p cpu_rapl -tM 6 -M 3`
2. Trigger PL1, PL2, Fast RAPL independently; verify corresponding HPM bits in messages to cbb0 and cbb1
3. Reference: DMR HAS §HPM-messaging-for-RAPL-RACL (applicable to NWP with same message structure)

**Priority**: High — `plc.feature.p2`; HPM message correctness is the communication path between iMH and CBBs for RAPL — critical for CBB frequency decisions
