# TCD: MC Shallow Self Refresh Actions

| Field | Value |
|-------|-------|
| **TCD ID** | [22022421220](https://hsdes.intel.com/appstore/article-one/#/22022421220) |
| **Title** | MC Shallow Self Refresh Actions |
| **Status** | rejected |
| **Owner** | bg3 |
| **Parent TP** | [16030762531 — NWP PM AIPM - Memory Trunk Clock Gating & SSR](https://hsdes.intel.com/appstore/article-one/#/16030762531) |
| **KB last updated** | 2026-06-22 |
| **NWP Disposition** | **ZBB — MC SSR not enabled on NWP (memory PM architecture decision)** |

## Section 1: Architecture / Micro-architecture and Functionality

### Feature Overview

**MC Shallow Self-Refresh (SSR)** places DRAM into self-refresh mode when the memory controller
detects sustained idle. Unlike deep power-down, SSR preserves DRAM state with minimal refresh
current; the MC can exit SSR quickly on any memory access. On LPDDR6, the relevant SSR variant
is **SREF without clock stop** (`sref_sx`) — clock stop and PHY power-down are not supported by
the LPDDR6 PHY (WCK always-on).

Three entry actions are validated under this TCD:

| HSD | Title | Status | Reason |
|-----|-------|--------|--------|
| [22022422910](https://hsdes.intel.com/appstore/article-one/#/22022422910) | MC Shallow Self Refresh_PActive deassertion | **Rejected — ZBB** | SSR not enabled on NWP; PActive never de-asserts for SR entry |
| [22022422918](https://hsdes.intel.com/appstore/article-one/#/22022422918) | MC Shallow Self Refresh_Phy Power Down | **Rejected — ZBB** | PHY power-down not supported on LPDDR6 (WCK always-on; no clock stop) |
| [22022422923](https://hsdes.intel.com/appstore/article-one/#/22022422923) | MC Shallow Self Refresh_SR without clock stop | **Rejected — ZBB** ✅ | SSR ZBB'd on NWP per NWP Memory Feature Set Delta and MC team decision (co-design confirmed) |

### Why ZBB on NWP — Evidence

> **Source**: aipm.md KB (co-design MAS query 2026-05-31), NWP HAS comments

The ZBB root cause is a **memory power management architecture decision**: APD, PPD, LPM, and
SSR are not specified for NWP LPDDR6. This is independent of PkgC6 ZBB, though the two are
compounding:

```
MC SSR preconditions (server platforms):
  1. MC detects sustained idle → asserts PActive de-assert
  2. DRAM enters self-refresh (sref_sx on LPDDR6)
  3. SSR residency accumulated → PkgC6 entry possible

NWP status:
  Step 1: SSR NOT enabled per MC team decision → no SSR entry regardless
  Step 3: PkgC6 also ZBB'd → even if SSR were enabled, no full PkgC path
  PHY: LPDDR6 clock stop = No; WCK always-on; no PHY power-down
```

**Co-design MCP confirmed (2026-06-22)** — all three rejections are correct:

| TC | Rejection | Co-design Source |
|----|-----------|------------------|
| 22022922918 Phy Power Down | ✅ Correct | LPDDR6: no clock stop, WCK always-on, PHY always-on |
| 22022422910 PActive deassertion | ✅ Correct | SSR entry not enabled on NWP; PActive never de-asserts for SR |
| 22022422923 SR without clock stop | ✅ Correct | NWP Memory PM: *"No Shallow Self-Refresh (SSR)"*; MC team ZBB per NWP Memory Feature Set Delta |

**Definitive NWP sources (co-design MCP query 2026-06-22):**
> *"Memory Power Management: No APD/PPD, No LPM1/LPM2/LPM3, No Shallow Self-Refresh (SSR), No Self-Refresh (SR). See HSD. Also documented in NWP Memory Feature Set Delta."*

> *"PkgC6 is not supported on NWP. Therefore, there will not be any SR, nor any SSR flows supported from the IP teams."*

> *"on Oldport (NWP1.0), the MC team ZBBed shallow self-refresh (SSR). I think this is still ZBBed."*

The HAS feature table entry "SREF No Clock Stop = Yes" refers to **spec compliance** only, not validation enablement. The MC team has ZBB'd SSR and it is not a required validation item on NWP.

### LPDDR6 SSR Architecture Reference (DMR)

| Parameter | LPDDR6 Support | Notes |
|-----------|---------------|-------|
| Self-Refresh (SREF) | ✅ Yes | `sref_sx` — warm reset variant |
| Clock Stop during SR | ❌ No | WCK always-on mode; no CK/WCK tristate |
| PHY Power Down | ❌ No | LPDDR6 PHY always-on |
| Deep Sleep Mode | ❌ No | Not supported |
| WCK Always-On Mode | ✅ Yes | Required for LPDDR6 |
| Thermal (CLTT) | ✅ MR4-based | TSOD not used — LPDDR6 thermal via DRAM MR4 register |

---

## Section 2: Interfaces and Protocols

| Interface | Description | NWP |
|-----------|-------------|-----|
| PActive signal | MC→DRAM: deasserted to signal SR entry request | HW present; SR entry ZBB'd |
| MR4 register | DRAM thermal status read by MC for CLTT | ✅ Active on NWP (replaces TSOD) |
| SSR_RESIDENCY PMON | Perfmon counter for SSR residency time | Not applicable — SSR ZBB'd; counter stays 0 |
| sref_sx command | MC DRAM command for SR without clock stop | HW present; never issued on NWP |

---

## Section 3: Reset, Power, and Clocking

- LPDDR6 CK/WCK clock stop: **not supported** — WCK always-on; this eliminates PHY Power Down
- Self-refresh state clears on warm reset; MC reprograms DRAM after reset exit
- PkgC6 (which would be the deepest MC idle state on server): also ZBB'd on NWP
- CLTT (MR4 polling): **active on NWP** — continues to run regardless of SSR ZBB

---

## Section 4: Programming Model

| Register / Interface | Description | NWP Status |
|---------------------|-------------|-----------|
| MC SSR enable knob | BIOS/PCode enable for SSR entry | ZBB'd — not programmed |
| DRAM MR4 | Thermal readout register; polled by MC for CLTT | ✅ Active |
| TSOD polling | DDR5 thermal polling via SMBus | ❌ Not used on LPDDR6 |
| SSR_RESIDENCY counter | PMON counter tracking SSR gating time | Not applicable (ZBB) |
| PActive de-assert | MC signal to DRAM initiating SSR entry | ZBB'd — never asserted for SR |

---

## Section 5: Operational Behavior

**DMR (reference)**: MC monitors memory access pattern; after idle threshold met, MC de-asserts
PActive → DRAM enters `sref_sx`. SSR_RESIDENCY PMON counter accumulates. CLTT monitors MR4
thermal; can exit SSR early if temperature threshold reached. MC exits SSR on any memory access.

**NWP**: SSR entry never occurs (MC PM arch decision — APD/PPD/LPM/SSR not enabled). CLTT
via MR4 is active and continues independent of SSR. WCK clock always-on; no PHY power-down.
SSR_RESIDENCY PMON counter remains at zero.

---

## Section 6: Corner Cases & Error Handling

| Scenario | DMR | NWP |
|----------|-----|-----|
| PHY Power Down during SSR | Validated (TC 22022422918) | N/A — PHY always-on, no clock stop |
| PActive deassertion timing | Validated (TC 22022422910) | N/A — SSR ZBB'd |
| SR without clock stop (`sref_sx`) | Validated (TC 22022422923) | N/A — SSR ZBB'd |
| CLTT interaction during SSR | In scope on DMR | CLTT active on NWP but SSR never entered |
| Conflicting HAS table vs MC team ZBB | N/A | Risk: HAS table says "Yes"; MC team confirmed ZBB. Treat as ZBB per TPF review. |

---

## Section 7: Security / Safety / Policy

- CLTT (MR4-based) remains active on NWP regardless of SSR ZBB — thermal safety maintained
- No security-sensitive registers in SSR path
- TSOD SMBus polling is absent on LPDDR6 — no SMBus CLTT attack surface

---

## Section 8: References

- [AIPM KB — aipm.md](../../pm_features/pm_cross_products/aipm.md) — SSR ZBB confirmation; TPF TC review 2026-06-01; all 14 MC SSR TCs ZBB'd
- [NWP HAS Overview](https://docs.intel.com/documents/custom-xeon/newport-docs/has/overview/nwp_has.html) — Feature table: SREF No Clock Stop listed (conflicting with MC team ZBB)
- [NWP HAS Comments](https://docs.intel.com/documents/custom-xeon/newport-docs/has/comments.html) — MC team comment: "SSR ZBBed on NWP"
- [LPDDR6 HAS](https://docs.intel.com/documents/iparch/mc/has/gen6/releases/lpddr6/lpddr6.html) — Self-Refresh=Yes; Clock Stop=No; PHY Power Down=No; WCK Always-On=Yes
- [NWP HAS PM Features](https://docs.intel.com/documents/custom-xeon/newport-docs/has/Overview/NWP_HAS.html) — NWP memory PM feature applicability
- [HSD 22022421244 — MIO Trunk Clock Gating Entry/Residency](https://hsdes.intel.com/appstore/article-one/#/22022421244) — Sibling TCD under AIPM TP; same ZBB pattern
