# Deep Analysis: PCT - NWP MADT Partition Algorithm Validation

| Field | Value |
|-------|-------|
| **HSD ID** | [16030982850](https://hsdes.intel.com/appstore/article-one/#/16030982850) |
| **Title** | PCT - NWP MADT Partition Algorithm Validation |
| **Target Program** | NWP (Newport) |
| **Feature** | SST / PCT |
| **NWP Disposition** | **Runnable_On_N-1** |

---

### Test Case Intent

Verify BIOS correctly maps NWP 96 cores (2 CBBs x 48, no SMT) into N equal partitions using MADT/APIC ID order, and that HP cores are the first 2 per partition (per HP count = 8 = 2/partition x 4 partitions). NWP MADT structure differs from DMR (NIO+2CBBs vs 2IMH+4CBBs). Also validates PCT Partition Count BIOS knob effect.

---

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| SV session | sv.socket0 accessible |
| BIOS | PCT Partition Count = 4 (default) |
| Tools | ACPI MADT enumeration or PythonSV topology read |

---

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|----------------------|-------------------|
| 1 | Boot with PCT Partition Count = 4. Enumerate 96 physical APIC IDs in MADT order. | 96 unique APIC IDs; NIO root != compute die IDs; 2 CBB compute ranges visible | Wrong count — MADT construction error or unfused cores |
| 2 | Compute expected HP cores: 96/4 = 24 per partition; HP = first 2 APIC IDs per partition (indices 0,1,24,25,48,49,72,73 in MADT order). | Algorithm produces 8 HP APIC IDs | Math error in test setup |
| 3 | Read SST_CLOS_ASSOC for all 96 cores; verify 8 HP in CLOS[0], 88 LP in CLOS[3]. | Exactly 8 HP cores match computed indices; all others LP | Mismatch — wrong APIC IDs, wrong count, or wrong offset algorithm |
| 4 | Change PCT Partition Count to 2; reboot; verify 2 partitions of 48; HP = first 2 of each = 4 HP total. | 4 HP cores for count=2; topology consistent | Still 8 HP — BIOS knob not taking effect |

---

### Pass / Fail Criteria

- **PASS**: 96 cores in 4 partitions; 8 HP match MADT-order algorithm; count=2 gives 4 HP.
- **FAIL**: Wrong HP count; wrong APIC IDs; partition count knob ineffective.

---

### References

- [https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/PCT.html](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/PCT.html) — HP core selection algorithm; MADT order; partition count
- [https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) — NWP 2-CBB MADT; CPUID 0x1F topology
- CCB HSD 14026595435 — NWP PCT 8 HP cores authoritative count

