# HSD 14026586861: [DMR][X1 A0][Cstate] Reading wrong value for resolved_cores_sub_state for cores in C1 state

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [14026586861](https://hsdes.intel.com/appstore/article-one/#/14026586861) |
| **Status** | rejected.not_a_defect |
| **Priority** | 3-medium |
| **Owner** | tensaeke |
| **Component** | fw.pcode |
| **Defect Die** | base |
| **Conclusion** | not_a_bug |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **UNKNOWN** | 20% |
| **Feature** | Core C-States | 80% |
| **Sub-Feature** | C1E | — |

**Reasoning**: No strong indicators found

## Root Cause Summary

Platform
: SC00901159H0008

IFW: 
OKSDCRB1.86B.2834.D10.2510170119

=============================================================

|Package                         |Version                   |

-------------------------------------------------------------

|pysvext.diamondrapids           |1.8.3.600                 |

|pysvext.diamondrapids_imh       |1.5.5.600                 |

|pysvext.diamondrapids_imh_a0    |1.3.2.600                 |

|pysvext.diamondrapids_cbb       |1.1.18.600          

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
[26ww05.4]

AR Tensea to provide information in HSD, Hector suggest we can close this sighting now as new information does not add anything new. AR sysdebug close it. 

[26ww04.3]

Information was collected for both cores and replied to mail, need architectural input. Will bump the thread and look for more attention to this sighitng. 

[26ww03.3]

Hector requested more experiments based on Elad, Tensea will extract the information for both of the cores in a module to understand why sub_state is 4, it is still not clear. Currently Tensea only extracted for 1 core of the module. Next steps need to be defined after the data collection is done. 

[26ww03.1]

Jesus relayed that the substate is considered a wish state rather than an actual state, and Hector M noted no functional impact but will verify if the behavior is expected. 
Hector M will review the relevant information and coordinate with the team to determine if further clarification or action is needed.

[26ww02.3]

Sighting provided by Elad has been rejected and merged with this sighting. There is already a mail conversation going on. Having sub_state value of 0x4 currently does not have any functionality impact, but it is still an unexpected value compared to the HAS value accordin to FV. Latest reply from CBB (Ofek) confirms that PMA reports to PCU the wish state, not the actual state, and this wish state does not have any functionality meaning. Based on this, need FV to evaluate if this register is needed or if the documentation needs to be updated.

[25ww51.3]

We need architectural CBB PMA team, looking for Ido/Yulia Okunev/Yuval Markuvish. Hector will start the conversation and add architectural team to help grabing attention from CBB team

[25ww50.3]

Hector M observed that the substate for C1 and C1E is consistently read as four, whereas documentation specifies expected values of zero or one, and this behavior has persisted since power-on, prompting questions about possible undocumented changes or PMA in

### Description
Platform
: SC00901159H0008

IFW: 
OKSDCRB1.86B.2834.D10.2510170119

=============================================================

|Package                         |Version                   |

-------------------------------------------------------------

|pysvext.diamondrapids           |1.8.3.600                 |

|pysvext.diamondrapids_imh       |1.5.5.600                 |

|pysvext.diamondrapids_imh_a0    |1.3.2.600                 |

|pysvext.diamondrapids_cbb       |1.1.18.600                |

|pysvext.diamondrapids_cbb_a0    |1.3.2.600                 |

|pysvext.panthercove             |1.3.0                     |

|pysvtools.server_wave_5         |0.6.9.600                 |

configuration:  

AcpiC2Enumeration=0, AcpiC3Enumeration=0 and MWait Enabled, 

ProcessorC1eEnable =
1

Reading 

resolved_cores_sub_state = 0x4

 when cores are in C1 state, which is not expected (expected to see value 0x0 for C1). The C1 residency counter (MSR 0x660) is incrementing, confirming cores are  in C1.

In [54]: sv.socket0.cbb0.base.punit_regs.punit_gpsb.gpsb_infvnn_crs.ccp_status['fid_48'].show()

0x00000000 : rsvd_3 (31:28) (rw/v) -- Reserved

0x00000000 : probe_mode_done (27:27) (rw/v) -- This bit is used by UCODE to inform the PCU that the Probe Mode sequence that it was running is done. in CNL CR and special moved to be RW_V from WO to match SK...

0x00000000 : rsvd_2 (26:20) (rw/v) -- Reserved

0x00000000 : lp_at_c0 (19:16) (rw/v) -- LP_AT_C0[i] = 1 while the related LP (BigCore - thread, Atom - core) is in TC0/CC0 respectively. Note: when TC1/CC1, LP_AT_C0[i] = 0. Used for Punit internal counters,...

0x00000004 : resolved_cores_sub_state (15:12)
 (rw/v) -- Updated by Core PMA as the resolved sub-state of all LPs of the related module. The Core PMA will reflect the wish sub-state of the Min(LPs) of the RES...

0x00000001 : resolved_cores_state (11:08) (rw/v) -- Updated by Core PMA as the resolved state of all LP of the related module. Possible values are: 4'h0 - 

### Comments (latest)
++++14614883925 senthil1
Assigned co-owner and component based on the information available in the pre-sighting record. Please update as appropriate

++++14614883926 tensaeke
<p>SVOS and IFIW info:</p><p>&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;dmr2544-bookworm-update011</p><p><span class="cf0">&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;OKSDCRB1.86B.0030.D17.2512030720 (WW49.5)</span></p><p><span class="cf0"><br /></span></p><p><span class="cf0"><br /></span></p><p><span style="color: rgb(16, 24, 40); font-family: Montserrat, sans-serif; font-size: 13px;">As an experiment, I tried limiting the cores to C1 by disabling C6 through the driver</span><span style="color: rgb(16, 24, 40); font-family: Montserrat, sans-serif; font-size: 13px;">&nbsp;rather than using the&nbsp;</span><code style="white-space-collapse: break-spaces; color: rgb(16, 24, 40); font-size: 13px;">dfx_ctrl_unprotected.core_cstate_limit</code><span style="color: rgb(16, 24, 40); font-family: Montserrat, sans-serif; font-size: 13px;">&nbsp;register. The goal was to see if this approach would affect the&nbsp;</span><code style="white-space-collapse: break-spaces; color: rgb(16, 24, 40); font-size: 13px;">resolved_cores_sub_state</code><span style="color: rgb(16, 24, 40); font-family: Montserrat, sans-serif; font-size: 13px;">&nbsp;value. However, even after applying the C1 limit via the driver, I am still seeing&nbsp;</span><code style="white-space-collapse: break-spaces; color: rgb(16, 24, 40); font-size: 13px;">resolved_cores_sub_state</code><span style="color: rgb(16, 24, 40); font-family: Montserrat, sans-serif; font-size: 13px;">&nbsp;as 4.</span></p><p><span class="cf0"><span style="color: rgb(16, 24, 40); font-family: Montserrat, sans-serif; font-size: 13px;"><br /></span></span></p><p><span class="cf0"><span style="color: rgb(16, 24, 40); font-family: Montserrat, sans-serif; font-size: 13px;"><br /></span></span></p><p><img src="https://hsdes.intel.com/rest/binary/14026579628" style="width: 921px;" data-processed="true" /><span class="cf0"><span style="color: rgb(16, 24, 40); font-family: Montserrat, sans-serif; font-size: 13px;"><br /></span></span></p><p><span class="cf0"><span style="color: rgb(16, 24, 40); font-family: Montserrat, sans-serif; font-size: 13px;"><br /></span></span></p><p><span class="cf0"><span style="color: rgb(16, 24, 40); font-family: Montserrat, sans-serif; font-size: 13px;"><br /></span></span></p><p><span class="cf0"><span style="color: rgb(16, 24, 40); font-family: Montserrat, sans-serif; font-size: 13px;">below is&nbsp;</span></span>ccp_status for some of the modules</p><p><br /></p><p><span class="cf0"></span></p><p><br /></p><p><span class="cf0">ccp_status</span><span class="cf0">[&quot;fid_24&quot;]</span></p><p><span class="cf0">    0x00000000 : rsvd_3 (31:28) (</span><span class="cf0">rw</span><span class="cf0">/v) -- Reserved</span></p><p><span class="cf0">    0x00000000 : </span><span class="cf0">probe_mode_done</span><span class="cf0"> (27:2

### Tags
FV_PM

### Conclusion
not_a_bug

### Component
fw.pcode

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
- **Sub-Feature**: C1E
- **Component Path**: fw.pcode

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `MSR 0x660`
- `sv.socket0.cbb0.base.punit_regs.punit_gpsb.gpsb_infvnn_crs.ccp_status`
- `sv.socket0.cbb0.compute0.pma0.gpsb.core_status`
- `sv.socket0.cbb0.compute0.pma0.pmsb.core_sub_state_dec`
- `sv.socket0.cbb0.compute0.pma0.pmsb.core_sub_state_dec.show`
- `sv.socket0.cbb0.compute0.pma0.pmsb.pma_static_chicken_bits_2.show`

## Timeline

- **Submitted**: 2025-12-10 10:17:25
- **Closed**: 2026-02-03 00:09:12
- **Days Open**: 54

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
