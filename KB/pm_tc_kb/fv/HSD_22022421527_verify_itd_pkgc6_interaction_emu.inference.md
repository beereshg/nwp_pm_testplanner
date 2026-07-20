# Deep Analysis: [ITD] Verify ITD and PkgC6 Interaction_emulation

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421527 |
| **Title** | [ITD] Verify ITD and PkgC6 Interaction_emulation |
| **Date** | 2026-07-19 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | SoC Thermal Management > ITD |
| **Sub-Feature** | ITD Common Controls — PkgC6 Emulation |
| **NWP Disposition** | **ZBB_N/A** |

---


## Test Case Intent

Validates the ITD x PkgC6 emulation interaction — ZBB on NWP (no PkgC6) scenario defined in [TCD 16031170075 — ITD Common Controls](https://hsdes.intel.com/appstore/article-one/#/16031170075) §5. Environment: N/A — ZBB.

## Section A: NWP Disposition & Justification

**Disposition: ZBB_N/A — PkgC6 is not POR on NWP**

NWP does not support PkgC6 (Zero Bug Bounce). This TC validates ITD behavior during PkgC6 in emulation, which is not applicable on NWP.

**Key facts:**
- NWP has no PkgC6 (ZBB per NWP PM MAS)
- ITD x PkgC6 interaction is DMR-specific
- TC remains in HSD for DMR reference but is not NWP POR

---

## Section B: NWP-Specific Test Procedure

**N/A — ZBB on NWP. No test execution required.**

---

## Section C: Pass/Fail Measurement Method

**N/A — ZBB on NWP.**
