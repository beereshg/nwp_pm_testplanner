#!/usr/intel/bin/tcsh
setenv PATH /p/hdk/cad/zapo_crt/latest/bin:${PATH}
setenv NB_WASH_ENABLED
setenv NB_WASH_GROUPS intelall,soc,soc73,shdk73,hdk7nm,adl_rtl,adl,gnr74,gnr76,cicg,c2dgusers,dmrips,dmrprj,cbbb_c2dg_ex,dmrmcp

# HGS (Hardware Guided Scheduling) emulation run
# Script: /nfs/site/disks/ive_dmr_prednv_009/mps/test_hgs.py
# Model:  HSLE IMH2 M7 (MCP ICI)
# BIOS:   HWP knob enabled (bios_knob_new)
# Trackers: pcode, primecode, acode, iosf-sb
# Queue: standard

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
 -pythonsv.script /nfs/site/disks/ive_dmr_prednv_009/mps/test_hgs.py \
 -p_tracker_en -primecode_tracker_en -acode_tracker_en -iosf_sb_tracker_en \
 -pythonsv.stub /nfs/site/disks/ive_pysv_dmr_001/pysv_configs/DMR/AP2/M7/MCP/SLE/pysv_config_ici.ini \
 -pythonsv.start_condition "'"'@wait_for_log(\"uefi_post.simics\",\"PPR_TEST_DONE\",\"emu.devices\")'"'" --
