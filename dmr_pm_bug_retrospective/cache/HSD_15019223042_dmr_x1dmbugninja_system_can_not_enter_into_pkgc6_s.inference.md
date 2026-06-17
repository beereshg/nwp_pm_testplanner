# HSD 15019223042: [DMR X1][DM][BugNinja] System can not enter into PkgC6 state with cap failover

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [15019223042](https://hsdes.intel.com/appstore/article-one/#/15019223042) |
| **Status** | root_caused.awaiting_fix |
| **Priority** | 2-high |
| **Owner** | lumingch |
| **Component** | fw.primecode |
| **Defect Die** | ioe |
| **Conclusion** | fw.arch |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **UNKNOWN** | 20% |
| **Feature** | Core C-States | 80% |
| **Sub-Feature** | MC6 | — |

**Reasoning**: No strong indicators found

## Root Cause Summary

Description
: System can't enter into PkgC6 state after CAP failover. But it works without CAP failover

Recipe:

1: Set biosknob: 

MirrorMode=0x1，DfxEnableCapInj=1, PackageCState = 2,  MonitorMWait = 0x1

2: Power cycle the system

3: Apply below WA before entering into OS to enable PC6 
Known PC6 issue - 14026822627
:

sv.sockets.imhs.d2d_stack.d2d_stacks.uxis.ula_link_ctrl.l1_enable=0

4: Check C6SP is enabled and keep system in idle state, check PC6 residency:

cpupower idle-info

ptat -mon

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Description
Description
: System can't enter into PkgC6 state after CAP failover. But it works without CAP failover

Recipe:

1: Set biosknob: 

MirrorMode=0x1，DfxEnableCapInj=1, PackageCState = 2,  MonitorMWait = 0x1

2: Power cycle the system

3: Apply below WA before entering into OS to enable PC6 
Known PC6 issue - 14026822627
:

sv.sockets.imhs.d2d_stack.d2d_stacks.uxis.ula_link_ctrl.l1_enable=0

4: Check C6SP is enabled and keep system in idle state, check PC6 residency:

cpupower idle-info

ptat -mon -filter 0x8

CORE_
C6_
RESIDENCY: MSR 0x3FD

MC6_
RESIDENCY: MSR 0x664

PKG_

C6_

RESIDENCY: MSR 0x3F9

4: inject cap failover

import mc.dmr_mirror_harasser as mm

mm.failover(socket=0, imh = 0, mc = 0, subch = 0, method = &quot;ca&quot;)

5: Check PC6 residency

ptat -mon -filter 0x8

CORE_
C6_
RESIDENCY: MSR 0x3FD

MC6_
RESIDENCY: MSR 0x664

PKG_

C6_

RESIDENCY: MSR 0x3F9

Failure signature:

Before cap failover:

Index Device Cor Thr     C0     C1     C6    PC2    PC6

     0   CPU0   -   -   0.20   0.14  99.66   
2.42   9.05

     1   CPU0   -   -   0.04   0.05  99.91   
4.16  16.27

     2   CPU0   -   -   0.07   0.06  99.86   
3.38  13.11

     3   CPU0   -   -   0.05   0.05  99.90   
3.89  15.04

     4   CPU0   -   -   0.07   0.05  99.88   
3.96  16.21

     5   CPU0   -   -   0.05   0.05  99.90   
3.93  15.79

     6   CPU0   -   -   0.08   0.06  99.86   
3.51  13.61

     7   CPU0   -   -   0.09   0.05  99.86   
3.95  14.55

     8   CPU0   -   -   0.04   0.05  99.91   
4.22  15.86

     9   CPU0   -   -   0.04   0.06  99.90   
4.30  17.00

    10   CPU0   -   -   0.12   0.07  99.81   
3.73  14.52

    11   CPU0   -   -   0.06   0.05  99.90   
4.15  16.19

After cap failover:

 Index Device Cor Thr     C0     C1     C6    PC2    PC6

     0   CPU0   -   -   0.19   0.10  99.70   2.24   
0.00

     1   CPU0   -   -   0.04   0.04  99.92   4.86   
0.00

     2   CPU0   -   -   0.06   0.03  99.91   3.80   
0.00

     3   CPU0   -   -   0.05   0.05  99.90   3.75   
0.

### Comments (latest)
++++22611825383 mbfausto
[CloneScript] Sighting [sighting_central.sighting.id=15019223042] of [component=fw.primecode] in [release=package.dmrap-ucc-x1-a0] has been cloned to a [feature] to [server.bugeco.id=22022251128] of [component=soc.PrimeCode 2.0#] in [release=dmrhub-a0]

++++22611914370 jmattapa
RAS has says that when memory failover happens, MC should result in a timeout error without Primecode workaround. But the sighting description says we just don't see PC6 residency and no timeout errors. Observed behavior doesn't seem to match HAS description.  Source:https://docs.intel.com/documents/arch_datacenter/DMR/RAS/DMR%20RAS%20HAS.html#ras_start-and-ras_exit-for-memory-sparing

++++22611914464 agraback
Note that the Arch Open HSD to clarify the direction has been rejected after discussion with PM and RAS Archs.  Primecode change will therefore be rejected as well 14027761756 [DMR][IMH2][ARCH] Define Interaction between PkgC flow and Memory Mirror Failover Mattapalli, Jaivardhan Last updated on: Thursday, May 14, 20269:55:58 AM(4 days ago) id:  22611900499   Notes from discussion with RAS team: Participants: Joe Brooks (PM val), Trevor Key (Primecode), RAS team: Camille Raad, Chen, Hsing-min, Rahul Shah.   1. Memory mirror failover is generally not used by our customers.  2. More over, it is very rare to hit errors and enter this memory mirror failover state. 3. There are no functional failures. System just doesn't enter PC6 in this rare event. 4. GNR did not support this cross-product too.   Given the rarity of the event and the set precedent on GNR, we do not want to add complexity and additional cross-products to PkgC flow. There's lot of effort involved in Primecode, Validation to support this.

### Tags
SysDebugCloned,SysDebugDccbBypass

### Conclusion
fw.arch

### Component
fw.primecode

## Root Cause Description

<!-- Populated by LLM enrichment stage (Stage 3b). -->

## Fix Description

<!-- Populated by LLM enrichment stage (Stage 3b). -->

## Source Code References

<!-- Populated by LLM enrichment stage (Stage 3b). -->

## Component Interaction: Root Cause

<!-- Populated by LLM enrichment stage (Stage 3b). -->

## Component Interaction: Fix

<!-- Populated by LLM enrichment stage (Stage 3b). -->

## Feature Mapping

- **Primary Feature**: Core C-States
- **Sub-Feature**: MC6
- **Component Path**: fw.primecode

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `MSR 0x3FD`
- `MSR 0x664`
- `MSR 0x3F9`

## Timeline

- **Submitted**: 2026-03-31 06:35:19
- **Root Caused**: 2026-03-31 19:24:40
- **Days Open**: 51

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
