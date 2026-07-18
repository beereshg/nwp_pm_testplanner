<!-- STALE: HSD 16031169298 renamed. See TCD_16031169298_pct_dq_rules.md -->
# TCD 16031169298 — PCT - DQ Rules & Negative Validation (STALE)

| Field | Value |
|-------|-------|
| **TCD ID** | [16031169298](https://hsdes.intel.com/appstore/article-one/#/16031169298) |
| **Title** | PCT - DQ Rules & Negative Validation |
| **Status** | open |
| **Owner** | bg3 |
| **Parent TPF** | [16030762939 — [NWP PM] PCT (Priority Core Turbo)](https://hsdes.intel.com/appstore/article-one/#/16030762939) |
| **KB last updated** | 2026-07-18 |

---

## Section 1: Architecture / Micro-architecture and Functionality

This TCD validates two complementary quality gates for PCT: **DQ Rules compliance** (FlexconPM framework verifying silicon bring-up correctness against spec-required register values) and **negative path validation** (invalid BIOS configurations and invalid TPMI runtime writes are rejected without state corruption). Together they ensure PCT is both spec-compliant and robust against misconfiguration.

> **Architecture overview:** See [TPF 16030762939 — PCT](https://hsdes.intel.com/appstore/article-one/#/16030762939) §2 Design Details for the full-stack PCT architecture, CLOS mechanism, ordered throttle, and frequency hierarchy.

### NWP-Specific Constants

| Parameter | Value | Relevance to this TCD |
|-----------|-------|----------------------|
| `max_partitions` | 4 (SST_TF_INFO_8.NUM_CORE_0 / MAX_LPIDS) | Boundary for partition count negative tests |
| Total cores | 96 (2 CBBs × 48) | CLOS assignment completeness check |
| `SST_TF_INFO_10.PCT_Module_Mask` | DLCP fuse; `0` on non-DLCP parts | DQ rule must verify fuse-to-register correctness |
| FlexconPM suite | SST-TF DQ assertions | Validates SST_TF_INFO_* field values against NWP spec |

### TC Coverage Map

| TC | Title | Scope | Tier |
|----|-------|-------|------|
| [22022422118](https://hsdes.intel.com/appstore/article-one/#/22022422118) | PCT - DQ Rules (FlexconPM) | FlexconPM compliance assertions on real silicon | FV |
| [16030715680](https://hsdes.intel.com/appstore/article-one/#/16030715680) | [PSS] PCT - BIOS Negative Validation | Invalid BIOS config on VP (safe — no silicon risk) | PSS (VP) |
| [16030715682](https://hsdes.intel.com/appstore/article-one/#/16030715682) | [PSS] PCT - DQ Rules (FlexconPM) | DQ assertions in PSS environment (model-level) | PSS |
| [16030768621](https://hsdes.intel.com/appstore/article-one/#/16030768621) | PCT - TPMI runtime negative validation | Invalid runtime TPMI writes; ERROR_TYPE reporting | PSS / FV |

---

## Section 2: Interfaces and Protocols

| Register / Interface | Scope | Role in this TCD |
|---------------------|-------|-----------------|
| `SST_TF_INFO_0..10` (TPMI, RO) | DQ Rules | Register field values must match FlexconPM DQ assertions |
| `SST_CP_STATUS.ERROR_TYPE` | Negative validation | Must be set to `not_supported` or `conflict` on invalid control write |
| `SST_CP_CONTROL.sst_cp_enable` | Negative validation (runtime) | Invalid enable + conflicting feature → ERROR_TYPE != 0 |
| BIOS knob: PCT Partition Count | Negative validation | Count > max_partitions must be rejected/clamped by BIOS |
| BIOS knob: PCT HP Module Select | Negative validation | Conflicting HP module positions must be rejected |
| `SST_CP_STATUS.LAST_HANDSHAKE` | Negative validation | Must match HANDSHAKE after any control write (even rejected) |

---

## Section 3: Reset, Power, and Clocking

- **DQ Rules:** Executed after PrimeCode Phase 5 (SST_TF_INFO_* registers valid and immutable post-reset) and after BIOS CPL3 PCT configuration. Tests run at steady-state OS/FV level.
- **Negative BIOS:** Tested at BIOS CPL3 phase (before OS boot) on VP where silicon cannot be damaged.
- **Negative TPMI Runtime:** Tested at OS/FV runtime via PythonSV or SST tool writes.
- SST_TF_INFO_* registers are **read-only after Phase 5** — DQ check reads, never writes.

---

## Section 4: Programming Model

**DQ Rules (FlexconPM):**
FlexconPM checks PCT compliance by reading SST_TF_INFO_* TPMI registers and asserting specific field values match the NWP spec. Each assertion maps to a DQ requirement:
- `SST_TF_INFO_0.LP_CLIP_RATIO_*`: LP clip ratios within spec bounds
- `SST_TF_INFO_2.RATIO_*`: HP TRL ratios correctly loaded from fuses
- `SST_TF_INFO_8.NUM_CORE_0`: max_partitions derivation correct
- `SST_TF_INFO_10.PCT_Module_Mask`: DLCP mask reflects fuse (0 on non-DLCP parts)

**BIOS Negative Validation (PSS VP only):**
BIOS is given out-of-range or conflicting PCT knob values; expected behavior: BIOS rejects/clamps, SST_CLOS_* reflects safe fallback, feature disabled rather than corrupted.

**TPMI Runtime Negative Validation:**
PythonSV/tool writes invalid values to `SST_CP_CONTROL` (unsupported enable combinations). Expected: `SST_CP_STATUS.ERROR_TYPE = not_supported or conflict`; prior state preserved; HANDSHAKE/LAST_HANDSHAKE match confirmed after write.

---

## Section 5: Operational Behavior

### Pass/Fail Bar

| Scenario | Pass Criterion | TC |
|----------|----------------|-----|
| FlexconPM DQ assertions (FV) | All required PCT FlexconPM assertions **PASS** on silicon; zero DQ rule violations; SST_TF_INFO_* register values match spec-expected ranges | TC 22022422118 |
| FlexconPM DQ assertions (PSS) | All PCT DQ assertions pass in PSS model; any model-gap assertions noted as known | TC 16030715682 |
| BIOS negative validation (PSS VP) | Invalid partition count / conflicting HP positions → BIOS rejects; PCT remains disabled or falls to safe default; no SST_CLOS_* corruption | TC 16030715680 |
| TPMI runtime negative (PSS/FV) | Invalid SST_CP_CONTROL write → `SST_CP_STATUS.ERROR_TYPE != 0`; prior CLOS state unchanged; HANDSHAKE == LAST_HANDSHAKE | TC 16030768621 |

**Failure mode:** Any FlexconPM assertion failure = DQ bug (silicon does not meet spec). Any state corruption after negative injection = critical reliability bug.

---

## Section 6: Corner Cases & Error Handling

| Corner Case | Description | Current Coverage | Action Required |
|-------------|-------------|-----------------|----------------|
| **Partition count = max_partitions + 1** | BIOS overflow; must not program SST_CLOS_* with invalid count | ✅ TC 16030715680 (PSS VP) | No action — VP tests boundary |
| **Conflicting HP module positions** | Two partitions claim same core as HP | ✅ TC 16030715680 (PSS VP) | No action |
| **PCT + SST-BF conflict** | PCT enable with SST-BF present → ERROR_TYPE = conflict | ✅ TC 16030768621 | Verify PSS has SST-BF model support |
| **Unsupported PCT enable (fuse=0)** | SST_CP_CONTROL.sst_cp_enable on non-PCT-capable SKU → ERROR_TYPE = not_supported | ✅ TC 16030768621 | No action |
| **SST_TF_INFO_10 write attempt** | Should be RO post Phase 5; write must not change value | ⚠️ TC 16030715680 mentions but not primary focus | Add write-protect check as pass criterion in TC 16030715680 |
| **DQ model gap (PSS vs silicon)** | Simics model may not enforce all DQ values at RTL precision | ⚠️ TC 16030715682 | Note model gaps; FV TC 22022422118 is ground truth |

---

## Section 7: Security / Safety / Policy

- FlexconPM DQ rules enforce silicon correctness at bring-up — a DQ failure indicates the silicon does not meet spec.
- Negative BIOS validation must run on VP only (PSS) — running invalid BIOS configurations on real silicon risks corruption.
- Invalid TPMI writes must not create a covert channel: ERROR_TYPE must be visible to OS; prior state must be preserved.
- `SST_TF_INFO_*` are read-only post Phase 5 — write-protect is a security property.

---

## Section 8: References

- [PCT HAS](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/PCT.html) — DQ requirements, negative path behavior
- [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) — SST_CP_STATUS.ERROR_TYPE, HANDSHAKE semantics, DQ assertions
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) — NWP PCT scope, FlexconPM reference
- [TPF 16030762939 — PCT](https://hsdes.intel.com/appstore/article-one/#/16030762939) — Feature architecture
- Co-Design T1 findings: related gaps tracked in TCD 16031169308 (PCT - Negative / Boundary Validation) for scenarios beyond current TC scope
