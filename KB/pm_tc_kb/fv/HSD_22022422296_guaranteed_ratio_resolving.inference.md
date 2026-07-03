# Deep Analysis: Guaranteed Ratio Resolving

| Field | Value |
|-------|-------|
| **HSD ID** | 22022422296 |
| **Title** | Guaranteed Ratio resolving |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | Pstate Stack |
| **Sub-Feature** | P1 Guaranteed Ratio resolution considering Active Cores (SST-PP) and SST-BF |
| **NWP Disposition** | **Skip_ZBB** |

---

## Section A: NWP Disposition & Justification

**Disposition: Skip_ZBB**

This test verifies the **full Guaranteed Ratio (P1) resolution** accounting for:
1. Base fused P1 ratio (`IA_P1_RATIO` fuse)
2. Flex Ratio clip (when enabled)
3. **Active Core count via SST-PP** (SST Performance Profile)
4. **Core-specific Class of Service via SST-BF** (SST Base Frequency)

The command is `runPmx.py -x dmr.xml -p sst_pp -tM 60 --retry_count 2`, which uses the SST-PP plug-in.

**SST-PP and SST-BF are both ZBB on NWP.** The full guaranteed ratio resolution algorithm that accounts for SST-PP active-core-count tables and SST-BF per-core CoS cannot be validated on NWP without these features. Additionally, the test is tagged `To_be_ported`, indicating it needs explicit porting work.

**Justification:**
- `sst_pp` plug-in requires SST-PP functionality — **ZBB on NWP**
- SST-BF (per-core Class of Service) — **ZBB on NWP**
- Full P1 resolution algorithm depends on both SST-PP and SST-BF
- `To_be_ported` tag: explicit acknowledgment that porting is needed

---

## Section B: Partial NWP Coverage (Non-SST Path)

The **base P1 resolution** (without SST-PP/SST-BF) is still valid on NWP:

```
NWP P1 = min(IA_P1_RATIO_fuse, FLEX_RATIO) [without SST-PP active-core table]
```

This simpler P1 resolution is covered by TC 22022422287 (Flex Ratio) and the MSR-based P-state TCs.

### NWP P1 Non-SST Validation

```python
# NWP Base P1 Guaranteed Ratio (without SST-PP/BF)

try:
    platform_info = sv.socket0.imh0.punit.ptpcioregs.ptpcioregs.platform_info.read()
    p1_ratio = (platform_info >> 8) & 0xFF
    print(f"Guaranteed P1 Ratio: {p1_ratio}")

    # Cross-check with fused P1
    p1_fuse = sv.socket0.imh0.fuses.punit.ia_p1_ratio.read()
    flex_ratio = sv.socket0.imh0.punit.ptpcioregs.ptpcioregs.flex_ratio.read()
    expected = min(p1_fuse, flex_ratio) if flex_ratio > 0 else p1_fuse
    print(f"Fused P1: {p1_fuse}, Flex Ratio: {flex_ratio}")
    print(f"Expected P1: {expected}, Actual: {p1_ratio}")
    print("PASS" if p1_ratio == expected else "FAIL")
except Exception as e:
    print(f"P1 resolution: {e}")
```

---

## Section C: Action Items

| # | Action | Owner |
|---|--------|-------|
| 1 | Skip full SST-PP/SST-BF P1 resolution — both ZBB on NWP | Test team |
| 2 | Validate base P1 resolution (no SST) via TC 22022422287 + MSR TCs | NWP PM FV team |
| 3 | Create NWP-specific P1 resolution TC without SST-PP dependency | Future work — tag with NWP P1 non-SST |
| 4 | Port when SST features enabled on future NWP stepping | Long-term |

---

## Section F: Recommendation

**Recommendation: SKIP — SST-PP and SST-BF are ZBB on NWP; create NWP-specific P1 TC**

The full P1 resolution algorithm cannot be tested without SST-PP and SST-BF. Base P1 coverage exists via other TCs.

**Priority**: N/A — ZBB skip; base P1 coverage exists via TC 22022422287 and MSR TCs
