# TCD: ITD-CONTRACT-005 - VCCUCIEA Runtime DVFS Handshake Protocol

| Field | Value |
|-------|-------|
| **TCD ID** | [16031185178](https://hsdes.intel.com/appstore/article-one/#/16031185178) |
| **Title** | ITD-CONTRACT-005 - VCCUCIEA Runtime DVFS Handshake Protocol |
| **Status** | open |
| **Parent TPF** | [16031170066 — ITD Compensation](https://hsdes.intel.com/appstore/article-one/#/16031170066) |
| **Feature** | ITD Compensation |
| **Sub-Feature** | VCCUCIEA D2D VCCIO ITD |
| **NWP Disposition** | Needs_Adaptation (handshake protocol same as DMR; NWP register paths differ) |
| **KB last updated** | 2026-07-21 |
| **Spec refs** | D2D PM HAS §VCCIO ITD runtime; RA MAS §master-slave-voltage-workpoint-change-flow; SOC HSD 22016961651 |
| **Co-Design T2 origin** | Table 2 row 2 (new) — 2026-07-21 |

---

## Definition Block

- **Layer:** 1 (Contract)
- **Sentence:** Every runtime VCCUCIEA ITD-triggered voltage change must execute a DVFS-like handshake with the UCIe Phy (change_req asserted → Phy aligns calibration → change_ack returned) before the FIVR voltage transition is applied.
- **Gate:** ITD-CONTRACT-003 (Fabric/IO Domain Compensation — steady-state VCCUCIEA offset correct)
- **Suspect:** IMH Primecode D2D VCCIO ITD handshake implementation; Resource Adapter voltage request/ack interface
- **Setup:** ITD enabled, D2D links trained, VCCUCIEA steady-state ITD active. Phy out of reset (SB Phy operational). At least one enabled D2D stack per VCCUCIEA FIVR.
- **Check:** Inject temperature change sufficient to trigger ITD voltage update on VCCUCIEA → observe req/ack handshake signals around voltage transition.
- **Invariant:** On every runtime VCCUCIEA ITD-triggered voltage change: (1) change_req asserted BEFORE FIVR transition begins; (2) change_ack returned by Phy; (3) no FIVR voltage change applied before ack received at protocol point; (4) handshake honored in L1 state; (5) req sampled on VCCINF power / infra-clk within 8 cycles.

---

## Section 1: Architecture / Micro-architecture and Functionality

**VCCUCIEA Runtime DVFS Handshake** validates that the D2D VCCIO ITD voltage change protocol is correctly executed by IMH Primecode. VCCUCIEA (VCCIO) affects UCIe terminations and delay line — unnotified voltage changes can cause tens of mV gap vs Phy's calibration point, reducing margins and increasing error rates. The handshake allows Phy to align background calibrations before the voltage moves.

> **Architecture overview:** See [TPF 16031170066 — ITD Compensation](https://hsdes.intel.com/appstore/article-one/#/16031170066) §2 Design Details

### NWP Delta

- Same DVFS-like handshake mechanism as DMR; NWP register paths via IMH2 Resource Adapter
- Driver-receiver interface is fully async
- Phy honors handshake during L1 (sampled on VCCINF power, infra-clk)
- IMH uses existing RA capability (voltage request/ack)

### Key Interfaces

| Interface | Direction | Purpose |
|---|---|---|
| RA voltage change_req | Primecode → Phy | Notify Phy of upcoming VCCIO voltage change |
| RA voltage change_ack | Phy → Primecode | Phy confirms calibration aligned, ready for change |
| FIVR VID transition | Primecode → FIVR | Actual voltage change (gated by ack) |
| HWRS D2D enable mask | HWRS → RA | Informs RA which D2Ds to collect acks from |

---

## Section 2: Functional Requirements / Spec Refs

| FR ID | Requirement | Spec ref |
|---|---|---|
| FR1 | DVFS-like handshake with Phy before every VCCUCIEA ITD voltage change | D2D PM HAS §VCCIO ITD runtime; SOC HSD 22016961651 |
| FR2 | change_req asserted before voltage transition begins | RA MAS §master-slave-voltage-workpoint-change-flow |
| FR3 | No voltage change applied before change_ack received | D2D PM HAS — handshake protocol |
| FR4 | Phy honors handshake during L1 state | D2D PM HAS — "Phy will honor this handshake during L1" |
| FR5 | Request sampled on VCCINF power and infra-clk | SOC HSD 22016961651 |
| FR6 | Mutex between VCCUCIEA ITD and training enforced by Phy | D2D PM HAS — "Phy enforces mutex between VCCUCIEA ITD and training" |
| FR7 | Phy supports VCCUCIEA ITD independently of other side's changes | D2D PM HAS — independence clause |

---

## Section 3: Test Strategy

| Approach | Detail |
|---|---|
| Temperature injection | Inject temp change large enough to trigger VCCUCIEA ITD update (≥1°C from current) |
| Protocol observation | Monitor RA req/ack signals during voltage transition via PythonSV/namednodes |
| Timing verification | Verify ack latency in expected range (240-480 ns absent training delay) |
| L1 state coverage | Execute with D2D links in L1 to confirm handshake still honored |

---

## Section 4: Programming Model

VCCUCIEA ITD handshake uses the IMH Resource Adapter (RA) voltage request/ack flow:
1. Primecode determines new VCCUCIEA target (ITD algorithm output)
2. Primecode asserts **voltage change_req** via RA to all enabled D2D Phys
3. Each enabled Phy receives req, aligns or triggers background calibration
4. Each enabled Phy returns **change_ack**
5. RA collects all acks from enabled D2Ds (HWRS mask determines which)
6. Only after all acks collected: Primecode commands FIVR to new voltage

The RA capability already supports voltage request/ack (same mechanism as DVFS). The D2D VCCIO ITD reuses this existing path.

---

## Section 5: Pass/Fail Bar

| Bar | Measurable criterion | Spec ref |
|---|---|---|
| Req before transition | change_req observed asserted BEFORE any FIVR VID movement | RA MAS §master-slave |
| Ack before voltage | change_ack returned before FIVR voltage reaches new target | D2D PM HAS handshake |
| Ack timing | Ack latency within 240-480 ns range (8 infra-clk cycles) absent training | SOC HSD 22016961651 |
| L1 coverage | Handshake executes correctly with D2D links in L1 | D2D PM HAS — L1 clause |
| No premature transition | No VCCUCIEA voltage change observed before protocol completion | D2D PM HAS — no dead time |

---

## Section 6: Corner Cases / Coverage

| Scenario | TC ID | Env | Verdict |
|---|---|---|---|
| Basic runtime DVFS handshake on temp change | *(TC TBD)* | FV, HSLE XOS | ⚠️ GAP |
| Handshake during L1 state | *(TC TBD)* | FV | ⚠️ GAP |
| Multiple consecutive ITD changes (rapid temp drift) | *(TC TBD)* | FV | ⚠️ GAP |
| Handshake with large voltage step (15 mV post-seamless-patch) | *(TC TBD)* | FV | ⚠️ GAP |
| Mutex: ITD handshake vs training — Phy rejects if training active | *(TC TBD)* | FV, HSLE XOS | ⚠️ GAP |

---

## Section 7: Dependencies

| Dependency | Impact |
|---|---|
| TCD ITD-CONTRACT-003 (steady-state) | VCCUCIEA offset must be correct before handshake timing matters |
| TCD ITD-FUSE-001 (fuse checkout) | Fuse coefficients must be valid |
| UCIe link trained | D2D links must be up for Phy to receive handshake |
| SB Phy out of reset | Phy can honor handshake only after SB Phy reset exit |

---

## Section 8: Open Items

| Item | Status | Notes |
|---|---|---|
| HSD TCD ID | pending | Create in HSD under TPF 16031170066 |
| TC authoring | pending | Need PythonSV observation method for RA req/ack signals |
| Env feasibility: HSLE XOS | TBD-T7 | Cross-die handshake requires both IMH+CBB — confirm model coverage |
| Ack timing spec confirmation | pending | 240-480 ns from SOC HSD; confirm in RA MAS |
