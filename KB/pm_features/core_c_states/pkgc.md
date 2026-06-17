# Core C-States > PKGC

> **Status**: Enriched — HW/FW/OS touchpoints + KPI & Timing added (2026-05-28)
> **Parent**: [Core C-States](core_c_states_main.md)

## Baseline (DMR)

Package C-state (PCx) is the deepest idle level — it requires **all modules** (and all other package-level components) to be idle. `PCx = min(M1, M2, …Mn)` where Mx is the module C-state.

## HW Touchpoints

| IP Block | Die | Role | Key Signals / Wires | HAS Reference |
|----------|-----|------|---------------------|---------------|
| Q-channels (CFC_CLK / CFC_PWR / INF) | CBB | All three must be deasserted by ALL modules before PkgC entry is possible; aggregated by PUnit across modules | Q_CFC_CLK.qactive=0, Q_CFC_PWR.qactive=0, INF.qactive=0 (all modules simultaneously) | PNC PM HAS §8.14 |
| PkgC Aggregator (PUnit CBB) | CBB | Package C-state resolution: min of all module states; broadcasts PkgC idle to IMH via HPM | HPM PkgC_idle; D2D virtual wires to IMH | DMR CBB PM HAS |
| D2D / UCIe | CBB ↔ IMH | Inter-die coordination link for PkgC state; Pchannel interface removed on NWP (PkgC6 fused off) | Pchannel (removed NWP); Qchannel (retained for future use) | DMR SoC PM HAS |
| SCF / Fabric (full package) | CBB + IMH | Complete fabric idle required for PkgC6; IMH must also release all resources | Full-package CFC_CLK/PWR deasserted | DMR SoC PM HAS |

## FW Touchpoints

| Agent | Location | Role | Key Functions / Handlers | Source |
|-------|----------|------|--------------------------|--------|
| PCode (CBB) | CBB | Package C-state aggregation: monitors all module Q-channel states; sends HPM PkgC_idle; enforces PKG_C_STATE_LIMIT_REQ; CBB PKG C-state limit register (= 0 on NWP) | CBB PKG_C_STATE_LIMIT_REQ; HPM PkgC_idle broadcast; PkgC FSM | DMR CBB PM HAS |
| PrimeCode (IMH) | IMH | Receives HPM PkgC_idle from each CBB; coordinates IMH-side fabric power-gating for PkgC6 entry; manages D2D link gating | HPM PkgC_idle receive; D2D CFC_CLK/PWR gating; cross-CBB PkgC aggregation | PrimeCode firmware |
| uCode (PantherCove) | CBB core | Must set P (Package) bit in MWAIT hint for OS to allow any PkgC entry; all cores must agree | MWAIT EAX P-bit (bit[4] in C6 sub-state encoding); MWAIT hint propagation | PNC PM HAS §8.1 |
| BIOS / UEFI | Platform | Programs package C-state limit; reflects FUSE_PKG_C_STATE in ACPI _CST and MSR 0xE2 limit fields | MSR 0xE2 bit[10] PKG_C_STATE_LIMIT; ACPI _CST PkgC descriptor | BIOS PM HAS |

## OS Interfaces

| Interface | ID / Address | Access | Description | Spec Reference |
|-----------|-------------|--------|-------------|----------------|
| MWAIT P-bit | CPU instruction, EAX[4]=1 (in C6 sub-states) | W | All cores must set Package bit to allow PkgC entry; MWAIT C6S-P = EAX=0x25 | PNC PM HAS §8.1 |
| MSR PkgC6 Residency | 0x3F9 | RO | Crystal cycles in Package C6; reads 0 on NWP (PkgC6 fused off) | PNC PM HAS §8.1 |
| MSR CLOCK_CST_CONFIG_CONTROL | 0xE2 | RW | bits[10:9] PKG_C_STATE_LIMIT: caps max package C-state OS can request | PNC PM HAS §8.6.5 |
| CPUID.05H | Leaf 5, EDX | RO | Enumerates package C-states; PkgC6 absent on NWP (FUSE_PKG_C_STATE=0) | IA-32 SDM |
| ACPI _CST (package-level) | ACPI namespace | RO | Package C-state descriptor; PkgC6 object absent on NWP | ACPI Spec 6.x |

## KPI & Timing

| Parameter | Value | Units | Condition / Notes | Source |
|-----------|-------|-------|-------------------|--------|
| PkgC6 residency on NWP | 0 | crystal cycles | PkgC6 fused off; FUSE_PKG_C_STATE=0 on NIO PUNIT | NWP PM MAS §6.2 |
| Q-channel deassert requirement | All 3 × all modules | — | All three Q-channels must be deasserted by every module simultaneously for PkgC | PNC PM HAS §8.14 |
| MWAIT P-bit requirement | All cores | — | All cores must set P (Package) bit in MWAIT hint to allow any PkgC entry | PNC PM HAS §8.1 |
| CBB PKG_C_STATE_LIMIT_REQ | = 0 on NWP | — | CBB limit register also clamps PkgC to C0/C1 max | NWP PM MAS §6.2 |
| PkgC6 entry test (NWP) | Negative test | — | Verify PkgC6 entry is blocked even when OS requests C6S-P MWAIT hint | NWP PSS TC |

## NWP Delta

**PkgC6 is REMOVED on NWP** — confirmed in [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html).

### How Disabled
- NIO: `FUSE_PKG_C_STATE = 0` (fused off)
- CBB: `PKG_C_STATE_LIMIT_REQ_C_STATE_MAX_LIMIT = 0`
- No global aggregation for PkgC6 entry/exit
- Pchannel interface between NIO PUNIT and RC is **removed** (was unused on DMR anyway since MBVR actions were ZBB'd — HSD 22020334714)
- Pchannel/Qchannel interfaces from RCs to downstream Stacks/IPs **retained** for future NWP product lines that may re-enable PkgC6

### Rationale
- Customer workload profile doesn't benefit from deep package idle
- Simplifies NIO design and validation
- Pchannel distributors between NIO PUNIT and RCs eliminated

### Validation Impact
- **All PkgC6 test cases are N/A on NWP**
- All PkgC6 cross-products (PkgC6 × PROCHOT, PkgC6 × D2D, PkgC6 × MC6 flush, etc.) are removed
- MC6 becomes the deepest idle state
- Verify `FUSE_PKG_C_STATE=0` and `PKG_C_STATE_LIMIT_REQ_C_STATE_MAX_LIMIT=0` are correctly fused
- Verify that PkgC6 entry is not possible even if OS requests it

