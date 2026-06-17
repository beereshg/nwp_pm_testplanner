# Deep Analysis: Solar Cross Products

| Field | Value |
|-------|-------|
| **HSD ID** | 14019764517 |
| **Title** | Solar Cross Products |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | (blank) |
| **Sub-Feature** | Solar PM stress tool — concurrent multi-feature stress (DVF, C-states, RAPL, etc.) |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

Solar is a PM stress tool that exercises multiple PM features simultaneously. It verifies that PM features can run concurrently without conflicts per spec. Solar has DMR XML configuration; NWP requires adaptation to use NWP XML.

---

## Section B: NWP-Specific Test Procedure

### NWP Solar Configuration
```bash
# Solar for NWP — adapt XML paths
# DMR Solar XML: .../diamondrapids/pm/Solar/SOLAR_DMR_XMLS/...
# NWP Solar XML: .../newport/pm/Solar/SOLAR_NWP_XMLS/...
```

### Features Stressed by Solar
| Feature | NWP Status |
|---------|------------|
| DVF (frequency scaling) | Functional |
| C-states (core-level) | Functional (C1E, C6A/C6S) |
| RAPL power limiting | Functional |
| HWP/P-states | Functional |
| Thermals (PROCHOT) | Functional |
| SST-TF / PCT | Functional |

**Note**: Solar should be configured to EXCLUDE ZBB features (SST-PP, SST-BF, PkgC6, HGS).

### Pass Criteria
- Solar runs for 30+ minutes without crash, MCA, or hang
- All featured PM features co-exist without conflicts
- No unexpected throttle or frequency collapse

---

## Section F: Recommendation

**Recommendation: ADOPT — Solar XML: `SOLAR_DMR_XMLS` → `SOLAR_NWP_XMLS`; exclude ZBB features from Solar config (SST-PP, SST-BF, PkgC6, HGS); NWP 2 CBBs × 48 cores**

**Priority**: High — Solar concurrent stress is the highest-value cross-product validation; verifies PM feature co-existence
