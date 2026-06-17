# Deep Analysis: AshTree PRT Silicon

| Field | Value |
|-------|-------|
| **HSD ID** | 14027619766 |
| **Title** | AshTree PRT_silicon |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | (blank) |
| **Sub-Feature** | AshTree PRT — TSC monotonicity during package C-state (12 hrs) |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

AshTree PRT verifies TSC monotonicity (always-increasing) via MSR 0x10 during package C-state residency for 12+ hours. PkgC2/PkgC3 are functional on NWP.

**NWP adaptation**: Use PkgC2 or PkgC3 (functional) — NOT PkgC6 (ZBB on NWP). Test run for `PkgCstate` where target must be one of the non-ZBB package C-states.

---

## Section B: NWP-Specific Test Procedure

### NWP Commands
```bash
# PTAT monitoring
/usr/local/ptat/ptat -mon -filter 0x0f -id TSC

# TSC monotonicity script
python readtsc3_base.py
```

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Enable MonitorMWait | `msr -w 22 -o e2 -a` |
| 2 | Enable Package C-state (PkgC2/PkgC3) | **Not PkgC6 (ZBB)** |
| 3 | Run TSC monotonicity script for 12+ hours | `python readtsc3_base.py` |
| 4 | Monitor PTAT for TSC | `/usr/local/ptat/ptat -mon -filter 0x0f -id TSC` |
| 5 | Verify TSC is always increasing | No backwards TSC values |

### NWP PkgC-state Selection
```bash
# Set PkgC2/PkgC3 target (avoid PkgC6 which is ZBB)
msr -w 22 -o e2 -a  # Enable MonitorMWait
# BIOS knob: PackageC = C3 (or C2)
```

### Pass Criteria
- TSC monotonic for 12+ hours during PkgC2/C3 transitions
- No OS error from `readtsc3_base.py`
- PTAT TSC monitoring shows no backwards timestamps

---

## Section F: Recommendation

**Recommendation: ADOPT — Use PkgC2/PkgC3 (NOT PkgC6 which is ZBB on NWP); TSC monotonicity test architecture same; 12-hour runtime**

**Priority**: High — Long-run stability test; TSC monotonicity failure is a critical defect for OS and VM correctness
