# TCD: PSS Negative test content

| Field | Value |
|-------|-------|
| **TCD ID** | [16031172984](https://hsdes.intel.com/appstore/article-one/#/16031172984) |
| **Title** | PSS Negative test content |
| **Status** | open |
| **Owner** | thangama |
| **Parent TPF** | [22022562325](https://hsdes.intel.com/appstore/article-one/#/22022562325) |
| **Parent TP** | [16030765631 - PM Cross Product](https://hsdes.intel.com/appstore/article-one/#/16030765631) |
| **KB last updated** | 2026-07-20 |
| **Feature** | Power / PM Cross-product - Pre-Si negative validation and ZBB feature checks |

## Section 1: Architecture / Micro-architecture and Functionality

Contains pre-silicon (PSS) negative test cases that validate features fused off or ZBB on NWP behave correctly when disabled, and sideband protocol robustness under abnormal conditions. These tests run in VP (Simics) or HSLE environments to confirm expected negative behavior before silicon.

> **Architecture overview:** See [TPF 22022562325](https://hsdes.intel.com/appstore/article-one/#/22022562325) Section 2

### NWP-Specific Deltas

- Memory PM ZBB checks validate features intentionally disabled on NWP
- Sideband harasser PSS validates firmware harasser logic in simulation

### TC Coverage Map

| TC | Scope | Environment |
|----|-------|-------------|
| [16030715653](https://hsdes.intel.com/appstore/article-one/#/16030715653) | [PSS] Memory PM ZBB Negative Checks | PSS (VP/HSLE) |
| [16030715718](https://hsdes.intel.com/appstore/article-one/#/16030715718) | [PSS] Sideband Harasser | PSS (VP/HSLE) |

---

## Section 2: Interfaces and Protocols

| Interface | Register / Path | Role |
|-----------|----------------|------|
| Fuse registers | ZBB feature fuses | Verify feature disabled |
| PCode mailbox | SB harasser config | Validate in simulation |
| GPSB/PMSB | Sideband fabric | Harasser traffic generation |

---

## Section 3: Reset, Power, and Clocking

- ZBB negative checks verify disabled features do not activate post-reset
- Harasser PSS validates firmware logic without real sideband hardware

---

## Section 4: Programming Model

Memory PM ZBB checks: read feature control registers after boot and verify ZBB features (PkgC6, UFS, DRAM RAPL as applicable) are correctly fused off and produce no effect when triggered. SB harasser PSS: exercise firmware harasser path in simulation to validate message generation, rate control, and clean termination.

---

## Section 5: Operational Behavior

### Pass/Fail Bar

| Criterion | Measurable Threshold | Spec Basis |
|-----------|---------------------|-----------|
| ZBB features disabled | Feature control registers show disabled state | Fuse/ZBB spec |
| No activation on trigger | Triggering ZBB feature produces no effect | Architecture: fused-off behavior |
| Harasser terminates cleanly | SB harasser start/stop cycle without hang | Firmware spec |
| No MCA from disabled path | Zero MCAs when exercising fused-off path | Architecture invariant |

---

## Section 6: Corner Cases & Error Handling

| Corner Case | Description | Current Coverage | Action Required |
|-------------|-------------|-----------------|----------------|
| Attempt to enable ZBB feature | Write to disabled feature register | Memory PM ZBB TC | No action |
| Harasser at max rate in VP | Simulation timing differences | Harasser PSS TC | No action |

---

## Section 7: Security / Safety / Policy

- ZBB features must not be activatable even with privileged access
- Confirms security of fuse-disabled paths

---

## Section 8: References

- [NWP IMH SoC PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) - ZBB features, fuse map
- [DMR SoC PM HAS](https://docs.intel.com/documents/pm_doc/src/server/dmr/soc_pm_has/dmr_soc_pm_has.html) - sideband harasser
