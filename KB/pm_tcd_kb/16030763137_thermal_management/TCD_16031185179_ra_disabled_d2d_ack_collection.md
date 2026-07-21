# TCD: ITD-SCENARIO-002 - RA Disabled-D2D Ack Collection

| Field | Value |
|-------|-------|
| **TCD ID** | [16031185179](https://hsdes.intel.com/appstore/article-one/#/16031185179) |
| **Title** | ITD-SCENARIO-002 - RA Disabled-D2D Ack Collection |
| **Status** | open |
| **Parent TPF** | [16031170066 — ITD Compensation](https://hsdes.intel.com/appstore/article-one/#/16031170066) |
| **Feature** | ITD Compensation |
| **Sub-Feature** | VCCUCIEA D2D VCCIO ITD |
| **NWP Disposition** | Needs_Adaptation (RA masking mechanism same as DMR; topology config differs) |
| **KB last updated** | 2026-07-21 |
| **Spec refs** | RA MAS §master-slave-voltage-workpoint-change-flow; SOC HSD 22016961651; D2D PM HAS |
| **Co-Design T2 origin** | Table 2 row 3 (new) — 2026-07-21 |

---

## Definition Block

- **Layer:** 3 (Scenario)
- **Sentence:** When D2D stacks are disabled, the Resource Adapter completes VCCUCIEA ITD handshakes without waiting for ack from disabled D2D Phys, while still collecting ack from all enabled D2Ds.
- **Gate:** ITD-CONTRACT-005 (VCCUCIEA Runtime DVFS Handshake Protocol — basic handshake works with all D2Ds enabled)
- **Suspect:** HWRS → RA enable mask programming; RA ack collection logic for partial-D2D topology
- **Setup:** ITD enabled, at least one D2D disabled via HWRS (reduced topology). Remaining D2Ds trained and active.
- **Check:** Trigger VCCUCIEA ITD voltage change → verify RA does not hang waiting for disabled D2D; verify enabled D2Ds still acked.
- **Invariant:** VCCUCIEA ITD request completes within expected latency (no timeout / no hang) with disabled D2D present; enabled D2Ds receive req and return ack; disabled D2D Phy is NOT queried (no stale req assertion to powered-down Phy).

---

## Section 1: Architecture / Micro-architecture and Functionality

**RA Disabled-D2D Ack Collection** validates that the VCCUCIEA ITD handshake correctly handles partial-D2D topologies. When some D2D stacks are disabled (via HWRS reset widget), the Resource Adapter must skip ack collection from those Phys. A bug here manifests as a hang (RA waiting forever for ack from a powered-down Phy) or incorrect masking (sending req to a disabled Phy).

> **Architecture overview:** See [TPF 16031170066 — ITD Compensation](https://hsdes.intel.com/appstore/article-one/#/16031170066) §2 Design Details

### NWP Delta

- Same RA masking mechanism as DMR; NWP has different D2D stack topology (IMH-CBB mapping)
- HWRS informs RA to skip responses from Phy placed in disabled D2Ds
- VCCUCIE FIVR-to-D2D mapping: NW=IMH-CBB[1], NE=IMH-CBB[0], SW=IMH-CBB[3]/[5], SE=IMH-CBB[2]/[4]

### VCCUCIEA FIVR → D2D Stack Mapping

| VCCUCIE FIVR | Connected D2D Stacks |
|---|---|
| VCCUCIE_NW | IMH-CBB[1] |
| VCCUCIE_NE | IMH-CBB[0] |
| VCCUCIE_SW | IMH-CBB[3], IMH-CBB[5] |
| VCCUCIE_SE | IMH-CBB[2], IMH-CBB[4] |

---

## Section 2: Functional Requirements / Spec Refs

| FR ID | Requirement | Spec ref |
|---|---|---|
| FR1 | RA collects acks only from enabled D2Ds | SOC HSD 22016961651; RA MAS |
| FR2 | HWRS informs RA to skip responses from disabled D2D Phys | D2D PM HAS — reset widget interaction |
| FR3 | Disabled D2D/FIVR path is skipped entirely (no req to disabled Phy) | SOC HSD 22016961651 |
| FR4 | ITD request completes without timeout when disabled D2Ds present | RA MAS — completion semantics |
| FR5 | Shared FIVR (SW/SE driving 2 stacks): if one stack disabled, only enabled stack acked | D2D PM HAS — shared FIVR topology |

---

## Section 3: Test Strategy

| Approach | Detail |
|---|---|
| Topology configuration | Configure platform with at least one D2D stack disabled via HWRS/fuse |
| Trigger ITD | Inject temperature change to trigger VCCUCIEA voltage update |
| Observe RA behavior | Verify RA completes without hang; verify no req sent to disabled Phy |
| Shared FIVR case | Test with one of two stacks disabled on SW or SE FIVR |

---

## Section 4: Programming Model

The HWRS reset widget programs the RA enable mask during boot:
1. HWRS determines which D2D stacks are disabled (from fuse / config)
2. HWRS programs RA to skip responses from disabled D2D Phys
3. During runtime ITD: RA broadcasts voltage change_req only to enabled Phys
4. RA waits for ack only from enabled Phys (disabled Phys not in collection set)
5. Once all enabled acks received → FIVR voltage change proceeds

Critical corner: Shared FIVR (VCCUCIE_SW drives CBB[3]+CBB[5]). If CBB[5] disabled:
- RA sends req to CBB[3] Phy only
- RA collects ack from CBB[3] only
- FIVR change applies to shared rail (both stacks see voltage, but disabled one doesn't care)

---

## Section 5: Pass/Fail Bar

| Bar | Measurable criterion | Spec ref |
|---|---|---|
| No hang with disabled D2D | ITD request completes within normal latency (no timeout) | RA MAS — completion |
| Enabled D2D acked | All enabled D2D Phys receive req and return ack | RA MAS §master-slave |
| Disabled D2D not queried | No req assertion observed to disabled D2D Phy | SOC HSD 22016961651 |
| Shared FIVR partial disable | With one of two stacks disabled on shared FIVR, ITD completes correctly | D2D PM HAS topology |

---

## Section 6: Corner Cases / Coverage

| Scenario | TC ID | Env | Verdict |
|---|---|---|---|
| Single D2D disabled, remaining enabled — ITD completes | *(TC TBD)* | FV | ⚠️ GAP |
| All D2Ds on one FIVR disabled — ITD skips entire FIVR | *(TC TBD)* | FV | ⚠️ GAP |
| Shared FIVR: one of two stacks disabled | *(TC TBD)* | FV | ⚠️ GAP |
| HWRS mask programmed at boot — verify mask persists through warm reset | *(TC TBD)* | FV | ⚠️ GAP |
| Race: D2D disable during active ITD handshake | *(TC TBD)* | FV, HSLE | ⚠️ GAP |

---

## Section 7: Dependencies

| Dependency | Impact |
|---|---|
| TCD ITD-CONTRACT-005 (DVFS handshake) | Basic handshake must work before testing partial-topology masking |
| Platform with disabled D2D | Requires reduced-topology config or fuse-based disable |
| HWRS programming | HWRS must correctly program RA mask during boot |

---

## Section 8: Open Items

| Item | Status | Notes |
|---|---|---|
| HSD TCD ID | pending | Create in HSD under TPF 16031170066 |
| TC authoring | pending | Need platform config with disabled D2D stacks |
| Shared FIVR behavior | confirm | Verify FIVR voltage still changes even with one stack disabled |
| Env feasibility | FV-only likely | Disabled D2D requires real topology or advanced model support |
