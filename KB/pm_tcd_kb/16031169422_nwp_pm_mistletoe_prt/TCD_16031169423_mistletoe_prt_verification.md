# TCD: Mistletoe PRT - Platform Runtime Test Verification

| Field | Value |
|-------|-------|
| **TCD ID** | [16031169423](https://hsdes.intel.com/appstore/article-one/#/16031169423) |
| **Title** | Mistletoe PRT - Platform Runtime Test Verification |
| **Status** | open |
| **Owner** | bg3 |
| **Parent TPF** | [16031169422 -- NWP PM Mistletoe PRT](https://hsdes.intel.com/appstore/article-one/#/16031169422) |
| **Parent TP** | [16030765561 -- NWP PM Interfaces](https://hsdes.intel.com/appstore/article-one/#/16030765561) |
| **KB last updated** | 2026-07-20 |
| **Feature** | PM Interfaces -- Mistletoe PRT (Platform Runtime Test) |
| **Created from** | Co-Design T2 audit -- moved from Socket RAPL TCD 22022420821 (cross-feature scope) |

## Section 1: Architecture / Micro-architecture and Functionality

**Mistletoe PRT (Platform Runtime Test)** is an OOB (Out-of-Band) platform runtime validation mechanism that verifies the end-to-end BMC/NM access path through PECI-over-MCTP and OOBMSM to PM firmware (PrimeCode). PRT is a platform-level feature that exercises the OOB communication path independent of any specific PM feature (RAPL, thermal, C-state, etc.).

This TCD validates that the PRT path completes successfully and that the OOB access infrastructure is functional. Feature-specific OOB register consistency (e.g., Socket RAPL OOB reads matching inband TPMI) is validated by feature-specific TCDs (e.g., TCD 22022420821 TC 22022422040).

### Functional Scope

- PRT request from BMC/NM reaches PrimeCode via PECI-over-MCTP / OOBMSM
- PrimeCode processes PRT and returns completion status
- OOB access path is functional end-to-end
- PRT completes without error or timeout

### NWP Applicability

PRT is supported on NWP. OOB access uses the NIO die OOBMSM path. NWP-specific: single NIO root (vs DMR dual-IMH).

### TC Coverage Map

| TC | Scope | Key Validation | Status |
|----|-------|----------------|--------|
| [16030715734 -- [PSS] Verify Mistletoe PRT](https://hsdes.intel.com/appstore/article-one/#/16030715734) | PRT path verification (PSS) | PRT request reaches PrimeCode; PRT completes; OOB path functional | rejected |
| [22022421995 -- RAPL X Security (Mistletoe PRT) - Verification of Energy Fuzzing](https://hsdes.intel.com/appstore/article-one/#/22022421995) | PRT security -- energy fuzzing verification | Validates PRT path under energy fuzzing security scenario | open |

### Coverage Gaps

| Gap | Recommended TC | Priority |
|-----|---------------|----------|
| FV PRT verification (post-silicon, non-security) | *(TC TBD)* -- Basic PRT on real silicon via BMC (non-fuzzing) | H |
| PRT under active PM feature load (RAPL throttling, C-state transitions) | *(TC TBD)* -- PRT while PM features actively changing state | L |

---

## Section 2: Interfaces and Protocols

| Interface | Path | Description |
|-----------|------|-------------|
| PECI-over-MCTP | BMC -> OOBMSM -> PrimeCode | OOB communication path for PRT |
| OOBMSM | NIO die | Primary-to-Sideband translation via LTM |

---

## Section 3: Reset, Power, and Clocking

- OOB access path reinitializes after reset
- PRT should complete successfully after warm reset recovery

---

## Section 4: Programming Model

1. BMC/NM issues PRT request via PECI-over-MCTP
2. OOBMSM translates and routes to PrimeCode on NIO
3. PrimeCode processes PRT
4. Completion status returned to BMC
5. Validate: PRT completes without error or timeout

---

## Section 5: Operational Behavior

> **WHAT:** Mistletoe PRT platform runtime test path completes successfully via OOB.

**Pass/fail bar:**
- PRT request reaches PrimeCode via PECI-over-MCTP / OOBMSM path
- PRT processing completes without error or timeout
- OOB access path is functional end-to-end

---

## Section 6: Corner Cases & Error Handling

| Scenario | Expected Behavior |
|----------|------------------|
| PRT during warm reset | PRT fails gracefully; retries after reset recovery |
| PRT with OOBMSM path busy | PRT queued or retried per platform policy |
| Multiple concurrent PRT requests | Serialized by OOBMSM; no corruption |

---

## Section 7: Security / Safety / Policy

- OOB access is authenticated via BMC/platform security policy
- PRT does not modify any PM state -- read-only verification path

---

## Section 8: References

- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/PM/NWP_IMH_SOC_PM_MAS.html) -- NWP OOB access path
- DMR IMH PM HAS Section 8.2 -- OOBMSM, PECI-over-MCTP
- Co-Design T2 audit 2026-07-18 -- split from Socket RAPL TCD 22022420821
