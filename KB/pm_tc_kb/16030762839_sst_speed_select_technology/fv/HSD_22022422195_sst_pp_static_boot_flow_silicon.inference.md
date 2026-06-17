# Deep Analysis: SST-PP Static Boot Flow Silicon

| Field | Value |
|-------|-------|
| **HSD ID** | 22022422195 |
| **Title** | SST-PP Static Boot flow_silicon |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | SST |
| **Sub-Feature** | SST-PP — verify PP profile applied after boot (BIOS knob ConfigTdp=1..5) |
| **NWP Disposition** | **Skip_ZBB** |

---

## Section A: NWP Disposition & Justification

**Disposition: Skip_ZBB**

**Reason**: This TC requires **SST-PP** via BIOS knob `ConfigTdp=1..5` to select different performance profiles at boot. SST-PP is on the NWP ZBB list — not functional on NWP initial silicon.

Test steps:
1. Enable SST-PP profile via `ConfigTdp=1/2/3/4/5` BIOS knob
2. Boot and verify profile resolved correctly via `runPmx.py -x nwp.xml -p sst_pp`

All 5 profile variants require SST-PP functionality.

Tags: `DMR_PO`, `plc.feature.p1`, `PMSS_NWP_READINESS_CHECK`.

---

## Section F: Recommendation

**Recommendation: SKIP — SST-PP is ZBB on NWP; ConfigTdp boot flow not applicable; revisit for future NWP stepping**

**Priority**: N/A — ZBB blocker
