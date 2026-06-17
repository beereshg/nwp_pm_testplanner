# HSD 14026043025: [DMR][X1 A0 PO] set_lock_load_line() doesn't work

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [14026043025](https://hsdes.intel.com/appstore/article-one/#/14026043025) |
| **Status** | rejected.not_a_defect |
| **Priority** | 3-medium |
| **Owner** | jcmontan |
| **Component** | fw.primecode |
| **Defect Die** | ioe |
| **Conclusion** | not_a_bug |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **HW** | 40% |
| **Feature** | Unknown | 20% |
| **Sub-Feature** | general | — |

**Reasoning**: keyword 'eco' in title/desc → HW

## Root Cause Summary

BIOS: \\amr.corp.intel.com\ec\proj\debug\DMR\User\_Groups\memory\FV\BIOS \ OKSDCRB1.86B.2025.35.3.01_2688.D02_6020095E_1P0_NonIPClean_Trace_DebugSigned_update_primecode_pcode_fvmem.bin.7z 

ms.set_lock_load_line() doesn't move the epb to the desired value. Manually setting the register in MC works. 

code possibly not updated for DMR. 

CPLs updated already updated

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
[25ww45.1]

Alex explained ongoing efforts with PM FV and Johana to find a way to adjust load lines on memory controllers using PythonSV, with progress being made.

Shreyas provided settings from Primecode, but these do not fully disable EPB, as CBB pCode can override them. The team is seeking a solution via CBB pCode or TPMI.

Emiliano previously shared BIOS knobs and MSRs, but Johana needs a different approach; Emiliano is searching for a relevant register to resolve the request.

[25ww44.3]

Emiliano is working with Alex on this one. Alex provided some suggestions for Johanna to try also.

It seems it's just an issue of just finding the right way to to set the proper settings in Johanna's validation environment. we don't think it is bugs now.

[25ww44.1]

Shreyas checked the data Johana collected and mentioned the PythonSV configuration might not be correct, will double check it with her offline.

[25ww43.3]

Timothy explained that Energy Performance Bias (EPB) acts as a global orchestrator, influencing whether system components, including the memory controller, prioritize performance or energy efficiency. When set to performance bias, the memory controller avoids power-saving states, while energy efficiency bias encourages entry into such states. But we are uncertainty around set_lock_load_line with EPB

ARn: Shreyas will check both Primecode and pCode to determine if any relevant behavior is implemented

ww42.2
Next Steps:
1)Max to talk with Vidar and move to PM sysdebug.

ww41.4
Force LPM levels is not working on DMR.
Next Steps:
1) Move to PM sysdebug.

### Description
BIOS: \\amr.corp.intel.com\ec\proj\debug\DMR\User\_Groups\memory\FV\BIOS \ OKSDCRB1.86B.2025.35.3.01_2688.D02_6020095E_1P0_NonIPClean_Trace_DebugSigned_update_primecode_pcode_fvmem.bin.7z 

ms.set_lock_load_line() doesn't move the epb to the desired value. Manually setting the register in MC works. 

code possibly not updated for DMR. 

CPLs updated already updated

### Comments (latest)
++++14614699477 wrjones
Automated Message: This record has been cloned. The preceding comments are originally from the parent record 14025835882.

++++14614699531 jcmontan
the set_lock_load_lines function, we found some registers on the punit IMH   imh.punit.ptpcfsms.ptpcfsms.power_ctl1.pwr_perf_tuning_enable_dyn_switching": 0 imh.punit.ptpcfsms.ptpcfsms.power_ctl1.pwr_perf_tuning_disable_sapm_ctrl": 0 imh.punit.ptpcioregs.ptpcioregs.energy_perf_bias_config.alt_energy_perf_bias": ll * 4 imh.punit.ptpcfsms.ptpcfsms.power_ctl1.pwr_perf_tuning_cfg_mode =1   however they seem to not make anything.   talking to alex grabacki he mentioned that cbb pcode may support that same tpmi register, just have to target that die instead of imh.    I found the following registers in the cbb0 pcode   In [460]: sv.socket0.cbb0.showsearch("epb") pcode.vars.hwp_resolve.prev_epb = 0x0 pcode.vars.sapm.die_epb = 0x1 pcode.vars.sapm.socket_epb = 0x1 pcode.vars.sapm.disable_dynamic_epb = False pcode.vars.palpha.num_epb_steps = 0x4 pcode.vars.palpha.forced_epb_dfx = 0x0 pcode.vars.palpha.forced_epb_dfx_enabled = False pcode.vars.sapmproxymailbox.bios_mbx_epb_peci_override_enable = False it looks like I need to use this register first to be able to write to the registers first: sv.socket0.cbb0.pcode.vars.sapm.disable_dynamic_epb =1 after I did this, I saw KDB happening, but I did not get this reflected on MC registers Basically we need help from design, understanding how to used primecode or cbb pcode to be able to set the load lines. 

++++14614721504 mrtruehe
Moving to PM sysdebug for further debug.

++++14614738386 shreyasu
So EPB communication is slightly different with HPM. Each CBB pcode will determine their own EPB and communicate that with the Root IMH primecode.  The local EPBs get sent through HPM to root. The root IMH will resolve the final socket-level EPB and send it to the MCs. So could you check the following items after you make your injections: In IMH0 pcudata, look for:  Primecode::PstateCommon::resolved_socket_epb  Primecode::PstateCommon::socket_epb_buffer[i] // this will be the array from each of the dies The above will tell us what the EPB is for all the dies and what the socket level resolved EPB is.  Once we see the right EPBs in the above, we can check the MC register: pdm_ctrl0_data.epb_powermodesel

++++14614747183 jcmontan
on DMR, I see the following.  I will follow up with Shreyas to help me understand this values and how they map to MC? In [59]: sv.socket0.imh0.pcudata.socket_epb_buffer_0.show() 0x00000000 : socket_epb_buffer_0 -- /tmp/nb-tmp-sc_tiers3_vp.9454312400/Nightly/Release/main/553/dmr_imh1_a0/target/dmr_imh1_a0/pcode/gen/runtime/pstates_common.hpp In [60]: sv.socket0.imh0.pcudata.socket_epb_buffer_1.show() 0x00000000 : socket_epb_buffer_1 -- /tmp/nb-tmp-sc_tiers3_vp.9454312400/Nightly/Release/main/553/dmr_imh1_a0/target/dmr_imh1_a0/pcode/gen/runtime/pstates_common.hpp In [58]: sv.socket0.imh0.pcudata.socket_epb_buffer_2.show() 0x800128

### Conclusion
not_a_bug

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

- **Primary Feature**: Unknown
- **Sub-Feature**: general
- **Component Path**: fw.primecode

## Firmware Touchpoints

### BIOS
- `BIOS knob`

## Key Registers

- `sv.socket0.cbb0.pcode.vars.sapm.disable_dynamic_epb`
- `sv.socket0.imh0.pcudata.socket_epb_buffer_0.show`
- `sv.socket0.imh0.pcudata.socket_epb_buffer_1.show`
- `sv.socket0.imh0.pcudata.socket_epb_buffer_2.show`
- `sv.socket0.imh0.pcudata.socket_epb_buffer_3.show`

## Timeline

- **Submitted**: 2025-10-10 00:42:33
- **Closed**: 2025-11-13 05:05:42
- **Days Open**: 34

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
