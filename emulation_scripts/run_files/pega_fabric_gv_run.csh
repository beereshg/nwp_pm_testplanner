#!/usr/intel/bin/tcsh
# =============================================================================
# pega_fabric_gv_run.csh
#
# HSD: 16030715604 - [PSS] PEGA-driven FabricGV
#
# Launches HSLE IMH2 M7 (MCP ICI) emulation run to verify that PCode responds
# to PEGA mailbox pstate commands by changing fabric GV ratios across all dies.
#
# BIOS knobs required:
#   - ProcessorHWPMEnable = 1  (PEGA mailbox requires HWP init)
#   - Run setup_bios_knobs.csh first if IFWI has not been prepared
#
# Script path on NFS (copy pega_fabric_gv.py there before running):
#   /nfs/site/disks/ive_dmr_prednv_009/mps/pega_fabric_gv.py
#
# Usage:
#   tcsh pega_fabric_gv_run.csh
# =============================================================================

setenv PATH /p/hdk/cad/zapo_crt/latest/bin:${PATH}
setenv NB_WASH_ENABLED
setenv NB_WASH_GROUPS intelall,soc,soc73,shdk73,hdk7nm,adl_rtl,adl,gnr74,gnr76,cicg,c2dgusers,dmrips,dmrprj,cbbb_c2dg_ex,dmrmcp

crt -rid 40584 -bf mcp_ici_hsle_svos \
 -io IFWI=/nfs/site/disks/ive_dmr_prednv_009/nkudliba/training/bios_knob_new -- \
 --er \
 -nbqslot /prj/sv/dmr/sysval/standard \
 -c 4000000000 \
 -netbatch_opts \'--log-file-dir /tmp/netbatch\' \
 -mail \'S E\' \
 -pythonsv_enable \
 -pythonsv.base simics \
 -pythonsv.logging \
 -pythonsv.path /nfs/site/disks/ive_pysv_dmr_001/pythonsv_ap2_live \
 -pythonsv.script /nfs/site/disks/ive_dmr_prednv_009/mps/pega_fabric_gv.py \
 -p_tracker_en -primecode_tracker_en -acode_tracker_en -iosf_sb_tracker_en \
 -pythonsv.stub /nfs/site/disks/ive_pysv_dmr_001/pysv_configs/DMR/AP2/M7/MCP/SLE/pysv_config_ici.ini \
 -pythonsv.start_condition "'"'@wait_for_log(\"uefi_post.simics\",\"PPR_TEST_DONE\",\"emu.devices\")'"'" --
