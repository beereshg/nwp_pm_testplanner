#!/usr/intel/bin/tcsh
setenv PATH /p/hdk/cad/zapo_crt/latest/bin:${PATH}
setenv NB_WASH_ENABLED
setenv NB_WASH_GROUPS intelall,soc,soc73,shdk73,hdk7nm,adl_rtl,adl,gnr74,gnr76,cicg,c2dgusers,dmrips,dmrprj,cbbb_c2dg_ex,dmrmcp

#crt -rid 40584 -bf mcp_ici_hsle_svos --er -nbqslot /prj/sv/dmr/sysval/standard -c 4000000000 -netbatch_opts \'--log-file-dir /tmp/netbatch\' -mail \'S E\' -simics_post_setup_script /nfs/site/disks/ive_oks_dppci_002/dmr/A0/hsle/mcp_ici/releases/26ww11.4_imh2_mcp_ici/simics_post_script/PPR_auto_exit_svos_sc.simics -pythonsv_enable -pythonsv.base simics -pythonsv.logging -pythonsv.path /nfs/site/disks/ive_pysv_dmr_001/pythonsv_ap2_live -pythonsv.script  /nfs/site/disks/ive_oks_dppci_002/dmr/collaterals/pythonsv_doa_test/pysvdoa_ww45/pythonSV_DOA.py -pythonsv.stub /nfs/site/disks/ive_pysv_dmr_001/pysv_configs/DMR/AP2/M7/MCP/SLE/pysv_config_ici.ini -pythonsv.start_condition "'"'@wait_for_log(\"uefi_post.simics\",\"PPR_TEST_DONE\",\"emu.devices\")'"'" --

#added bios knob for HWP
#added acode,pcode,primecode and iosf-sb tracker 
#running job with priority
crt -rid 40584 -bf mcp_ici_hsle_svos \
 -io IFWI=/nfs/site/disks/ive_dmr_prednv_009/nkudliba/training/bios_knob_new -- \
 --er \
 -nbqslot /prj/sv/dmr/sysval/priority \
 -c 4000000000 \
 -netbatch_opts \'--log-file-dir /tmp/netbatch\' \
 -mail \'S E\' \
 -pythonsv_enable \
 -pythonsv.base simics \
 -pythonsv.logging \
 -pythonsv.path /nfs/site/disks/ive_pysv_dmr_001/pythonsv_ap2_live \
 -pythonsv.script /nfs/site/disks/ive_dmr_prednv_009/nkudliba/training/hwp_test/hwp_tpmi_hold.py \
 -p_tracker_en -primecode_tracker_en -acode_tracker_en -iosf_sb_tracker_en \
 -pythonsv.stub /nfs/site/disks/ive_pysv_dmr_001/pysv_configs/DMR/AP2/M7/MCP/SLE/pysv_config_ici.ini \
 -pythonsv.start_condition "'"'@wait_for_log(\"uefi_post.simics\",\"PPR_TEST_DONE\",\"emu.devices\")'"'" --
