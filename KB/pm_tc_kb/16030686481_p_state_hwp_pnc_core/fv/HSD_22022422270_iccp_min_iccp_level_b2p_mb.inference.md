# Deep Analysis: ICCP — Min_ICCP_Level B2P MB Functionality

| Field | Value |
|-------|-------|
| **HSD ID** | 22022422270 |
| **Title** | ICCP: Min_ICCP_Level B2P MB Functionality |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | Pstate Stack |
| **Sub-Feature** | ICCP — Minimum ICCP Level via B2P Mailbox (WRITE_PM_CONFIG) |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies the **Min ICCP Level** field in the B2P (BIOS-to-PCode) WRITE_PM_CONFIG mailbox command. The test:
1. Writes various `Min_ICCP_Level` values (0x0 to 0xF) via B2P mailbox
2. Verifies valid levels are resolved (PCode enforces minimum ICCP license level)
3. Verifies invalid/unsupported levels are handled without causing watchdog timeouts

Related GNR risk: watchdog timer expired when writing `0x8` to `Min_ICCP_Level (0x95, 0x2)` — motivates this test to sweep all bit combinations.

On NWP, the same B2P mailbox interface exists with `WRITE_PM_CONFIG` command. Primary adaptation: `dmr.xml` → `nwp.xml`.

**Key Justification:**
- B2P WRITE_PM_CONFIG mailbox is present on NWP
- Min ICCP Level functionality same architecture
- GNR watchdog risk motivates full bit sweep validation
- `DMR_PO` tag: silicon validation bring-up priority
- `PMSS_NWP_READINESS_CHECK` tag: evaluated for NWP

---

## Section B: NWP-Specific Test Procedure

### B2P Mailbox Reference

| Mailbox Command | ID | Purpose |
|----------------|-----|---------|
| `WRITE_PM_CONFIG` | 0x95 | Write PM configuration fields including Min ICCP Level |
| Subcommand | 0x2 | Min_ICCP_Level field selector |

**Spec ref**: `https://docs.intel.com/documents/primecode/has/DMR/BIOS%20Mailbox/B2P_mailbox_specification.html#WRITE_PM_CONFIG` (NWP equivalent URL TBD)

### Adapted Test Steps

| Step | Action | NWP Adaptation |
|------|--------|----------------|
| 1 | Run turbo plug-in to verify baseline ICCP behavior | `python runPmx.py -x nwp.xml -p turbo -tM 60` |
| 2 | Write Min_ICCP_Level = 0x0 via B2P WRITE_PM_CONFIG | Same B2P mailbox call |
| 3 | Verify ICCP license level ≥ 0x0 (no constraint) | Read ICCP license status register |
| 4 | Write Min_ICCP_Level = 0x1, 0x2, 0x3 (valid levels) | Verify each is resolved |
| 5 | Write Min_ICCP_Level = 0x4..0xF (invalid/unused levels) | Verify no watchdog timeout; PCode handles gracefully |
| 6 | Verify no MCAs during invalid value sweep | Monitor for watchdog or IERR |

### NWP Min ICCP Level Effects

| Min_ICCP_Level | Minimum License Enforced | Effect |
|----------------|--------------------------|--------|
| 0x0 | None (default) | Normal ICCP operation |
| 0x1 | Level 1 (128 Heavy min) | Cores forced to ≥ Level 1 license |
| 0x2 | Level 2 (256 Heavy min) | Cores forced to ≥ Level 2 license |
| 0x3 | Level 3 (AMX/AVX-512 min) | All cores operate at highest cdyn |
| 0x4..0xF | Invalid | PCode must handle without crash |

### NWP Pass Criteria
- Valid levels (0x0–0x3) programmed and resolved correctly
- Invalid levels (0x4–0xF) handled without watchdog timeout or IERR
- B2P mailbox command returns success/failure code appropriately
- No machine check errors during sweep

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; critical risk from GNR watchdog timeout precedent**

Min ICCP Level B2P mailbox sweep is directly applicable on NWP. The GNR watchdog timeout risk makes this a high-priority validation.

Required adaptations:
1. `python runPmx.py -x nwp.xml -p turbo -tM 60`
2. Get NWP B2P mailbox specification URL (WRITE_PM_CONFIG for NWP)
3. Verify valid Min_ICCP_Level range on NWP (may differ from DMR if 4-level ICCP vs 3-level)

**Priority**: High — `DMR_PO`; GNR watchdog risk precedent; ICCP mailbox stability validation
