# CBB CCF Message to Punit

| Field | Value |
|-------|-------|
| **HSD ID** | [22022422896](https://hsdes.intel.com/appstore/article-one/#/22022422896) |
| **Title** | CBB CCF Message to Punit |
| **Status** | open |
| **Owner** | bg3 |
| **Val Environment** | silicon, virtual_platform |
| **Feature** | Ring Scalability / Distress Message / PUnit Grade Indication |
| **Parent TCD** | [22022421199 -- CBB CCF Message To Punit](https://hsdes.intel.com/appstore/article-one/#/22022421199) |
| **KB last updated** | 2026-07-10 |

---

## Test Case Intent

Verify the CCF PMA distress message delivery mechanism to PUnit — specifically that the message carries a **4-bit grade** (0-15) via CR_WR opcode to PUNIT_CR_RING_DISTRESS_STATUS (address 0x1C8), rather than the legacy 3-state {No, Low, High} distress. The scaling block converts logistic regression output to a 4-bit grade using 7 configurable thresholds (th0..th6 → Grade0..7[3:0]). This TC verifies the full-resolution grade message is received and readable by PCode.

**⚠️ NOTE — Differentiation from related TCs:**
- **TC 22022422851** (CBB CCF GV PEGA Injection, TCD 22022421168, Active States TPF): Validates PEGA-driven **CCF GV state machine** output. Completely different sideband path — unrelated to ring_distress_status.
- **TC 22022422905** (PCODE Algorithm, TCD 22022421197): Validates PCode **algorithm PROCESSING** of the distress grade (`ia_ring_factor`, `ia_promote_ring` workpoint). THIS TC validates the **DELIVERY** of the grade to PUNIT *before* any algorithm runs.
- **TC 22022422894/22022422895**: Validate the upstream telemetry inputs (CBO/SBO counters → grade computation), not the delivery mechanism.

**Differentiator from sibling TCs:**
- TC 22022422894 — IA distress *inputs* (CBO counters → grade computation)
- TC 22022422895 — Snoop distress *inputs* (SBO counters → snoop grade)
- **This TC** — the *message delivery* mechanism (CCF PMA → PMSB CR_WR → PUnit register)

**Message format (PMSB CR_WR to 0x1C8):**
- Data[3:0] = Main Grade[3:0] (4-bit, 0-15 IA stress level)
- Data[4] = Always 0 (PCode first-access detection)
- Data[11:8] = Snoop Grade[3:0] (4-bit, 0-15 snoop stress level)
- Data[12] = Always 0
- Data[31] = Group (0=Main, 1=Snoop)

**Verification path:** `cbb.base.punit_regs.punit_pmsb.pmsb_pcu.ring_distress_status` — this register holds the last received grade message.

**Flow:**

- Verify 4-bit grade is being received (not legacy 3-state): `ia_distress[3:0]` covers full 0-15 range under varying load
- Verify message delivery: `ring_distress_status` updates periodically as CCF PMA sends new grade messages
- Verify both Main (Group=0) and Snoop (Group=1) messages reach PUnit
- Verify validity flags are clear (`ia_distress_invalid=0`, `snoop_level_invalid=0`)

---

## Pre-Conditions

| Pre-Condition | Requirement |
|---|---|
| System booted to OS | BIOS CPL4 complete; ring scalability running |
| Ring scalability enabled | MSR 0x1FC bit[25] `disable_ring_ee=0` |
| `ring_distress_status` accessible | `cbb.base.punit_regs.punit_pmsb.pmsb_pcu.ring_distress_status` readable |
| System under varying load | Idle + light workload to generate non-trivial grade values |

---

## Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|--------------------|
| 1 | Verify ring scalability enabled: `cbb_ccf_distress_to_punit_test(skt, 'cbbs')` — checks MSR 0x1FC bit[25] per core | `disable_ring_ee=0` on all cores — message pathway active | Any core shows bit=1 — messages not being generated |
| 2 | Read `ring_distress_status` repeatedly (10 samples, 1s apart): check `ia_distress_invalid=0` and `snoop_level_invalid=0` | Both validity flags = 0 consistently — message format correct | Any invalid flag set — CCF PMA not initializing message correctly |
| 3 | Sample `ia_distress[3:0]` across idle and light workload. Verify at least 2 distinct values observed | `ia_distress` takes multiple values across samples — full 4-bit grade functional (not stuck at one level) | Always same value — grade not updating or stuck at zero |
| 4 | Sample `snoop_level[11:8]` across same window | `snoop_level` accessible and non-constant | Always 0 or invalid — snoop message not reaching PUnit |
| 5 | Read `ring_distress_status.group` field across multiple samples | Group field toggles between 0 (Main) and 1 (Snoop) — both message types sent periodically | Only one group value — one message type not being sent |

---

## Pass / Fail Criteria

**PASS:** `ring_distress_status` receives valid 4-bit grade messages (0-15 range, not stuck); both `ia_distress_invalid=0` and `snoop_level_invalid=0`; grade value varies across samples under varying load; both Group=0 and Group=1 messages observed; MSR 0x1FC `disable_ring_ee=0`.

**FAIL:** `ring_distress_status` always reads 0 or shows invalid flags; `ia_distress` stuck at single value regardless of load; only one group type observed; ring scalability disabled.

---

## Post-Process

Save: 10+ samples of `ring_distress_status` (ia_distress, snoop_level, both invalid flags, group) per CBB across idle and workload, MSR 0x1FC value per core.

---

## References

- [CBB CCF Power Management HAS (Ring Scalability)](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/IP%20Integration/CCF/CBB_CCF_PM.html#cbb-ring-frequency-scalability)
- [CBB CCF Power Management HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/IP%20Integration/CCF/CBB_CCF_PM.html#ccf-gv)
- [CBB Telemetry Aggregator](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/CBB_Telemetry/TelemetryAggregator_CBB.html#punit-telemetry-space-details)
- [CBB CCF Power Management HAS index](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/index.html)
- [pCode Home](https://wiki.ith.intel.com/display/ServerPcode/Server+Pcode+Home)
- [Related TC 22022422894 - IA Distress](https://hsdes.intel.com/appstore/article-one/#/22022422894)
- [Related TC 22022422895 - Snoop Distress](https://hsdes.intel.com/appstore/article-one/#/22022422895)
