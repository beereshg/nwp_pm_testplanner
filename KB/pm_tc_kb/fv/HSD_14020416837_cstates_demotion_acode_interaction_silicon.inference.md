# Deep Analysis: CStates Demotion: Acode Interaction Silicon

| Field | Value |
|-------|-------|
| **HSD ID** | 14020416837 |
| **Title** | CStates: Demotion: Acode interaction_silicon |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Core C-States |
| **Sub-Feature** | C6 demotion via Acode (Autonomous Performance Controller) — A2P capability vector bit 5 |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This **negative test** verifies that C6 demotion via Acode interaction does NOT produce additional C1 residency unexpectedly. Checks that:
- ACP (Autonomous Core Perimeter) has enabled C6 demotion
- A2P ACP capability vector bit 5 is set

A2P to PCODE data (from test steps):

| Bit | Field | Description |
|-----|-------|-------------|
| 0:0 | ACP_EN | Enable Autonomous Core Perimeter |
| 1:1 | AUTO_VF_MGMT | Enable Autonomous V/F Management by Acode |
| 2:2 | APS_EN | Enable Autonomous FI |
| 5:5 | ACP_C6_DEMOTION_EN | Enable ACP C6 demotion |

Uses `pm.Idle_PM.cstates.cstate_focus.check_acp_c6_demotion_focus()`. Tags: `NGA_MAIN`, `plc.feature.p1`.

---

## Section B: NWP-Specific Test Procedure

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Boot SVOS with C6 enabled | ACP active |
| 2 | Run ACP demotion check | `import pm.Idle_PM.cstates.cstate_focus as cf; cf.check_acp_c6_demotion_focus()` |
| 3 | Verify ACP_EN = 1 | Acode autonomous core perimeter active |
| 4 | Verify ACP_C6_DEMOTION_EN (bit 5) | A2P capability vector bit 5 set |
| 5 | **Negative check**: Enable demotion and verify NO extra C1 residency | This is a negative test — no unexpected demotions |
| 6 | Verify C1 residency matches expectations | Should not spike when Acode demotion is enabled |

### NWP Notes
- ACP (Acode) C6 demotion capability same mechanism on NWP
- NWP python package: `newport.pm.Idle_PM.cstates.cstate_focus`
- `NGA_MAIN`: automate via NGA

### Pass Criteria
- A2P capability vector bit 5 (`ACP_C6_DEMOTION_EN`) = 1
- No unexpected C1 residency when Acode demotion enabled
- Demotion only occurs when explicitly expected (correct uncore hint)

---

## Section F: Recommendation

**Recommendation: ADOPT — Acode A2P interface same on NWP; adapt Python import to NWP package; run as negative test**

**Priority**: Medium — `NGA_MAIN`, `plc.feature.p1`; unexpected C1 residency from Acode demotion is a known source of idle power regression
