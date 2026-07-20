# TCD: PMX Security cross product

| Field | Value |
|-------|-------|
| **TCD ID** | [16031172977](https://hsdes.intel.com/appstore/article-one/#/16031172977) |
| **Title** | PMX Security cross product |
| **Status** | open |
| **Owner** | thangama |
| **Parent TPF** | [22022562325](https://hsdes.intel.com/appstore/article-one/#/22022562325) |
| **Parent TP** | [16030765631 - PM Cross Product](https://hsdes.intel.com/appstore/article-one/#/16030765631) |
| **KB last updated** | 2026-07-20 |
| **Feature** | Power / PM Cross-product - PM features x Security (energy filtering/fuzzing) |

## Section 1: Architecture / Micro-architecture and Functionality

Validates that PM features remain correct and enforceable when security features (energy filtering/fuzzing via MSR 0xBC) are concurrently active. Each TC exercises a specific PM feature under security cross-product conditions to verify no interference with PM enforcement.

> **Architecture overview:** See [TPF 22022562325](https://hsdes.intel.com/appstore/article-one/#/22022562325) Section 2

### NWP-Specific Deltas

- PkgC6 ZBB on NWP - TC 22022421695 (Security x PC6) is **not applicable**
- DRAM RAPL fused off on NWP - TC 22022421691 (Security x DRAM RAPL) **may not apply**
- Platform RAPL / Psys scope limited on single-NIO NWP topology
- Socket RAPL and RACL remain in scope

### TC Coverage Map

| TC | Scope | NWP Applicability |
|----|-------|-------------------|
| [22022421691](https://hsdes.intel.com/appstore/article-one/#/22022421691) | pmx Security x DRAM RAPL | **Review** - DRAM RAPL may be fused off |
| [22022421695](https://hsdes.intel.com/appstore/article-one/#/22022421695) | pmx Security x PC6 | **ZBB / not applicable** - PkgC6 not supported |
| [22022421697](https://hsdes.intel.com/appstore/article-one/#/22022421697) | pmx Security x Platform RAPL | In scope (reduced - single NIO) |
| [22022421698](https://hsdes.intel.com/appstore/article-one/#/22022421698) | pmx Security x RACL | In scope |
| [22022421700](https://hsdes.intel.com/appstore/article-one/#/22022421700) | pmx Security x Socket RAPL | In scope |

---

## Section 2: Interfaces and Protocols

| Interface | Register / Path | Role |
|-----------|----------------|------|
| MSR 0xBC | IA32_MISC_PACKAGE_CTLS.bit0 | Energy filtering toggle |
| TPMI | ENERGY_STATUS | Fuzzed by security feature |
| TPMI | PL1_CONTROL / PL2_CONTROL | RAPL limits (must remain enforced) |
| TPMI | RACL control registers | RACL limits (must remain enforced) |

---

## Section 3: Reset, Power, and Clocking

- Security energy filtering enabled via MSR 0xBC.bit0=1
- PM features must remain correctly enforced regardless of filtering state
- Reset clears energy filtering; PM features reinitialize independently

---

## Section 4: Programming Model

Energy fuzzing (MSR 0xBC) modifies energy telemetry reporting without affecting actual power consumption or PM enforcement. The validation confirms that energy filtering is orthogonal to PM feature operation - RAPL/RACL limits continue to be enforced correctly with fuzzed telemetry.

---

## Section 5: Operational Behavior

### Pass/Fail Bar

| Criterion | Measurable Threshold | Spec Basis |
|-----------|---------------------|-----------|
| PM enforcement persists | RAPL/RACL limits correctly applied with fuzzing active | PM x Security architecture |
| No MCA | Zero MCAs | Architecture invariant |
| No hang | Test completes within timeout | Architecture invariant |
| Energy reporting modified | ENERGY_STATUS reflects fuzzing | Security feature spec |

---

## Section 6: Corner Cases & Error Handling

| Corner Case | Description | Current Coverage | Action Required |
|-------------|-------------|-----------------|----------------|
| PC6 x Security on NWP | PkgC6 ZBB - not applicable | TC 22022421695 exists but N/A | **Reject or mark ZBB** |
| DRAM RAPL x Security | DRAM RAPL may be fused off | TC 22022421691 exists | **Verify fuse state** |
| Fuzzing + active RAPL throttle | Fuzzed telemetry during PID control | Covered by Socket RAPL TC | No action |

---

## Section 7: Security / Safety / Policy

- Energy filtering is a security feature to prevent power side-channel attacks
- MSR 0xBC requires CPL0 access; BIOS may lock
- Testing validates security feature does not degrade PM functionality

---

## Section 8: References

- [NWP IMH SoC PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html)
- [Intel RAPL HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/RAPL/RAPL.html) - energy filtering interaction
