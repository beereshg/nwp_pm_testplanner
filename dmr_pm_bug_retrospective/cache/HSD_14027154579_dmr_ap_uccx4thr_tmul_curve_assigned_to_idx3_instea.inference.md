# HSD 14027154579: [DMR AP UCC][X4][THR] TMUL Curve assigned to IDX3 instead of IDX4

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [14027154579](https://hsdes.intel.com/appstore/article-one/#/14027154579) |
| **Status** | complete.validated |
| **Priority** | 2-high |
| **Owner** | lvargasv |
| **Component** | hw.big_core |
| **Defect Die** | compute |
| **Conclusion** | hw.arch |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **FW_PCODE** | 70% |
| **Feature** | PState Stack | 45% |
| **Sub-Feature** | general | — |

**Reasoning**: tag contains FIX_PATCH → FW_PCODE

## Root Cause Summary

while running TMUL content at EFI/Linux granted license is 3 and it ended up using voltage curve mapped to IDX3 fuses, which according to the fuse description it is not the right one. it should be using IDX4.

in the 
HAS 
there is a contradiction. for config registers it says tmul uops should be 3.

but below in the HAS it also said TMUL should be 4

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Description
while running TMUL content at EFI/Linux granted license is 3 and it ended up using voltage curve mapped to IDX3 fuses, which according to the fuse description it is not the right one. it should be using IDX4.

in the 
HAS 
there is a contradiction. for config registers it says tmul uops should be 3.

but below in the HAS it also said TMUL should be 4

### Comments (latest)
++++14615118221 lvargasv
2units recovering by modifying config register (al_cr_iccp_uop_mapping_cfg_2) to point to IDX4 for tmul uops. 2units ran with class TP ww04.  and according to Steven Chen. they started splitting AVX2/AVX3 license in class TP ww04. below image summarize the issue observed. ICCP level Tester vmin test/fusing System currently Iccp1 SSE SSE Iccp2 AVX2 AVX2/AVX3 Iccp3 AVX3 AMX Iccp4 AMX  

++++14615118428 vwang
Laura has been working on DMR TMUL PPV failures – about . As part of the characterization work she did, she noticed that parts were responding to voltage bumps on the IDX3 curve – which in theory is for AVX512 instructions. Later on, she discovered that iccp_uop_mapping register does points TMUL instructions to the IDX3 curve – explaining why voltage margining on IDX3 curve recovered TMUL failures:   al_cr_iccp_uop_mapping_cfg_2 0x00000000 : load_64 (02:00) (rw) -- group39 iccp req level 0x00000001 : load_128 (05:03) (rw) -- group40 iccp req level 0x00000002 : load_256 (08:06) (rw) -- group41 iccp req level 0x00000002 : load_512 (11:09) (rw) -- group42 iccp req level 0x00000000 : store_64 (14:12) (rw) -- group43 iccp req level 0x00000001 : store_128 (17:15) (rw) -- group44 iccp req level 0x00000002 : store_256 (20:18) (rw) -- group45 iccp req level 0x00000002 : store_512 (23:21) (rw) -- group46 iccp req level 0x00000000 : spare_cb1 (26:24) (rw) -- spare cbit for iccp 0x00000000 : spare_cb2 (29:27) (rw) -- spare cbit for iccp 0x00000000 : spare_cb3 (30:30) (rw) -- spare cbit for iccp 0x00000000 : iccp_dis_wait_4_tmul_inuse_off (31:31) (rw) -- if Tmul InUse is on ICCP level request should be for Tmul. This is to replace wait_4_Tmul_PG_off in case Tmul PF i... 0x00000000 : change_light_throttle (32:32) (rw) -- light throttle diff of 2. 0x00000003 : tmb (35:33) (rw) -- group47 iccp req level 0x00000003 : tmul_tdq_rest (38:36) (rw) -- group48 iccp req level 0x00000003 : tmul_int (41:39) (rw) -- group49 iccp req level 0x00000003 : tmul_f32 (44:42) (rw) -- group50 iccp req level 0x00000003 : tmul_fp8 (47:45) (rw) -- group51 iccp req level 0x00000003 : tmul_bf16 (50:48) (rw) -- group52 iccp req level 0x00000003 : tmul_fp16 (53:51) (rw) -- group53 iccp req level 0x00000000 : dot_product_256 (56:54) (rw) -- group54 iccp req level 0x00000000 : dot_product_512 (59:57) (rw) -- group55 iccp req level 0x00000000 : disable_rat_throttle (60:60) (rw) -- Turning on this bit will disable RAT throttling. 0x00000000 : iccp_dis_wait_4_tmul_pg_off (61:61) (rw) -- if Tmul Power Good is on ICCP level request should be for Tmul. 0x00000001 : tmul_no_grant_no_disp_off (62:62) (rw) -- block Tmul disp. if the iccp grant level isn't tmul. 0x00000000 : telem_final_or_uop_iccp_req_select (63:63) (rw) -- Selector for ICCP request telemetry source     On at least two recent failures, by making the iccp_uop_mapping register point at IDX4 curve for TMUL instructions- parts recovered. It is worth saying that on these parts Laura sees ~100mV delta between ID

### Tags
SysDebugDccbBypass,FIX_PATCH_DMR_AP1_A0_60000999,FIX_IFWI_DMR_AP1_2026.12.5.01,BKC#OKS_DMR_AP_X1_2026WW14,FIX_BKC_OKS_DMR_AP1_2026WW14, PSF=Y

### Conclusion
hw.arch

### Component
hw.big_core

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

- **Primary Feature**: PState Stack
- **Sub-Feature**: general
- **Component Path**: hw.big_core

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Timeline

- **Submitted**: 2026-02-24 07:04:50
- **Root Caused**: 2026-03-02 23:30:19
- **Closed**: 2026-04-14 00:12:48
- **Days Open**: 48

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
