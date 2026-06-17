# HSD 15019145023: [DMR-AP][SPD_RECOVERY][[RAS] During SPD Recovery, Primecode Does Not Trigger SMI in IMH1

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [15019145023](https://hsdes.intel.com/appstore/article-one/#/15019145023) |
| **Status** | rejected.not_a_defect |
| **Priority** | 2-high |
| **Owner** | kjgalanc |
| **Component** | fw.primecode |
| **Defect Die** | ioe |
| **Conclusion** | not_a_bug |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **HW** | 40% |
| **Feature** | SST | 45% |
| **Sub-Feature** | general | — |

**Reasoning**: keyword 'eco' in title/desc → HW

## Root Cause Summary

Description:

Issue is not 100% reproducible.

After clock extension state test 12h , the spd recovery fail, however that the error is handling in present_state_debug register, the error is not handling by OS.

Remote_injector fisher:

[14:20:02.689] I: spd: biosstickylockbypassscratchpad_mem[8]:

 s
ocket0.imh0.ubox.ncevents.biosstickylockbypassscratchpad_mem[8] - 0x00000001

socket0.imh1.ubox.ncevents.biosstickylockbypassscratchpad_mem[8] - 0x00000000

[14:20:12.691] W: spd: ibi_error_status: 

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Description
Description:

Issue is not 100% reproducible.

After clock extension state test 12h , the spd recovery fail, however that the error is handling in present_state_debug register, the error is not handling by OS.

Remote_injector fisher:

[14:20:02.689] I: spd: biosstickylockbypassscratchpad_mem[8]:

 s
ocket0.imh0.ubox.ncevents.biosstickylockbypassscratchpad_mem[8] - 0x00000001

socket0.imh1.ubox.ncevents.biosstickylockbypassscratchpad_mem[8] - 0x00000000

[14:20:12.691] W: spd: ibi_error_status: 0x0

[14:20:12.699] W: 
spd: cm_tfr_st_status: 0x12

[14:20:12.699] W: spd: sda_line_signal_level: 0x1

[14:20:12.699] W: spd: scl_line_signal_level: 0x0

[14:20:12.709] W: spd: periodic_poll_command_enable: 0x505

[14:20:12.709] E: remote_injector: Traceback (most recent call last):

  File &quot;C:\Python311\Lib\site-packages\pysvext\fish_platform_oakstream\spd.py&quot;, line 114, in _spd_common_verify

    common_tools.wait_condition(cond=recovery_successful, timeout_seconds=10)

  File &quot;C:\Python311\Lib\site-packages\pysvext\fish_platform_oakstream\util\common_tools.py&quot;, line 57, in wait_condition

    raise AssertionError('timeout: wait condition expired!')

AssertionError: timeout: wait condition expired!

The above exception was the direct cause of the following exception:

Traceback (most recent call last):

  File &quot;C:\Python311\Lib\site-packages\pysvtools\fish_automation\remote_injector.py&quot;, line 476, in _remote_server_execute_optional

    func()

  File &quot;C:\Python311\Lib\site-packages\pysvext\fish_platform_oakstream\spd.py&quot;, line 164, in spd_error_12h_injection_verify

    _spd_common_verify()

  File &quot;C:\Python311\Lib\site-packages\pysvext\fish_platform_oakstream\spd.py&quot;, line 122, in _spd_common_verify

    raise AssertionError(&quot;SPD error not recovered&quot;) from e

AssertionError: SPD error not recovered

In [13]: sv.socket0.imhs.ubox.ncevents.biosstickylockbypassscratchpad_mem[8].show()

0x00000001 : data (31:00) (r

### Comments (latest)
++++14615184501 kjgalanc
Change to the BIOS version 32.D57 and microcode 0x60000991 the issue is no longer observed.  PeriodicTimer SMI is checking I3C bus reset done... [REMAP] GetRasipRemapLogicErrorBitMap: Error on Skt:0x0 Imh:0x0, RemapSts = 0x4000000000000 CallFromSmm = 1 PeriodicTimer SMI is checking I3C bus reset done... I3C BUS Reset Done Event on Socket: 0x0, Imh: 0x1 Instance: 0x1 TSOD Polling was disabled before recovery keep it disabled on Socket:0x0, Imh:0x1, Inst:0x1 Release Semaphore ERROR: C00000002:V03071008 I0 1DAE3520-E041-423D-9662-2B8F53D68390 BFFAEC10 WHEA: Detected Ras Non-Standard Error stopping PeriodicTimer Release Semaphore with socket id 0 [REMAP] GetRasipRemapLogicErrorBitMap: Error on Skt:0x0 Imh:0x0, RemapSts = 0x4000000000000 CallFromSmm = 1 [REMAP] GetRasipRemapLogicErrorBitMap: Error on Skt:0x0 Imh:0x0, RemapSts = 0x2 CallFromSmm = 1 Pcode kick off I3C Bus recovery on Socket:0x0, Imh:0x1, Instance:0x0 Aquire Semaphore success on Socket: 0x0 We can close this HSD.

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

- **Primary Feature**: SST
- **Sub-Feature**: general
- **Component Path**: fw.primecode

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `sv.socket0.imhs.ubox.ncevents.biosstickylockbypassscratchpad_mem`
- `sv.socket0.imh1.i3c.i3c3.sb_i3c_0.present_state_debug.show`

## Timeline

- **Submitted**: 2026-03-10 09:50:21
- **Closed**: 2026-03-11 01:16:12

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
