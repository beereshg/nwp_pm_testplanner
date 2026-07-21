# Deep Analysis: [ITD] Verify CCF (VccRing) ITD

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421524 |
| **Title** | [ITD] Verify CCF (VccRing) ITD |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | SoC Thermal Management > ITD |
| **Sub-Feature** | CCF (VccRing) — CBB PCode |
| **NWP Disposition** | **Runnable_On_N-1** |

---


## Test Case Intent

Validates that VccRing (CCF) ITD compensation is correctly applied per FIVR slice. For each of the 8 CCF slices per CBB: reads min/max DTS temperature from per-slice thermal telemetry, injects temperature via DFX thermal puller override (on SVOS), reads actual ring voltage from PCode vars, calculates base voltage from 4-point ring VF curve interpolation at current ratio, computes expected ITD offset using per-slice fuse coefficients with slope-selection logic, and verifies actual voltage matches expected within 100 mV guardband.

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

CCF (VccRing) ITD is controlled by **CBB PCode**. The ring interconnect voltage is managed per FIVR domain, using local min/max DTS temperature from each domain's sensors. On DMR, there are 4 top-die CBB shadows × 2 FIVRs = 8 independent ring FIVR domains. On NWP with 2 CBBs, the ring FIVR domain count differs (2 CBBs × number of ring FIVRs per CBB). The ITD calculation algorithm is the same: per-domain ITD using `PCU_CR_DTS_TEMP_CCF` temperature sources and ring-specific fuses (`RING_ITD_CUTOFF_V/V2`, `RING_ITD_SLOPE/SLOPE2`). Primary adaptation: `dmr.xml` → `nwp.xml` and verify NWP ring FIVR count.

**Key Justification:**
- CCF ring ITD via CBB PCode is present on NWP (NWP has ring fabric)
- Same dual-slope ITD algorithm with ring-specific fuse set
- `NGA_MAIN` tag: prioritize for NGA silicon automation
- `PMSS_NWP_READINESS_CHECK` tag: explicitly evaluated for NWP

---

## Section B: NWP-Specific Test Procedure

### Pre-Conditions
- NWP silicon platform with CCF ring active
- Ring ITD fuses non-zero (from TC 22022421521)
- PythonSv access to `sv.socket0.cbb{0,1}.punit.*`

### Adapted Test Steps

| Step | Action | NWP Adaptation |
|------|--------|----------------|
| 1 | Run ITD thermal test | `python runPmx.py -x nwp.xml -p itd_thermal -tM 9 -M 3` |
| 2 | Read CCF DTS for each ring FIVR domain | NWP: 2 CBBs; `PCU_CR_DTS_TEMP_CCF` in each CBB |
| 3 | Verify per-domain ITD compensation: `itd.print_itd_info(0, 0)` shows ring domains | Verify NWP ring domain count |
| 4 | Stress ring to change temperature; verify ITD compensation updates | Same mechanism via PCode slow loop |
| 5 | Verify ring FIVR output voltage matches ITD calculation | NWP ring FIVR RC register: `RESCTRL_CR_VOLTAGE_OFFSET.OFFSET` on each ring domain |

### NWP Ring Domain Count
- DMR: 4 CBBs × 2 ring FIVRs/CBB = 8 domains
- NWP: 2 CBBs × (TBD ring FIVRs/CBB) — confirm from NWP MAS/HAS

### NWP Pass Criteria
- All NWP ring FIVR domains show non-zero ITD compensation when below cutoff temp
- PCode calculates per-domain ITD; compensation tracked in RC voltage offset
- ITD updates on slow loop (~300 ms) or faster on DTS threshold crossing

---

## Section C: NWP Delta Impact Analysis

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| CBB count | 4 | 2 | Ring FIVR domain count halved |
| Ring FIVR architecture | 4 CBBs × 2 FIVRs | 2 CBBs × N FIVRs | Confirm from NWP HAS |
| ITD fuses | `RING_ITD_CUTOFF_V/V2`, `RING_ITD_SLOPE/SLOPE2` | Same names on NWP | Direct reuse |
| DTS source | `PCU_CR_DTS_TEMP_CCF[N:0]` | Same register, per CBB | NWP has 2 CBBs; same per-FIVR DTS |

---

## Section D: Key Registers & Validation Points

### PythonSv Validation Commands (NWP)

```python
from pm.focus import itd

# Print ITD info — ring domains should appear
itd.print_itd_info(0, 0)

# Per-CBB ring DTS read
for cbb_idx in range(2):  # NWP: 2 CBBs
    cbb = getattr(sv.socket0, f'cbb{cbb_idx}')
    try:
        dts_ccf = cbb.punit.dts_temp_ccf.read()
        print(f"CBB{cbb_idx} DTS_CCF: 0x{dts_ccf:08X}")
    except Exception as e:
        print(f"CBB{cbb_idx} DTS_CCF: {e}")

# Ring FIVR RC voltage offset
for cbb_idx in range(2):
    cbb = getattr(sv.socket0, f'cbb{cbb_idx}')
    try:
        ring_offset = cbb.punit.resctrl_cr_vring_offset.read()
        print(f"CBB{cbb_idx} Ring V_OFFSET: 0x{ring_offset:08X}")
    except Exception as e:
        print(f"CBB{cbb_idx} Ring offset: {e}")
```

---

## Section E: Risk Assessment & Open Items

| # | Risk/Open Item | Severity | Notes |
|---|----------------|----------|-------|
| 1 | **NWP ring FIVR domain count** — 2 CBBs may map differently to ring FIVR domains than DMR's 4 CBBs | Low | Confirm from NWP PCode MAS |
| 2 | **Ring DTS namednodes path on NWP** — `PCU_CR_DTS_TEMP_CCF` register path may differ in NWP namednodes hierarchy | Low | Locate via `sv.socket0.cbb0.search('dts_temp_ccf', 'r')` during bring-up |

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; verify ring FIVR domain count**

CCF ring ITD is architecturally the same on NWP. Primary adaptation: XML config and confirmation of NWP ring FIVR topology.

Required adaptations:
1. `python runPmx.py -x nwp.xml -p itd_thermal -tM 9 -M 3`
2. Confirm NWP ring FIVR domain count from NWP MAS
3. Locate NWP `PCU_CR_DTS_TEMP_CCF` namednodes path

**Priority**: High — NGA_MAIN; CCF ring ITD is a primary thermal validation domain
