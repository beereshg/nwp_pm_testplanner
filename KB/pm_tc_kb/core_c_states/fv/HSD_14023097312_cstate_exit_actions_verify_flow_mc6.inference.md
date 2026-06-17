# Deep Analysis: CState Exit Actions: Verify Flow MC6

| Field | Value |
|-------|-------|
| **HSD ID** | 14023097312 |
| **Title** | CState Exit Actions: verify flow MC6 |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Core C-States |
| **Sub-Feature** | MC6 exit flow — module exits MC6 back to C0 |
| **NWP Disposition** | **Skip_ZBB** |

---

## Section A: NWP Disposition & Justification

**Disposition: Skip_ZBB**

This test verifies the **MC6 exit flow**. Pass criteria verify:
- After exit: `gv_module_in_mc6 = 0`
- MSR 0x664 stops increasing
- Limit core_cstate_limit to C1 via `dfx_ctrl_unprotected` to force MC6 exit; verify module state transitions back

**NWP ZBB restriction**: **MC6 (Ring C6) is ZBB on NWP**. MC6 exit cannot be tested if MC6 cannot be entered.

**Disposition: Skip_ZBB** — MC6/Ring C6 ZBB prerequisite.

---

## Section F: Recommendation

**Recommendation: SKIP — MC6 exit flow is ZBB on NWP (cannot enter MC6)**

MC6 is ZBB on NWP. Without MC6 entry, exit flow cannot be exercised.

**Priority**: N/A (ZBB)
