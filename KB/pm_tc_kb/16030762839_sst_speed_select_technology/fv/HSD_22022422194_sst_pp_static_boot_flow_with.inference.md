# Deep Analysis: SST-PP Static Boot Flow with OSPL

| Field | Value |
|-------|-------|
| **HSD ID** | 22022422194 |
| **Title** | SST-PP Static Boot flow with OSPL |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | SST |
| **Sub-Feature** | SST-PP — boot flow after runtime MCU update (OSPL); SST state retained |
| **NWP Disposition** | **Skip_ZBB** |

---

## Section A: NWP Disposition & Justification

**Disposition: Skip_ZBB**

**Reason**: This test requires **SST-PP** to be functional (boot into different PP profiles, verify retention after OSPL). SST-PP is on the NWP ZBB list.

Test steps:
1. Run `runPmx.py -x nwp.xml -p sst_pp` → SST-PP not functional → Skip
2. Apply OSPL (OS-present live update)
3. Re-run `runPmx.py -x nwp.xml -p sst_pp` to verify state retention

Manual steps also require switching to SST-PP level 3, doing OS page flip — both require SST-PP functional.

Tags: `DMR_PO`, `PMSS_NWP_READINESS_CHECK`.

---

## Section F: Recommendation

**Recommendation: SKIP — SST-PP is ZBB on NWP; OSPL + SST-PP retention test not applicable; revisit for future NWP stepping**

**Priority**: N/A — ZBB blocker
