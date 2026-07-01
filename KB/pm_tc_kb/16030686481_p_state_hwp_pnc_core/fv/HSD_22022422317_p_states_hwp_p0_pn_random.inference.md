# Deep Analysis: [Solar] P-States-HWP-P0_PN_random

| Field | Value |
|-------|-------|
| **HSD ID** | 22022422317 |
| **Title** | [Solar] P-States-HWP-P0_PN_random |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | Pstate Stack |
| **Sub-Feature** | Solar tool — HWP mode random P-state sweep (P1..Pn) |
| **NWP Disposition** | **Runnable_On_N-1** |

---

### Test Case Intent

Verify **Solar tool** drives random HWP P-state requests across P0..Pn in HWP mode and system remains stable. Solar is platform-agnostic (no NWP-specific XML). Pre-condition: HWP enabled (`IA32_PM_ENABLE[0]=1`). `plc.feature.p1`.

---

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| SVOS | Running on NWP silicon |
| Solar | Installed at `/usr/bin/solar/` |
| HWP | Enabled: BIOS HWPMEnable=1 and IA32_PM_ENABLE[0]=1 |

---

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|----------------------|-------------------|
| 1 | Verify Solar installed and HWP enabled. `ls /usr/bin/solar/solar.sh; rdmsr 0x770` | Solar present; IA32_PM_ENABLE[0]=1 | Solar missing; or HWP not enabled — check BIOS |
| 2 | Run Solar HWP random P-state sweep. `/usr/bin/solar/solar.sh /hwp -gvpoints P0..Pn -r /logpath .` | Solar completes; log shows PASS for all ratio steps | Solar FAIL — check log for which ratio step failed |
| 3 | Verify no MCAs during Solar sweep. `dmesg | grep -i mce; mcelog` | No MCA events | MCA present — collect mcelog and crash dump |

---

### Pass / Fail Criteria

- **PASS**: Solar HWP sweep completes; all ratio steps PASS; no MCAs.
- **FAIL**: Solar FAIL; MCA during sweep.

---

### Health Checks

| Register / Log | Access | Pass/Fail Criteria |
|----------------|--------|-------------------|
| Solar output log | /logpath/solar_*.log | All HWP ratio steps = PASS |
| MCA events | dmesg / mcelog | No MCA during sweep |
| IA32_PM_ENABLE | MSR 0x770 | [0]=1 (HWP active) |

---

### Post-Process

Collect Solar log on failure. Check mcelog for MCA details.

---

### References

- [Core P-state HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Core_Pstates/Core_Pstate_HAS.html) — HWP P-state range; IA32_HWP_CAPABILITIES bounds
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) — NWP HWP; Solar tool SVOS operation

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test uses the **Solar** tool in HWP mode to stress P-states by issuing random HWP requests from P1 to Pn. The command:
```
/usr/bin/solar/solar.sh /hwp -hwpoints P1..Pn -r /logpath .
```

Solar has a config preset reference to `diamondrapids/pm/Solar/HWP/P0_Pn_random.xml` — this path needs to be updated to the NWP equivalent, or Solar auto-selects the correct preset.

Solar operates at SVOS level and does not use `nwp.xml` directly.

**Key Justification:**
- Solar HWP mode is platform-agnostic (SVOS-level tool)
- Only the config preset path references `diamondrapids` — may need NWP path
- `plc.feature.p2` + `PMSS_NWP_READINESS_CHECK` tags

---

## Section B: NWP-Specific Test Procedure

### Adapted Test Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Boot NWP to SVOS with HWP enabled | `ProcessorHWPMEnable = 1` BIOS |
| 2 | Verify Solar installed | `ls /usr/bin/solar/solar.sh` |
| 3 | Run Solar HWP random sweep | `/usr/bin/solar/solar.sh /hwp -hwpoints P1..Pn -r /logpath .` |
| 4 | If preset path fails, use NWP Solar config | `/cfg /usr/local/python/nwp/pm/Solar/HWP/P0_Pn_random.xml` (if exists) |
| 5 | Verify Solar PASS output | Check log at `/logpath/solar_*` |

### Solar HWP Mode Parameters
- `/hwp`: HWP mode (vs `/pstate` for legacy)
- `-hwpoints P1..Pn`: sweep from P1 guaranteed to Pn minimum, random order
- `-r`: randomize point order

### NWP Pass Criteria
- Solar exits with PASS
- HWP requests from P1 to Pn all achievable on NWP
- No MCAs or IERR during random HWP sweep
- Platform stable after test

---

## Section F: Recommendation

**Recommendation: ADOPT — Solar HWP mode command is platform-agnostic; may need NWP config path**

Required adaptations:
1. Verify Solar deployed on NWP SVOS image
2. Check if NWP Solar config exists at `/usr/local/python/nwp/pm/Solar/HWP/`; if not, Solar uses auto-discovery
3. No command change needed if Solar auto-detects platform

**Priority**: Low-Medium — no `DMR_PO`; Solar HWP stress sweep; complements hwpm_check TCs
