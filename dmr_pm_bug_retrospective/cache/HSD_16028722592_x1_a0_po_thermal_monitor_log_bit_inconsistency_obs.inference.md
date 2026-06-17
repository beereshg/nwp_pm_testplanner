# HSD 16028722592: [X1 A0 PO] Thermal Monitor Log bit inconsistency observed with MSR 0x19c

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [16028722592](https://hsdes.intel.com/appstore/article-one/#/16028722592) |
| **Status** | rejected.wont_do |
| **Priority** | 3-medium |
| **Owner** | ashashi |
| **Component** | sw.os |
| **Defect Die** | compute |
| **Conclusion** | no_root_cause.rejected |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **UNKNOWN** | 20% |
| **Feature** | Power/RAPL | 80% |
| **Sub-Feature** | VR | — |

**Reasoning**: No strong indicators found

## Root Cause Summary

Issue:

Injecting temperature to core greater than T_Throttle does not set Thermal Monitor Log bit on MSR 0x19C (IA32_THERM_STATUS) for one of the the core in the module.

Steps followed:

1. T_THROTTLE is 100 on CBB

2.
 
Inject high temperature on one core of the module using the below command

sv.socket0.cbb0.compute1.pma10.pmsb.dfvfcr_dts_fuse_0.cr_reg36_inst.digthermovrdval
=0x14c (102)

3.
 
MSR 0x19c does not show thermal Monitor Log bit set for one of the core in the module although it h

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
[25ww46.3]

Anjana explained that the Linux kernel's deferred algorithm clears the lock bit independently on each core, resulting in one core's lock bit being set while the other's is cleared, which Srinivas later confirmed as expected behavior.

Srinivas clarified that Linux provides more accurate counter presentation than MSRs for thermal events, and recommended not using MSRs for verification, suggesting the issue be closed as not a real problem.

[25ww45.1]

Jinwen explained that Linux is clearing a hardware log bit, but there is confusion over whether this is expected behavior and whether the correct bits are being targeted, as the naming in the Linux code does not match the register definition.

Jaivardhan reviewed the hardware and software logic, noting that if the bit is set in another core, it should indicate a hot condition, and agreed that both bits should be read and cleared if necessary.

The team agreed to consult with Srinivas from the Linux PM team to clarify the expected behavior and whether application software should have access to the status, with Anjana noting that Srinivas is on leave but will return tomorrow.

[25ww44.1]

Via offline email thread, the team is investigating a discrepancy where the Thermal Monitor Log bit is not being set consistently across cores in a module when using MSR 0x19c, despite the Thermal Monitor Status bit being set; this issue appears with both temperature injection and real heat scenarios.

There are unresolved questions about the roles of pCode and uCode in setting and clearing these bits, and whether the issue is due to hardware, software, or architectural changes; further debugging, including halting uCode and collecting tracker logs, is ongoing, with no definitive resolution yet. 

[25ww43.3]

Discussion meeting was scheduled today; the team will decide the next step.

[25ww43.1]

Anjana is working with Yuval and Eyal. Both the core and the module should ideally be setting the thermal log bit at the same time 

### Description
Issue:

Injecting temperature to core greater than T_Throttle does not set Thermal Monitor Log bit on MSR 0x19C (IA32_THERM_STATUS) for one of the the core in the module.

Steps followed:

1. T_THROTTLE is 100 on CBB

2.
 
Inject high temperature on one core of the module using the below command

sv.socket0.cbb0.compute1.pma10.pmsb.dfvfcr_dts_fuse_0.cr_reg36_inst.digthermovrdval
=0x14c (102)

3.
 
MSR 0x19c does not show thermal Monitor Log bit set for one of the core in the module although it has Thermal Monitor Status bit being set

As per HAS:

 

https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/Thermal/Thermal%20Management/Thermal%20Management.html#ia32_therm_status

Thermal Monitor Log should be set whenever 0 to 1 transition of THERMAL_MONITOR_STATUS occurs

4. Even after clearing the temperature injection, do not see the Thermal Monitor Log bit being set on one core in the Module. The Thermal Monitor Status bit gets cleared after clearing but still do not see Thermal Monitor Log bit being set

FW Versions

BIOS Version : OKSDCRB1.86B.2754.D05.2509160231

Kernel Version : 6.14.0-dmr.bkc.6.14.7.4.PO3.11.x86_64

IA32_BIOS_SIGN_ID (Pcode Patch ID) : 0x6000096700000000

Memory Config : 
16x Hynix RE32 2Rx8 8000 (mixed PNs)

BMC Version: 

oks-2025.25.4-0-g91f494e96c

QDF: Q7YL/32 core

Socket CBB IMH Cores CPU's  PKG_TDP PKG_MAX_PWR PKG_MIN_PWR RAPL_PL1 RAPL_PL2 DRAM_TDP DRAM_MAX_PWR DRAM_PWR_LIMIT

    0   1   2    32   32      325W     390W         0W        325W     390W     180W     212W          0W

Node 0: CPUs [0-31]

Socket 0: Online CPUs: 32

BIOS Knobs:

### Comments (latest)
++++1667015717 jinwengo
<p>I did not see high core temperature from MSR 0x19C.</p><p>&nbsp;<span class="intel-user" style="font-weight: bold; color: rgb(0, 123, 255);">@Rowe, James</span>&nbsp;any idea why it does not report high temperature here?</p><!--EndFragment-->

++++1667015715 jamesrow
<p>i just checked myself, I can reproduce but its due to module mapping, i.e. checking module's therm status we didnt inject to.&nbsp;</p><p><br /></p><p>steps to confirm them status works:<br />1. read msr 0x54 to determine what module_id&nbsp;</p><p>rdmsr 0x54 -c 0</p><p>0x18</p><p>module_id=3</p><p><br /></p><p>2. check pma's logical id to belongs to OS module 0, i.e module 3</p><p>sv.socket0.cbb0.compute0.pma3.pmsb.slice_cfg.logical_id</p><p>0x3</p><p>#so pma3 belongs to first module on OS</p><p><br /></p><p>3. inject tj+2C into all sensors in the pma:</p><p>sv.socket0.cbb0.compute0.pma3.pmsb.dfvfcr_dts_fuse_0.cr_reg36_inst.digthermovrden=1</p><p>sv.socket0.cbb0.compute0.pma3.pmsb.dfvfcr_dts_fuse_0.cr_reg36_inst.digthermovrdval=0x14c #102C</p><p><br /></p><p>4. read all core therm status's, can see only OS module 0, module_id 3, has its therm status's flipped as expected:</p><p>root@sut:/&gt;rdmsr 0x19C -a</p><p>88460280</p><p>root@sut:/&gt;rdmsr 0x19C -a</p><p>880003c1</p><p>884f03c3</p><p>88420000</p><p>88430000</p><p>88610000</p><p>883b0000</p><p>88450000</p><div>...</div><div><br /></div><div>5. disable ovrd&nbsp; and check again:</div><div><div>root@sut:/&gt;rdmsr 0x19C -a</div><div>88460280 # monitor, threshold 1/2 status removed</div><div>884e0282</div><div>88420000</div><div>88430000</div><div>88630000</div><div>883b0000</div></div><div>...</div><div><br /></div><div>6. I am not seeing freq drop, assume that is due to pmsb nor reporting min_max temps:&nbsp;<a href="https://hsdes.intel.com/appstore/article-one/#/article/22021555086" target="_blank">https://hsdes.intel.com/appstore/article-one/#/article/22021555086</a>&nbsp;</div><div><div>root@sut:/&gt;rdmsr 0x198 -a</div><div>d00</div><div>d00</div><div>d00</div><div>d00</div><div>d00</div><div>d00</div><div>d00</div></div><div><br /></div><div><br /></div><div><br /></div>

++++1667015714 jinwengo
<p>The result is strange.</p><p>1. I did not see&nbsp; the bit THERMAL_MONITOR_LOG for <span style="color: rgba(0, 0, 0, 0.87); font-family: Roboto, &quot;Helvetica Neue&quot;, sans-serif; font-size: 12.18px;">OS module 0 was set although the bit&nbsp;</span><font face="Roboto, Helvetica Neue, sans-serif"><span style="font-size: 12.18px;"><font color="rgba(0, 0, 0, 0.87)">THERMAL_MONITOR_STATUS </font>was set.</span></font></p><p><font face="Roboto, Helvetica Neue, sans-serif"><span style="font-size: 12.18px;">2.&nbsp; Both bits of&nbsp;</span></font>THERMAL_MONITOR_LOG and&nbsp;<span style="font-family: Roboto, &quot;Helvetica Neue&quot;, sans-serif; font-size: 12.18px;">THERMAL_MONITOR_STATUS&nbsp; for&nbsp;</span><span style="color: rgba(0, 0, 0, 0.87); font-family: Roboto, &quot;Helvetica Neue&quo

### Conclusion
no_root_cause.rejected

### Component
sw.os

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

- **Primary Feature**: Power/RAPL
- **Sub-Feature**: VR
- **Component Path**: sw.os

## Firmware Touchpoints

### PCODE
- `Pcode Patch`

### BIOS
- `BIOS Knob`

## Key Registers

- `MSR 0x19c`
- `MSR 0x19C`
- `MSR 0x1b1`
- `MSR 0x1a2`
- `MSR 0x1A2`
- `sv.socket0.cbb0.compute1.pma10.pmsb.dfvfcr_dts_fuse_0.cr_reg36_inst.digthermovrdval`
- `sv.socket0.cbb0.compute0.pma3.pmsb.slice_cfg.logical_id`
- `sv.socket0.cbb0.compute0.pma3.pmsb.dfvfcr_dts_fuse_0.cr_reg36_inst.digthermovrden`
- `sv.socket0.cbb0.compute0.pma3.pmsb.dfvfcr_dts_fuse_0.cr_reg36_inst.digthermovrdval`
- `sv.socket0.cbb0.compute1.pma8.pmsb.slice_cfg.logical_id`

## Timeline

- **Submitted**: 2025-09-26 18:24:48
- **Closed**: 2025-11-14 02:38:55
- **Days Open**: 48

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
