# Deep Analysis: HGS Functionality Silicon

| Field | Value |
|-------|-------|
| **HSD ID** | 22022422198 |
| **Title** | HGS Functionality_silicon |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | SST |
| **Sub-Feature** | HGS — HFI table update notification, OS non-compliance throttle, THERM_STATUS feedback bit |
| **NWP Disposition** | **Skip_ZBB** |

---

## Section A: NWP Disposition & Justification

**Disposition: Skip_ZBB**

**Reason**: HGS (Hardware Guided Scheduling) is on the NWP ZBB list. This test verifies:
1. Notification interrupt sent to OS after HFI table update
2. Pcode throttles core to Pn if OS is non-compliant (doesn't idle core)
3. `IA32_PACKAGE_THERM_STATUS[HW_FEEDBACK]` set after HFI table update

Since HGS is not implemented on NWP, none of these behaviors are expected.

Tags: `New_content`, `plc.feature.p1`, `PMSS_NWP_READINESS_CHECK`.

---

## Section F: Recommendation

**Recommendation: SKIP — HGS is ZBB on NWP; HFI interrupt, OS compliance throttle, and THERM_STATUS feedback not applicable; revisit for future NWP stepping**

**Priority**: N/A — ZBB blocker
