# Deep Analysis: CState Entry Actions: Verify Flow MC6

| Field | Value |
|-------|-------|
| **HSD ID** | 14023097313 |
| **Title** | CState Entry Actions: Verify flow MC6 |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Core C-States |
| **Sub-Feature** | MC6 entry flow — all cores in module in C6 → module enters MC6 |
| **NWP Disposition** | **Skip_ZBB** |

---

## Section A: NWP Disposition & Justification

**Disposition: Skip_ZBB**

This test verifies the **MC6 entry flow**: all cores in a compute module enter C6, then the module enters MC6 (Ring C6). Pass criteria check:
- `sv.sockets.cbbs.computes.pmas.pmsb.gvctrl_status8.gv_module_in_mc6 = 1`
- MSR 0x664 increasing

**NWP ZBB restriction**: **MC6 (Ring C6) is ZBB on NWP**. The module-level MC6 flow is not validated on NWP silicon in N-1 scope.

**Disposition: Skip_ZBB** — MC6/Ring C6 ZBB prerequisite.

---

## Section F: Recommendation

**Recommendation: SKIP — MC6 entry flow is ZBB on NWP**

MC6 requires Ring C6 infrastructure which is ZBB. Test cannot run on NWP N-1 silicon.

**Priority**: N/A (ZBB)
