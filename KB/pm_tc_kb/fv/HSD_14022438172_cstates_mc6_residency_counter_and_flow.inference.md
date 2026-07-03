# Deep Analysis: CStates MC6 Residency Counter and Flow Check

| Field | Value |
|-------|-------|
| **HSD ID** | 14022438172 |
| **Title** | CStates MC6 residency counter and flow check |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Core C-States |
| **Sub-Feature** | MC6 (Module C6 / Ring C6) residency counter and flow |
| **NWP Disposition** | **Skip_ZBB** |

---

## Section A: NWP Disposition & Justification

**Disposition: Skip_ZBB**

This test verifies **MC6 (Module C6 / Ring C6)** residency. MC6 requires all cores in a module to be in C6, followed by the module entering a deeper shutdown (ring/LLC powered down).

**NWP ZBB restriction**: **MC6 (Ring C6) is Zero Bug Baseline (ZBB) on NWP**. The Ring C6/MC6 infrastructure is not validated on NWP silicon in the N-1 validation phase.

**Disposition: Skip_ZBB** — MC6/Ring C6 is a prerequisite feature that is ZBB on NWP.

---

## Section B: NWP ZBB Impact

| Feature | NWP Status |
|---------|------------|
| Core C6A | Functional (Runnable) |
| Core C6S | Functional (Runnable) |
| Core C6S-P | Functional (Runnable) |
| MC6 (Ring C6) | **ZBB — not functional** |
| PkgC6 | ZBB |

### MC6 Residency Register (informational)
```
sv.socket0.cbb0.compute3.pma24.pmsb.gvctrl_status8.gv_module_in_mc6
MSR 0x664 (MC6 residency counter)
```
These registers are ZBB on NWP — not expected to show MC6 activity.

---

## Section F: Recommendation

**Recommendation: SKIP — MC6 (Ring C6) is ZBB on NWP; no MC6 residency expected**

This test case does not apply to NWP N-1 validation scope. Revisit when MC6 is enabled on NWP.

**Priority**: N/A (ZBB)
